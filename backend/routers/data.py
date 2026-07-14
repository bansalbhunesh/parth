from __future__ import annotations

import json
import logging
import time

from fastapi import APIRouter, HTTPException

from backend.agents.rfi_copilot import ask, ask_fallback, ask_stream
from backend.api_context import (
    _PROTECT_ANALYSIS,
    CopilotQuery,
    _count_requirements,
    _get_valid_systems,
    _load_json,
    _sse_response,
)
from backend.orchestrator import run_pipeline
from backend.paths import CORPUS

router = APIRouter()
log = logging.getLogger("pramaan.api")

@router.get("/project")
def project():
    gt = _load_json("ground_truth.json")
    return gt.get("project", {})


@router.get("/systems")
def systems():
    specs_dir = CORPUS / "specs"
    if not specs_dir.exists():
        return {"systems": []}
    return {"systems": sorted(p.stem for p in specs_dir.glob("*.md"))}


def _corpus_texts(system_id: str) -> tuple[str | None, str | None]:
    """Load the corpus spec + submittal markdown for a system, or (None, None)
    if either is missing. Used to run the INDEPENDENT rule-based detector when
    the LLM pipeline returns empty — never the seeded answer key."""
    spec_p = CORPUS / "specs" / f"{system_id}.md"
    sub_p = CORPUS / "submittals" / f"{system_id}.md"
    if spec_p.exists() and sub_p.exists():
        return spec_p.read_text(encoding="utf-8"), sub_p.read_text(encoding="utf-8")
    return None, None


@router.post("/ingest/{system_id}")
def ingest(system_id: str, seeded_demo: bool = False):
    if system_id not in _get_valid_systems():
        raise HTTPException(404, f"Unknown system '{system_id}'. Valid: {sorted(_get_valid_systems())}")
    t0 = time.time()

    # Explicit, opt-in demo fixture. This is the ONLY path that surfaces the
    # ground-truth (answer-key) labels, and it never poses as inference: the
    # caller must ask for it with ?seeded_demo=true and the payload is stamped
    # analysis_mode="seeded_demo" with a disclaimer. The normal analysis path
    # below never substitutes labels.
    if seeded_demo:
        seeded = _load_json("ground_truth.json").get("seeded_deviations", [])
        fixture = [d for d in seeded if d.get("system") == system_id]
        return {
            "system": system_id,
            "deviations": fixture,
            "count": len(fixture),
            "analysis_mode": "seeded_demo",
            "disclaimer": "SEEDED DEMO FIXTURE — pre-authored ground-truth labels, "
                          "not live inference. Omit ?seeded_demo=true for real analysis.",
            "elapsed_ms": 0,
        }

    log.info("Ingesting system %s", system_id)
    devs = run_pipeline(system_id)
    mode = "pipeline"
    # An empty result means the LLM/graph layer produced nothing (throttled, no
    # key, or genuinely clean). NEVER substitute the answer key: degrade to the
    # independent rule-based detector over the same spec/submittal — exactly the
    # /analyze contract. If the corpus text is missing, report unavailable.
    if not devs:
        spec_text, sub_text = _corpus_texts(system_id)
        if spec_text is not None and sub_text is not None:
            from backend.analyze import _resilient_fallback
            devs = _resilient_fallback(spec_text, sub_text, system_id)
            mode = "rule"
        else:
            mode = "unavailable"
    elapsed = round((time.time() - t0) * 1000)
    log.info("System %s: %d deviations in %dms (mode=%s)", system_id, len(devs), elapsed, mode)
    return {
        "system": system_id,
        "deviations": devs,
        "count": len(devs),
        "analysis_mode": mode,
        "elapsed_ms": elapsed,
    }


def _build_register(devs: list[dict]) -> dict:
    critical = sum(1 for d in devs if d.get("severity") == "Critical")
    major = sum(1 for d in devs if d.get("severity") == "Major")
    lead_times = [d["lead_time_weeks"] for d in devs if d.get("lead_time_weeks") is not None]
    return {
        "count": len(devs),
        "critical": critical,
        "major": major,
        "mean_lead_time_weeks": round(sum(lead_times) / len(lead_times), 1) if lead_times else 0,
        "max_lead_time_weeks": max(lead_times) if lead_times else 0,
        "register": devs,
    }


def _deterministic_register() -> dict:
    """Build the project overview without invoking the LLM pipeline.

    The overview is a read model, not an analysis command. Keeping it
    deterministic avoids launching one model call per corpus system during a
    server-rendered page refresh, especially after the frontend has timed out.
    Fresh inference remains available through /ingest and /analyze.
    """
    specs_dir = CORPUS / "specs"
    if not specs_dir.exists():
        return {
            **_build_register([]),
            "analysis_mode": "unavailable",
            "provenance": {
                "kind": "unavailable",
                "label": "Project snapshot unavailable",
                "description": "The project corpus is not present on this deployment.",
                "live": False,
                "source_documents": 0,
            },
        }

    from backend.analyze import _resilient_fallback

    out: list[dict] = []
    source_documents = 0
    for path in sorted(specs_dir.glob("*.md")):
        spec_text, sub_text = _corpus_texts(path.stem)
        if spec_text is None or sub_text is None:
            continue
        source_documents += 2
        out.extend(_resilient_fallback(spec_text, sub_text, path.stem))

    mode = "rule" if out else "unavailable"
    return {
        **_build_register(out),
        "analysis_mode": mode,
        "provenance": {
            "kind": "deterministic" if out else "unavailable",
            "label": (
                "Deterministic project snapshot"
                if out else "No deterministic findings available"
            ),
            "description": (
                "Recomputed from the bundled Meghdoot specification and submittal "
                "pairs without an LLM call. Run Live analysis for fresh inference."
                if out else
                "The available project documents produced no deterministic findings."
            ),
            "live": False,
            "source_documents": source_documents,
        },
    }


@router.get("/deviations")
def deviations(seeded_demo: bool = False):
    # Opt-in, clearly-labelled demo fixture (answer key) — never returned by the
    # default analysis path below.
    if seeded_demo:
        seeded = _load_json("ground_truth.json").get("seeded_deviations", [])
        return {
            **_build_register(seeded),
            "analysis_mode": "seeded_demo",
            "disclaimer": "SEEDED DEMO FIXTURE — pre-authored ground-truth labels, "
                          "not live inference. Omit ?seeded_demo=true for real analysis.",
        }
    return _deterministic_register()


# ── Copilot endpoints ───────────────────────────────────────────────

@router.post("/copilot", dependencies=_PROTECT_ANALYSIS)
def copilot(q: CopilotQuery):
    try:
        return ask(q.query)
    except Exception as exc:
        log.warning("Copilot LLM failed, using fallback: %s", exc)
        devs = _load_json("ground_truth.json").get("seeded_deviations", [])
        return ask_fallback(q.query, devs)


@router.post("/copilot/stream", dependencies=_PROTECT_ANALYSIS)
def copilot_stream(q: CopilotQuery):
    def generate():
        try:
            for event_type, data in ask_stream(q.query):
                # token data is raw model text (may contain newlines) — JSON-encode
                # it so the line-based SSE parser doesn't truncate at the first \n.
                # meta is already a JSON string; leave it as-is.
                if event_type == "token":
                    data = json.dumps(data)
                yield f"event: {event_type}\ndata: {data}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            log.warning("Copilot stream failed, sending fallback: %s", exc)
            devs = _load_json("ground_truth.json").get("seeded_deviations", [])
            fb = ask_fallback(q.query, devs)
            meta = {"sources": fb["sources"], "prior_rfis": fb["prior_rfis"],
                    "mode": fb.get("mode", "offline-fallback")}
            yield f"event: meta\ndata: {json.dumps(meta)}\n\n"
            yield f"event: token\ndata: {json.dumps(fb['answer'])}\n\n"
            yield "event: done\ndata: {}\n\n"

    return _sse_response(generate())


# ── Reference data endpoints ────────────────────────────────────────

@router.get("/cx-plan")
def cx_plan():
    return _load_json("commissioning/cx_plan.json")


@router.get("/cx-graph")
def cx_graph_endpoint():
    """The standards-grounded commissioning knowledge graph: stats + node/edge
    form (deviation-class -> Cx-test -> Cx-level) with per-edge citations."""
    from backend.agents import cx_graph
    return {"stats": cx_graph.graph_stats(), "graph": cx_graph.as_graph()}


@router.get("/rfi-log")
def rfi_log():
    return _load_json("rfi/rfi_log.json")


@router.get("/metrics")
def metrics():
    try:
        return _compute_metrics()
    except Exception as exc:
        log.warning("metrics unavailable: %s", exc)
        return {
            "detection": {}, "text_eval": {}, "commissioning": {}, "corpus": {},
            "citation_faithfulness": None,
            "error": "metrics temporarily unavailable",
        }


def _benchmark_headline() -> dict:
    """The frozen ps4_external_v1 (v1.2) result — the real accuracy signal.
    Surfaced on /metrics so a caller hitting the raw endpoint sees the headline
    benchmark numbers, not just the structured-baseline 1.000s below (which are
    1.000 by construction — see each block's `basis` field — not a capability
    score). Numbers come from the frozen benchmark card, never hardcoded here."""
    card = (CORPUS.parent.parent / "benchmarks" / "ps4_external_v1"
            / "reports" / "benchmark_card.json")
    try:
        data = json.loads(card.read_text(encoding="utf-8"))
        pr = data.get("primary_result", {})
        comp = data.get("composition", {})
        return {
            "benchmark": data.get("benchmark", "ps4_external_v1"),
            "version": data.get("benchmark_version"),
            "featured_model": data.get("featured_model"),
            "recall_mean": pr.get("recall_mean"),
            "precision_mean": pr.get("precision_mean"),
            "f1_mean": pr.get("f1_mean"),
            "clean_negative_false_alert_rate": pr.get("clean_negative_false_alert_rate_mean"),
            "pairs": comp.get("pairs"),
            "labels": comp.get("labels"),
            "note": "Real accuracy signal: frozen, team-authored benchmark — a "
                    "benchmark result, not field-validated. The detection and "
                    "text_eval blocks below are structured-baseline metrics "
                    "(1.000 by construction; see their `basis` fields), not a "
                    "capability measurement.",
        }
    except Exception:
        return {"note": "benchmark card unavailable"}


def _compute_metrics():
    from eval.baseline_reconciler import reconcile
    from eval.run_eval import load_ground_truth, score

    gt = load_ground_truth()
    findings = reconcile()
    r = score(findings, gt)

    from eval.text_eval import aggregate as text_agg
    from eval.text_eval import run_text_eval
    text_results = run_text_eval()
    text_aggregate = text_agg(text_results)

    gt_json = _load_json("ground_truth.json")
    project_info = gt_json.get("project", {})

    return {
        "detection": {
            "total_deviations": len(gt),
            "critical": sum(1 for d in gt if d.get("severity") == "Critical"),
            "major": sum(1 for d in gt if d.get("severity") == "Major"),
            "baseline_precision": round(r["precision"], 3),
            "baseline_recall": round(r["recall"], 3),
            "baseline_f1": round(r["f1"], 3),
            "false_positive_rate": round(r["false_positive_rate"], 3),
        },
        "text_eval": {
            "method": "regex extraction from raw markdown (non-circular)",
            "projects_evaluated": text_aggregate["projects"],
            "total_deviations": text_aggregate["total_deviations"],
            "precision": text_aggregate["aggregate_precision"],
            "recall": text_aggregate["aggregate_recall"],
            "f1": text_aggregate["aggregate_f1"],
        },
        "commissioning": {
            "cx_prediction_accuracy": round(r["cx_prediction_accuracy"], 3),
            "mean_lead_time_weeks": round(r["mean_lead_time_weeks"], 1),
            "max_lead_time_weeks": r["max_lead_time_weeks"],
            "total_lead_time_weeks": r["total_lead_time_weeks"],
            # Honesty annotation: on the structured baseline, cx_prediction_accuracy
            # is echoed from ground truth (1.000 by construction), not predicted.
            # Capability is measured by the real-datasheet eval, not this number.
            "basis": "structured baseline — cx echoed from ground truth (by construction)",
        },
        "corpus": {
            "systems_modeled": len(list((CORPUS / "specs").glob("*.md")))
                               or len(set(d["system"] for d in gt)),
            "requirements_modeled": _count_requirements(),
            "active_submittals": project_info.get("active_submittals", 0),
            "true_negative_systems": r["true_negative_systems"],
            # Enterprise projection, not what the demo corpus models — labelled
            # explicitly so the live number can't be mistaken for actuals.
            "scale_target_line_items_per_project": project_info.get("line_items_total", 0),
        },
        "citation_faithfulness": round(r["citation_faithfulness"], 3),
        # Baseline findings are not citation-checked, so this is the by-construction
        # structured value — not a capability measurement (see real-datasheet eval).
        "citation_faithfulness_basis": "structured baseline — not citation-checked (by construction)",
        # The real accuracy signal, foregrounded so /metrics can't be misread as
        # a headline 1.000 (the blocks above are structured-baseline, by construction).
        "benchmark_headline": _benchmark_headline(),
    }
