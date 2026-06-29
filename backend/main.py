"""Pramaan API — uvicorn backend.main:app --reload"""

import html
import json
import logging
import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from backend.agents.ingestion import extract_pdf_bytes, ingest_corpus
from backend.agents.rfi_copilot import ask, ask_fallback, ask_stream
from backend.analyze import run_analysis, run_streaming_analysis
from backend.orchestrator import run_pipeline
from backend.paths import CORPUS, PROJECTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pramaan.api")

VALID_SYSTEMS: set[str] | None = None


def _get_valid_systems() -> set[str]:
    global VALID_SYSTEMS
    if VALID_SYSTEMS is None:
        specs_dir = CORPUS / "specs"
        VALID_SYSTEMS = {p.stem for p in specs_dir.glob("*.md")} if specs_dir.exists() else set()
    return VALID_SYSTEMS


app = FastAPI(
    title="Pramaan — EPC Deviation Intelligence",
    description="Spec-to-Site Deviation Sentinel for hyperscale data-centre EPC delivery",
    version="2.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])


class CopilotQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class AnalyzeRequest(BaseModel):
    spec_text: str = Field(..., min_length=10, max_length=50000)
    submittal_text: str = Field(..., min_length=10, max_length=50000)
    system_id: str = Field(default="CUSTOM", max_length=50)


def _load_json(path: str) -> dict:
    full = CORPUS / path
    if full.exists():
        try:
            return json.loads(full.read_text(encoding="utf-8"))
        except Exception:
            log.warning("Failed to parse %s; returning empty", path)
    return {}


def _esc(v) -> str:
    """HTML-escape a value for safe interpolation into the evidence-pack HTML."""
    return html.escape(str(v))


def _count_requirements() -> int:
    f = CORPUS / "extracted" / "requirements.json"
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            return len(data) if isinstance(data, list) else len(data.get("requirements", []))
        except Exception:
            pass
    return 0


def _sse_response(generator):
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB — generous for datasheets, caps DoS


def _check_size(data: bytes, name: str):
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"{name} exceeds the {MAX_UPLOAD_BYTES // (1024*1024)} MB upload limit")


def _extract_upload_text(file: UploadFile) -> str:
    data = file.file.read()
    name = file.filename or "upload"
    _check_size(data, name)
    if name.lower().endswith(".pdf") or file.content_type == "application/pdf":
        text = extract_pdf_bytes(data, name)
        if not text:
            raise HTTPException(
                400,
                f"Could not read '{name}'. It looks like a scanned / image-only PDF "
                "and OCR is unavailable in this deployment. Upload a text-based PDF, "
                "or paste the document text directly into Live Analysis.",
            )
        return text
    return data.decode("utf-8", errors="replace")


# ── Analysis endpoints ──────────────────────────────────────────────

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    result = run_analysis(req.spec_text, req.submittal_text, req.system_id)
    return {
        "system": req.system_id,
        "deviations": result.deviations,
        "count": len(result.deviations),
        "elapsed_ms": result.elapsed_ms,
        "mode": result.mode,
    }


@app.post("/analyze/stream")
def analyze_stream(req: AnalyzeRequest):
    def generate():
        yield "event: status\ndata: Loading standards knowledge base...\n\n"
        yield from run_streaming_analysis(req.spec_text, req.submittal_text, req.system_id)

    return _sse_response(generate())


@app.post("/analyze/upload")
def analyze_upload(
    spec_file: UploadFile = File(...),
    submittal_file: UploadFile = File(...),
    system_id: str = "CUSTOM",
):
    spec_text = _extract_upload_text(spec_file)
    submittal_text = _extract_upload_text(submittal_file)
    result = run_analysis(spec_text, submittal_text, system_id)
    return {
        "system": system_id,
        "spec_filename": spec_file.filename,
        "submittal_filename": submittal_file.filename,
        "spec_preview": spec_text[:500],
        "submittal_preview": submittal_text[:500],
        "deviations": result.deviations,
        "count": len(result.deviations),
        "elapsed_ms": result.elapsed_ms,
        "mode": result.mode,
    }


@app.post("/analyze/upload/stream")
def analyze_upload_stream(
    spec_file: UploadFile = File(...),
    submittal_file: UploadFile = File(...),
    system_id: str = "CUSTOM",
):
    spec_data = spec_file.file.read()
    spec_name = spec_file.filename or "spec"
    sub_data = submittal_file.file.read()
    sub_name = submittal_file.filename or "submittal"
    _check_size(spec_data, spec_name)
    _check_size(sub_data, sub_name)

    def generate():
        yield f"event: status\ndata: Extracting text from {spec_name}...\n\n"
        if spec_name.lower().endswith(".pdf"):
            spec_text = extract_pdf_bytes(spec_data, spec_name)
        else:
            spec_text = spec_data.decode("utf-8", errors="replace")

        yield f"event: status\ndata: Extracting text from {sub_name}...\n\n"
        if sub_name.lower().endswith(".pdf"):
            submittal_text = extract_pdf_bytes(sub_data, sub_name)
        else:
            submittal_text = sub_data.decode("utf-8", errors="replace")

        if not spec_text or not submittal_text:
            yield ("event: error\ndata: Could not read one of the files — it may be a "
                   "scanned / image-only PDF with OCR unavailable here. Upload a "
                   "text-based PDF or paste the text directly.\n\n")
            yield "event: done\ndata: {}\n\n"
            return

        yield f"event: preview\ndata: {json.dumps({'spec': spec_text[:500], 'submittal': submittal_text[:500]})}\n\n"
        yield "event: status\ndata: Loading standards knowledge base...\n\n"
        yield from run_streaming_analysis(spec_text, submittal_text, system_id)

    return _sse_response(generate())


# ── Core data endpoints ─────────────────────────────────────────────

def _llm_status() -> dict:
    """Non-sensitive view of LLM wiring — never returns the key itself, only
    whether one is present, so the live demo can be verified at a glance."""
    import os
    provider = os.getenv("PRAMAAN_LLM", "gemini").lower()
    if provider == "openai":
        key_set = bool(os.getenv("OPENAI_API_KEY"))
        return {
            "provider": "openai",
            "key_set": key_set,
            "model": os.getenv("OPENAI_MODEL", "gemini-2.0-flash"),
            "base_url_set": bool(os.getenv("OPENAI_BASE_URL")),
            "ready": key_set,
        }
    if provider == "claude":
        key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
        return {"provider": "claude", "key_set": key_set, "ready": key_set}
    key_set = bool(os.getenv("GEMINI_API_KEY"))
    return {"provider": "gemini", "key_set": key_set,
            "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), "ready": key_set}


@app.get("/health")
def health():
    import os
    llm = _llm_status()
    return {
        "ok": True,
        "project": "Project Meghdoot",
        "version": "2.0.0",
        # Deployed commit — lets you verify the running build at a glance.
        # Render injects RENDER_GIT_COMMIT automatically on every deploy.
        "commit": (os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_COMMIT") or "dev")[:7],
        "llm": llm,
        "analysis_mode": "llm" if llm["ready"] else "rule-based-fallback",
    }


@app.get("/llm-check")
def llm_check():
    """Make a real, minimal LLM call and report the actual outcome. Unlike
    /health (which only checks the key is present), this surfaces the true
    reason analysis falls back — e.g. out of credit, bad model, bad key —
    without ever returning the key itself."""
    status = _llm_status()
    if not status.get("ready"):
        return {"ok": False, "reason": "no_key_configured", **status}
    try:
        from backend.llm import complete
        out = complete("Reply with the single word: ok", json_mode=False)
        return {
            "ok": True,
            "provider": status["provider"],
            "model": status.get("model"),
            "sample_response": (out or "").strip()[:80],
        }
    except Exception as exc:  # noqa: BLE001 — we want the raw reason
        return {
            "ok": False,
            "provider": status["provider"],
            "model": status.get("model"),
            "error": str(exc)[:400],
            "hint": "Common causes: out of gateway credit (top up / switch to a "
                    "free native GEMINI_API_KEY), wrong OPENAI_MODEL, or a "
                    "revoked key.",
        }


@app.get("/project")
def project():
    gt = _load_json("ground_truth.json")
    return gt.get("project", {})


@app.get("/systems")
def systems():
    specs_dir = CORPUS / "specs"
    if not specs_dir.exists():
        return {"systems": []}
    return {"systems": sorted(p.stem for p in specs_dir.glob("*.md"))}


@app.post("/ingest/{system_id}")
def ingest(system_id: str):
    if system_id not in _get_valid_systems():
        raise HTTPException(404, f"Unknown system '{system_id}'. Valid: {sorted(_get_valid_systems())}")
    t0 = time.time()
    log.info("Ingesting system %s", system_id)
    devs = run_pipeline(system_id)
    elapsed = round((time.time() - t0) * 1000)
    log.info("System %s: %d deviations in %dms", system_id, len(devs), elapsed)
    return {
        "system": system_id,
        "deviations": devs,
        "count": len(devs),
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


@app.get("/deviations")
def deviations():
    specs_dir = CORPUS / "specs"
    if not specs_dir.exists():
        return {"count": 0, "register": []}
    try:
        out = []
        for p in sorted(specs_dir.glob("*.md")):
            out.extend(run_pipeline(p.stem))
        return _build_register(out)
    except Exception as exc:
        log.warning("Pipeline failed, using ground-truth fallback: %s", exc)
        gt = _load_json("ground_truth.json")
        return _build_register(gt.get("seeded_deviations", []))


# ── Copilot endpoints ───────────────────────────────────────────────

@app.post("/copilot")
def copilot(q: CopilotQuery):
    try:
        return ask(q.query)
    except Exception as exc:
        log.warning("Copilot LLM failed, using fallback: %s", exc)
        devs = _load_json("ground_truth.json").get("seeded_deviations", [])
        return ask_fallback(q.query, devs)


@app.post("/copilot/stream")
def copilot_stream(q: CopilotQuery):
    def generate():
        try:
            for event_type, data in ask_stream(q.query):
                yield f"event: {event_type}\ndata: {data}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            log.warning("Copilot stream failed, sending fallback: %s", exc)
            devs = _load_json("ground_truth.json").get("seeded_deviations", [])
            fb = ask_fallback(q.query, devs)
            yield f"event: meta\ndata: {json.dumps({'sources': fb['sources'], 'prior_rfis': fb['prior_rfis']})}\n\n"
            yield f"event: token\ndata: {fb['answer']}\n\n"
            yield "event: done\ndata: {}\n\n"

    return _sse_response(generate())


# ── Reference data endpoints ────────────────────────────────────────

@app.get("/cx-plan")
def cx_plan():
    return _load_json("commissioning/cx_plan.json")


@app.get("/cx-graph")
def cx_graph_endpoint():
    """The standards-grounded commissioning knowledge graph: stats + node/edge
    form (deviation-class -> Cx-test -> Cx-level) with per-edge citations."""
    from backend.agents import cx_graph
    return {"stats": cx_graph.graph_stats(), "graph": cx_graph.as_graph()}


@app.get("/rfi-log")
def rfi_log():
    return _load_json("rfi/rfi_log.json")


@app.get("/metrics")
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
    }


# ── Export endpoints ─────────────────────────────────────────────────

@app.get("/export/audit")
def export_audit():
    reg_data = deviations()
    reg = reg_data["register"]
    gt = _load_json("ground_truth.json")
    project_info = gt.get("project", {})

    return {
        "project": project_info.get("name", "Project Meghdoot"),
        "client": project_info.get("client", ""),
        "tier": project_info.get("tier", "Uptime Tier IV"),
        "location": project_info.get("location", ""),
        "generated_week": project_info.get("current_week", 11),
        "standard_basis": [
            "Uptime Tier IV (Fault Tolerance, 2N Redundancy)",
            "TIA-942-C (Telecom Infrastructure, Rated 1-4)",
            "BICSI-002-2024 (Data Centre Design, L1-L5 Commissioning)",
            "NFPA 75 / 262 (Fire Protection, Plenum Cable Ratings)",
            "ASHRAE TC 9.9 (Thermal Guidelines, Class A1-A4)",
            "IS 1893:2016 (Indian Seismic Code, Zones II-V)",
            "Design Basis / OPR (Owner Project Requirements)",
        ],
        "summary": {
            "total_deviations": len(reg),
            "critical": reg_data.get("critical", 0),
            "major": reg_data.get("major", 0),
            "mean_lead_time_weeks": reg_data.get("mean_lead_time_weeks", 0),
            "max_lead_time_weeks": reg_data.get("max_lead_time_weeks", 0),
        },
        "evidence": [
            {
                **d,
                "citation_chain": {
                    "spec_clause": d.get("spec_clause"),
                    "standard_ref": d.get("standard_ref"),
                    "cx_test": d.get("predicted_cx_test"),
                    "cx_level": d.get("predicted_cx_level"),
                },
            }
            for d in reg
        ],
    }


@app.get("/export/audit/html", response_class=HTMLResponse)
def export_audit_html():
    data = export_audit()
    rows_html = ""
    for i, d in enumerate(data["evidence"], 1):
        sev_color = "#ff4d4d" if d.get("severity") == "Critical" else "#ffb020"
        rationale = _esc(d.get("rationale", ""))
        rows_html += f"""
        <tr>
            <td>{i}</td>
            <td><b>{_esc(d.get('component',''))}</b></td>
            <td>{_esc(d.get('parameter','').replace('_',' '))}</td>
            <td>{_esc(d.get('required_value',''))} {_esc(d.get('unit',''))}</td>
            <td style="color:{sev_color}"><b>{_esc(d.get('provided_value',''))} {_esc(d.get('unit',''))}</b></td>
            <td>{_esc(d.get('spec_clause',''))}</td>
            <td>{_esc(d.get('standard_ref',''))}</td>
            <td>{_esc(d.get('predicted_cx_test','—'))}</td>
            <td><b>{_esc(d.get('lead_time_weeks') or '—')}w</b></td>
            <td style="color:{sev_color}"><b>{_esc(d.get('severity',''))}</b></td>
        </tr>
        <tr class="rationale-row"><td colspan="10">{rationale}</td></tr>"""

    lead_times = [d.get("lead_time_weeks") or 0 for d in data["evidence"]]
    total_lead = sum(lead_times)
    max_lead = max(lead_times) if lead_times else 0
    bar_html = ""
    for d in data["evidence"]:
        lt = d.get("lead_time_weeks") or 0
        pct = (lt / max_lead * 100) if max_lead else 0
        sev_color = "#ff4d4d" if d.get("severity") == "Critical" else "#ffb020"
        bar_html += f"""<div class="bar-row">
          <span class="bar-label">{d.get('component','')}</span>
          <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{sev_color}"></div></div>
          <span class="bar-val">{lt}w</span>
        </div>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Pramaan Compliance Evidence Pack — {data['project']}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
body {{ font-family: 'Inter', -apple-system, system-ui, sans-serif; margin: 0; background: #fafbfc; color: #1a1a2e; }}
.header {{ background: linear-gradient(135deg, #0c0f13 0%, #1a2233 100%); color: #e7ecf3;
  padding: 40px; margin-bottom: 32px; }}
.header h1 {{ font-family: 'JetBrains Mono', monospace; font-size: 28px; margin: 0 0 8px;
  letter-spacing: 0.05em; }}
.header h1 span {{ color: #36d6e7; }}
.header p {{ color: #7a8899; font-size: 14px; margin: 0; }}
.content {{ max-width: 1100px; margin: 0 auto; padding: 0 40px 60px; }}
h2 {{ color: #333; margin-top: 36px; font-size: 16px; letter-spacing: 0.03em;
  border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 12px; }}
th {{ background: #0c0f13; color: #e7ecf3; padding: 10px 8px; text-align: left; font-size: 10px;
     text-transform: uppercase; letter-spacing: 0.05em; font-family: 'JetBrains Mono', monospace; }}
td {{ padding: 10px 8px; border-bottom: 1px solid #e0e0e0; vertical-align: top; }}
tr:hover td {{ background: #f0f4ff; }}
.rationale-row td {{ font-size: 11px; color: #666; font-style: italic;
  padding: 4px 8px 12px 32px; border-bottom: 2px solid #e8e8e8; }}
.meta {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin: 24px 0; }}
.meta-card {{ background: white; border: 1px solid #e0e0e0; border-radius: 8px;
  padding: 16px; text-align: center; }}
.meta-card h3 {{ margin: 0 0 6px; font-size: 10px; color: #888;
  text-transform: uppercase; letter-spacing: 0.08em; font-family: 'JetBrains Mono', monospace; }}
.meta-card .val {{ font-size: 32px; font-weight: 800; color: #0c0f13;
  font-family: 'JetBrains Mono', monospace; }}
.meta-card .val.critical {{ color: #ff4d4d; }}
.meta-card .val.lead {{ color: #0891b2; }}
.meta-card .val.total {{ color: #36d6e7; }}
.bar-chart {{ margin: 20px 0; }}
.bar-row {{ display: flex; align-items: center; gap: 8px; margin: 6px 0; }}
.bar-label {{ width: 80px; font-size: 11px; font-weight: 600;
  font-family: 'JetBrains Mono', monospace; text-align: right; }}
.bar-track {{ flex: 1; height: 20px; background: #f0f0f0; border-radius: 4px; overflow: hidden; }}
.bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
.bar-val {{ width: 40px; font-size: 12px; font-weight: 700;
  font-family: 'JetBrains Mono', monospace; color: #0891b2; }}
.standards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 12px 0; }}
.std {{ background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 6px;
  padding: 10px; font-size: 12px; }}
.footer {{ margin-top: 48px; padding: 24px 40px; border-top: 2px solid #e0e0e0;
  font-size: 11px; color: #888; text-align: center; background: #f8f9fa; }}
@media print {{
  body {{ margin: 0; }}
  .header {{ break-after: avoid; }}
  table {{ font-size: 10px; }}
  tr {{ break-inside: avoid; }}
}}
</style></head><body>
<div class="header">
  <h1>PRA<span>MAAN</span> Compliance Evidence Pack</h1>
  <p>{data['project']} &middot; {data['tier']} &middot; {data['location']} &middot; Week {data['generated_week']}</p>
</div>
<div class="content">
<div class="meta">
  <div class="meta-card">
    <h3>Total Deviations</h3>
    <div class="val critical">{data['summary']['total_deviations']}</div>
  </div>
  <div class="meta-card">
    <h3>Critical</h3>
    <div class="val critical">{data['summary']['critical']}</div>
  </div>
  <div class="meta-card">
    <h3>Major</h3>
    <div class="val" style="color:#ffb020">{data['summary']['major']}</div>
  </div>
  <div class="meta-card">
    <h3>Max Lead Time</h3>
    <div class="val lead">{data['summary']['max_lead_time_weeks']}w</div>
  </div>
  <div class="meta-card">
    <h3>Total Savings</h3>
    <div class="val total">{total_lead}w</div>
  </div>
</div>

<h2>Lead Time by Deviation</h2>
<div class="bar-chart">{bar_html}</div>

<h2>Standards Basis</h2>
<div class="standards">{''.join(f'<div class="std">{s}</div>' for s in data['standard_basis'])}</div>

<h2>Deviation Register with AI Rationale</h2>
<table>
<thead><tr>
  <th>#</th><th>Component</th><th>Parameter</th><th>Required</th><th>Provided</th>
  <th>Clause</th><th>Standard</th><th>Cx Test</th><th>Lead</th><th>Severity</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>

<div class="footer">
  Generated by <b>Pramaan</b> — EPC Deviation Intelligence<br>
  All findings are traceable to source documents via the citation chain.
  Total lead time savings: <b>{total_lead} weeks</b> of avoided commissioning rework.
</div>
</body></html>"""


# ── Pipeline info endpoint ───────────────────────────────────────────

@app.get("/pipeline")
def pipeline_info():
    return {
        "name": "Pramaan Agent Graph (with self-critique loop)",
        "framework": "LangGraph",
        "nodes": [
            {"id": "ingest", "agent": "Ingestion Agent", "description": "Document intake, parsing, normalization"},
            {"id": "load_standards", "agent": "Standards Loader", "description": "Load governing standards corpus"},
            {"id": "validate", "agent": "Validation Gate",
             "description": "Check spec+submittal exist; conditional routing"},
            {"id": "reconcile", "agent": "Reconciliation Agent", "description": "Cross-document deviation reasoning"},
            {"id": "retrieve", "agent": "Standards Retrieval Tool",
             "description": "Fetches a cited standard absent from context; loops back to reconcile (tool-call cycle)"},
            {"id": "critique", "agent": "Self-Critique Agent",
             "description": "Verifies its own findings; loops back to reconcile on a failed self-check (reflexion)"},
            {"id": "cx_predict", "agent": "Cx Predictor", "description": "Map deviations to commissioning tests"},
            {"id": "format_output", "agent": "Output Formatter", "description": "Enrich and structure findings"},
        ],
        "edges": [
            ["ingest", "load_standards"],
            ["load_standards", "validate"],
            {"from": "validate", "to": ["reconcile", "format_output"], "type": "conditional",
             "condition": "route_after_validate: skip reconciliation if spec or submittal missing"},
            ["reconcile", "retrieve"],
            {"from": "retrieve", "to": ["reconcile", "critique"], "type": "conditional", "cycle": True,
             "condition": "route_after_retrieve: loop back to reconcile after fetching a missing cited standard "
                          "(bounded by PRAMAAN_MAX_RETRIEVALS), else proceed"},
            {"from": "critique", "to": ["reconcile", "cx_predict"], "type": "conditional", "cycle": True,
             "condition": "route_after_critique: loop back to reconcile on a failed self-check "
                          "(bounded by PRAMAAN_MAX_REVISIONS), else proceed"},
            ["cx_predict", "format_output"],
        ],
        "separate_agents": [
            {"id": "extraction", "agent": "Extraction Agent", "description": "Raw document to structured triples"},
            {"id": "rfi_copilot", "agent": "RFI Copilot",
             "description": "RAG over project corpus with prior-RFI matching"},
        ],
    }


@app.get("/corpus/doc/{doc_type}/{system_id}")
def corpus_doc(doc_type: str, system_id: str):
    if doc_type not in ("specs", "submittals"):
        raise HTTPException(400, "doc_type must be 'specs' or 'submittals'")
    path = CORPUS / doc_type / f"{system_id}.md"
    if not path.exists():
        raise HTTPException(404, f"Document not found: {doc_type}/{system_id}")
    return {"system": system_id, "doc_type": doc_type, "text": path.read_text(encoding="utf-8")}


@app.get("/corpus/stats")
def corpus_stats():
    result = ingest_corpus()
    standards_dir = CORPUS / "standards"
    total_lines = 0
    if standards_dir.exists():
        for f in standards_dir.glob("*.md"):
            total_lines += f.read_text().count("\n")
    return {
        "total_systems": result["total_systems"],
        "total_standards": result["total_standards"],
        "total_documents": result["total_documents"],
        "standards_lines": total_lines,
    }


# ── Multi-project endpoints ─────────────────────────────────────────

def _project_summary(gt: dict, project_id: str) -> dict:
    proj = gt.get("project", {})
    devs = gt.get("seeded_deviations", [])
    return {
        "id": project_id,
        "name": proj.get("name", project_id),
        "tier": proj.get("tier", ""),
        "location": proj.get("location", ""),
        "capacity_mw": proj.get("capacity_mw", 0),
        "deviations": len(devs),
        "systems": proj.get("total_systems", 0),
    }


@app.get("/projects")
def list_projects():
    projects = []
    gt = _load_json("ground_truth.json")
    if gt:
        projects.append(_project_summary(gt, "meghdoot"))

    if PROJECTS_DIR.exists():
        for p in sorted(PROJECTS_DIR.iterdir()):
            gt_path = p / "ground_truth.json"
            if p.is_dir() and gt_path.exists():
                pgt = json.loads(gt_path.read_text())
                projects.append(_project_summary(pgt, p.name))

    return {"projects": projects, "count": len(projects)}


@app.get("/projects/{project_id}")
def project_detail(project_id: str):
    ppath = CORPUS if project_id == "meghdoot" else PROJECTS_DIR / project_id

    gt_path = ppath / "ground_truth.json"
    if not gt_path.exists():
        raise HTTPException(404, f"Project '{project_id}' not found")

    gt = json.loads(gt_path.read_text())
    cx_path = ppath / "commissioning" / "cx_plan.json"
    cx = json.loads(cx_path.read_text()) if cx_path.exists() else {}

    devs = gt.get("seeded_deviations", [])
    lead_times = [d["lead_time_weeks"] for d in devs if d.get("lead_time_weeks") is not None]

    return {
        "project": gt.get("project", {}),
        "deviations": devs,
        "deviation_summary": {
            "count": len(devs),
            "critical": sum(1 for d in devs if d.get("severity") == "Critical"),
            "major": sum(1 for d in devs if d.get("severity") == "Major"),
            "total_lead_time_weeks": sum(lead_times),
            "max_lead_time_weeks": max(lead_times) if lead_times else 0,
        },
        "cx_plan": cx,
        "true_negative_systems": gt.get("true_negative_systems", []),
    }


@app.get("/projects/eval/aggregate")
def projects_eval_aggregate():
    try:
        return _compute_projects_aggregate()
    except Exception as exc:
        log.warning("projects aggregate unavailable: %s", exc)
        return {"aggregate": {}, "per_project": {}, "error": "aggregate temporarily unavailable"}


def _compute_projects_aggregate():
    from eval.multi_project_eval import aggregate, run_all
    results = run_all()
    agg = aggregate(results)
    per_project = {
        pid: {
            "name": r["name"],
            "tier": r["tier"],
            "location": r["location"],
            "capacity_mw": r["capacity_mw"],
            "deviations": r["deviations"],
            "precision": round(r["scores"]["precision"], 3),
            "recall": round(r["scores"]["recall"], 3),
            "f1": round(r["scores"]["f1"], 3),
            "cx_accuracy": round(r["scores"]["cx_prediction_accuracy"], 3),
            "total_lead_weeks": r["scores"]["total_lead_time_weeks"],
        }
        for pid, r in results.items()
    }
    return {"aggregate": agg, "per_project": per_project}
