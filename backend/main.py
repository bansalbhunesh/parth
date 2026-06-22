"""
Pramaan API — FastAPI.

Endpoints:
  GET  /health
  GET  /systems                 list modelled systems
  POST /ingest/{system_id}      run the pipeline for one system -> deviations
  GET  /deviations              full deviation register (all systems)
  POST /copilot                 RFI/project copilot Q&A  {"query": "..."}
  GET  /export/audit            deviation register as a compliance evidence pack

Run: uvicorn backend.main:app --reload
"""

import json
import pathlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.orchestrator import run_pipeline
from backend.agents.rfi_copilot import ask

CORPUS = pathlib.Path(__file__).parent.parent / "data" / "corpus"

app = FastAPI(title="Pramaan — EPC Deviation Intelligence")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])


class CopilotQuery(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"ok": True, "project": "Project Meghdoot"}


@app.get("/systems")
def systems():
    return {"systems": sorted(p.stem for p in (CORPUS / "specs").glob("*.md"))}


@app.post("/ingest/{system_id}")
def ingest(system_id: str):
    return {"system": system_id, "deviations": run_pipeline(system_id)}


@app.get("/deviations")
def deviations():
    out = []
    for p in sorted((CORPUS / "specs").glob("*.md")):
        out.extend(run_pipeline(p.stem))
    return {"count": len(out), "register": out}


@app.post("/copilot")
def copilot(q: CopilotQuery):
    return ask(q.query)


@app.get("/export/audit")
def export_audit():
    reg = deviations()["register"]
    return {
        "project": "Project Meghdoot",
        "standard_basis": ["Uptime Tier IV", "TIA-942", "BICSI-002", "NFPA 75"],
        "total_deviations": len(reg),
        "critical": sum(1 for d in reg if d.get("severity") == "Critical"),
        "evidence": reg,
    }
