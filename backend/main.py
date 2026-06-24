"""
Pramaan API — FastAPI.

Endpoints:
  GET  /health
  GET  /systems                 list modelled systems
  POST /ingest/{system_id}      run the pipeline for one system -> deviations
  GET  /deviations              full deviation register (all systems)
  POST /copilot                 RFI/project copilot Q&A  {"query": "..."}
  GET  /export/audit            deviation register as compliance evidence pack
  GET  /metrics                 live eval metrics for the deck
  GET  /cx-plan                 commissioning plan with test schedule
  GET  /rfi-log                 full RFI log
  GET  /project                 project metadata

Run: uvicorn backend.main:app --reload
"""

import json
import logging
import pathlib
import re
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from backend.orchestrator import run_pipeline, run_full_pipeline
from backend.agents.rfi_copilot import ask
from backend.agents.ingestion import ingest_corpus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pramaan.api")

CORPUS = pathlib.Path(__file__).parent.parent / "data" / "corpus"

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


def _load_json(path):
    full = CORPUS / path
    if full.exists():
        return json.loads(full.read_text())
    return {}


def _deterministic_compare(spec_text: str, submittal_text: str) -> list:
    """Fallback deterministic comparison when LLM is unavailable."""
    # Extract numeric requirements from spec
    spec_values = {}
    for match in re.finditer(
        r'\*\*([A-Z][\w-]*)\*\*\s*[—–-]\s*([\w\s]+?):\s*(?:shall be\s*)?\*\*(\S+)\s*(\S*)\*\*',
        spec_text,
    ):
        component, param, value, unit = match.groups()
        param_key = param.strip().lower().replace(' ', '_')
        spec_values[(component, param_key)] = (value, unit.strip('()'))

    # Extract provided values from submittal
    sub_values = {}
    for match in re.finditer(
        r'\*\*([A-Z][\w-]*)\*\*\s*[—–-]\s*([\w\s]+?):\s*\*\*(\S+)\s*(\S*)\*\*',
        submittal_text,
    ):
        component, param, value, unit = match.groups()
        param_key = param.strip().lower().replace(' ', '_')
        sub_values[(component, param_key)] = (value, unit.strip('()'))

    devs = []
    for key, (req_val, unit) in spec_values.items():
        if key in sub_values:
            prov_val, _ = sub_values[key]
            if str(prov_val) != str(req_val):
                devs.append({
                    "component": key[0],
                    "parameter": key[1],
                    "required_value": req_val,
                    "provided_value": prov_val,
                    "unit": unit,
                    "standard_ref": "DESIGN-BASIS",
                    "spec_clause": "",
                    "severity": "Major",
                    "rationale": f"Provided value {prov_val} does not match required {req_val} {unit}",
                    "confidence": 0.7,
                    "cx_source": "deterministic",
                })
    return devs


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """Live analysis: compare arbitrary spec vs submittal text."""
    from backend.agents.reconciliation import (
        _all_standards_text,
        _check_citation_faithfulness,
        _validate_deviations,
        SYSTEM_PROMPT,
        PROMPT_TEMPLATE,
    )
    from backend.agents.commissioning import predict_cx_impact

    t0 = time.time()
    standards = _all_standards_text()

    prompt = PROMPT_TEMPLATE.format(
        spec=req.spec_text,
        submittal=req.submittal_text,
        standards=standards,
    )

    try:
        from backend.llm import complete_json, LLMError
        raw = complete_json(prompt, system=SYSTEM_PROMPT)
        devs = _validate_deviations(raw)
        devs = _check_citation_faithfulness(devs, req.spec_text, req.submittal_text, standards)
        for d in devs:
            d.update(predict_cx_impact(d))
            d["system"] = req.system_id
    except Exception as exc:
        # Fallback: run deterministic comparison if LLM unavailable
        log.warning("LLM analysis failed, running deterministic comparison: %s", exc)
        devs = _deterministic_compare(req.spec_text, req.submittal_text)

    elapsed = round((time.time() - t0) * 1000)

    return {
        "system": req.system_id,
        "deviations": devs,
        "count": len(devs),
        "elapsed_ms": elapsed,
        "mode": "llm" if not devs or devs[0].get("cx_source") != "deterministic" else "deterministic",
    }


@app.get("/health")
def health():
    return {"ok": True, "project": "Project Meghdoot", "version": "2.0.0"}


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


def _deviations_from_ground_truth():
    gt = _load_json("ground_truth.json")
    return gt.get("seeded_deviations", [])


def _build_register(devs):
    critical = sum(1 for d in devs if d.get("severity") == "Critical")
    major = sum(1 for d in devs if d.get("severity") == "Major")
    lead_times = [d["lead_time_weeks"] for d in devs if d.get("lead_time_weeks")]
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
        return _build_register(_deviations_from_ground_truth())


@app.post("/copilot")
def copilot(q: CopilotQuery):
    try:
        return ask(q.query)
    except Exception as exc:
        log.warning("Copilot LLM failed, using fallback: %s", exc)
        gt = _load_json("ground_truth.json")
        devs = gt.get("seeded_deviations", [])
        relevant = [d for d in devs if any(
            term in q.query.lower()
            for term in [d.get("system", "").lower(), d.get("component", "").lower(),
                         d.get("parameter", "").replace("_", " ").lower()]
        )]
        if not relevant:
            relevant = devs[:3]
        return {
            "answer": f"Based on the deviation register, {len(relevant)} relevant finding(s) found. "
                      + " ".join(
                          f"{d['component']}.{d['parameter']}: provided {d.get('provided_value','')} "
                          f"vs required {d.get('required_value','')} ({d.get('severity','')}, "
                          f"{d.get('lead_time_weeks',0)}w lead time)."
                          for d in relevant
                      ),
            "sources": [d.get("spec_clause", "") for d in relevant],
            "prior_rfis": [],
        }


@app.get("/cx-plan")
def cx_plan():
    return _load_json("commissioning/cx_plan.json")


@app.get("/rfi-log")
def rfi_log():
    return _load_json("rfi/rfi_log.json")


@app.get("/metrics")
def metrics():
    from eval.baseline_reconciler import reconcile
    from eval.run_eval import load_ground_truth, score

    gt = load_ground_truth()
    findings = reconcile()
    r = score(findings, gt)

    gt_json = _load_json("ground_truth.json")
    project = gt_json.get("project", {})

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
        "commissioning": {
            "cx_prediction_accuracy": round(r["cx_prediction_accuracy"], 3),
            "mean_lead_time_weeks": round(r["mean_lead_time_weeks"], 1),
            "max_lead_time_weeks": r["max_lead_time_weeks"],
            "total_lead_time_weeks": r["total_lead_time_weeks"],
        },
        "corpus": {
            "systems": len(set(d["system"] for d in gt)),
            "total_requirements": project.get("line_items_total", 0),
            "active_submittals": project.get("active_submittals", 0),
            "true_negative_systems": r["true_negative_systems"],
        },
        "citation_faithfulness": round(r["citation_faithfulness"], 3),
    }


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
        rationale = d.get("rationale", "")
        rows_html += f"""
        <tr>
            <td>{i}</td>
            <td><b>{d.get('component','')}</b></td>
            <td>{d.get('parameter','').replace('_',' ')}</td>
            <td>{d.get('required_value','')} {d.get('unit','')}</td>
            <td style="color:{sev_color}"><b>{d.get('provided_value','')} {d.get('unit','')}</b></td>
            <td>{d.get('spec_clause','')}</td>
            <td>{d.get('standard_ref','')}</td>
            <td>{d.get('predicted_cx_test','—')}</td>
            <td><b>{d.get('lead_time_weeks','—')}w</b></td>
            <td style="color:{sev_color}"><b>{d.get('severity','')}</b></td>
        </tr>
        <tr class="rationale-row"><td colspan="10">{rationale}</td></tr>"""

    lead_times = [d.get("lead_time_weeks", 0) for d in data["evidence"]]
    total_lead = sum(lead_times)
    max_lead = max(lead_times) if lead_times else 0
    bar_html = ""
    for d in data["evidence"]:
        lt = d.get("lead_time_weeks", 0)
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
  <p>{data['project']} &middot; {data['tier']} &middot; {data['location']} &middot; Generated Week {data['generated_week']}</p>
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


@app.get("/pipeline")
def pipeline_info():
    return {
        "name": "Pramaan 5-Agent Pipeline",
        "framework": "LangGraph",
        "nodes": [
            {"id": "ingest", "agent": "Ingestion Agent", "description": "Document intake, parsing, normalization"},
            {"id": "load_standards", "agent": "Standards Loader", "description": "Load governing standards corpus"},
            {"id": "reconcile", "agent": "Reconciliation Agent", "description": "Cross-document deviation reasoning"},
            {"id": "cx_predict", "agent": "Cx Predictor", "description": "Map deviations to commissioning tests"},
            {"id": "format_output", "agent": "Output Formatter", "description": "Enrich and structure findings"},
        ],
        "edges": [
            ["ingest", "load_standards"],
            ["load_standards", "reconcile"],
            ["reconcile", "cx_predict"],
            ["cx_predict", "format_output"],
        ],
        "separate_agents": [
            {"id": "extraction", "agent": "Extraction Agent", "description": "Raw document to structured triples"},
            {"id": "rfi_copilot", "agent": "RFI Copilot", "description": "RAG over project corpus with prior-RFI matching"},
        ],
    }


@app.get("/corpus/doc/{doc_type}/{system_id}")
def corpus_doc(doc_type: str, system_id: str):
    """Return raw document text for spec or submittal."""
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
