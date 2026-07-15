from __future__ import annotations

import json
import logging
import os

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from backend import security
from backend.agents.ingestion import extract_pdf_bytes
from backend.analyze import run_analysis, run_streaming_analysis
from backend.api_context import (
    _PROTECT_ANALYSIS,
    _PROTECT_LLMCHECK,
    _PROTECT_UPLOAD,
    AnalyzeRequest,
    _extract_upload_doc,
    _extraction_meta,
    _read_capped,
    _sse_response,
    _sse_safe,
)
from backend.paths import CORPUS
from backend.uploads import validate_upload

router = APIRouter()
log = logging.getLogger("pramaan.api")

# ── Analysis endpoints ──────────────────────────────────────────────

@router.post("/analyze", dependencies=_PROTECT_ANALYSIS)
def analyze(req: AnalyzeRequest):
    # Routed through the input-hash cache: an identical spec+submittal (same
    # model/prompt version) is computed once and reused (cached=true), so a
    # flaky demo or a double-click never re-burns quota. Every response carries a
    # request_id + input_hash for traceability.
    from backend import jobs
    view = jobs.analyze_cached(req.spec_text, req.submittal_text, req.system_id)
    return {
        "system": req.system_id,
        "request_id": jobs.new_request_id(),
        "input_hash": view["input_hash"],
        "cached": view["cached"],
        "deviations": view["deviations"],
        "count": view["count"],
        "elapsed_ms": view["elapsed_ms"],
        "mode": view["mode"],
        "timing": view["timing"],
    }


# ── Job flow (async-style submit → poll → result) ───────────────────
# Prototype-level scalability proof: bounded in-memory jobs + cache, no broker.
# See backend/jobs.py and docs/SCALABILITY_PROOF.md.

@router.post("/jobs/analyze", status_code=202, dependencies=_PROTECT_ANALYSIS)
def submit_analyze_job(req: AnalyzeRequest):
    """Submit an analysis as a background job; returns immediately (202) with a
    job_id to poll. Same auth + analysis rate limit as /analyze."""
    from backend import jobs
    job = jobs.submit_job(req.spec_text, req.submittal_text, req.system_id,
                          jobs.new_request_id())
    return {
        "job_id": job["job_id"],
        "request_id": job["request_id"],
        "input_hash": job["input_hash"],
        "status": job["status"],
        "poll": f"/jobs/{job['job_id']}",
        "result": f"/jobs/{job['job_id']}/result",
    }


@router.get("/jobs/{job_id}", dependencies=[Depends(security.require_demo_auth)])
def get_job(job_id: str):
    """Lightweight status metadata for a job (no result body) — poll this."""
    from backend import jobs
    if not jobs.valid_job_id(job_id):
        raise HTTPException(404, "Unknown or expired job id.")
    st = jobs.job_status(job_id)
    if st is None:
        raise HTTPException(404, "Unknown or expired job id.")
    return st


@router.get("/jobs/{job_id}/result", dependencies=[Depends(security.require_demo_auth)])
def get_job_result(job_id: str):
    """The full analysis result once the job is done; 202 while still running,
    404 for an unknown/expired id."""
    from backend import jobs
    if not jobs.valid_job_id(job_id):
        raise HTTPException(404, "Unknown or expired job id.")
    status, result = jobs.job_result(job_id)
    if status is None:
        raise HTTPException(404, "Unknown or expired job id.")
    if status in ("queued", "running"):
        return JSONResponse(status_code=202,
                            content={"status": status, "job_id": job_id})
    if status == "error" or result is None:
        return JSONResponse(status_code=500,
                            content={"status": "error", "job_id": job_id,
                                     "error": "analysis failed"})
    return {"status": "done", "job_id": job_id, **result}


@router.post("/analyze/stream", dependencies=_PROTECT_ANALYSIS)
def analyze_stream(req: AnalyzeRequest):
    def generate():
        yield "event: status\ndata: Loading standards knowledge base...\n\n"
        yield from run_streaming_analysis(req.spec_text, req.submittal_text, req.system_id)

    return _sse_response(generate())


@router.post("/analyze/upload", dependencies=_PROTECT_UPLOAD)
def analyze_upload(
    spec_file: UploadFile = File(...),
    submittal_file: UploadFile = File(...),
    system_id: str = "CUSTOM",
):
    spec_doc = _extract_upload_doc(spec_file)
    submittal_doc = _extract_upload_doc(submittal_file)
    spec_text, submittal_text = spec_doc["text"], submittal_doc["text"]
    result = run_analysis(spec_text, submittal_text, system_id)
    return {
        "system": system_id,
        "spec_filename": spec_file.filename,
        "submittal_filename": submittal_file.filename,
        "spec_preview": spec_text[:500],
        "submittal_preview": submittal_text[:500],
        # How each document was read (text layer / OCR / image OCR) + any OCR caveat.
        "extraction": {
            "spec": _extraction_meta(spec_doc),
            "submittal": _extraction_meta(submittal_doc),
        },
        "deviations": result.deviations,
        "count": len(result.deviations),
        "elapsed_ms": result.elapsed_ms,
        "mode": result.mode,
        "telemetry": {
            "total_ms": result.elapsed_ms,
            "llm_call_ms": result.llm_call_ms,
            "standards_load_ms": result.standards_load_ms,
            "postprocess_ms": result.postprocess_ms,
            "provider": result.provider,
        },
    }


@router.post("/analyze/vision", dependencies=_PROTECT_UPLOAD)
def analyze_vision(
    spec_file: UploadFile = File(...),
    submittal_image: UploadFile = File(...),
    system_id: str = "CUSTOM",
):
    """Reconcile a text spec against a submittal supplied AS AN IMAGE — Gemini
    vision reads values straight from the picture (datasheet page, table, or
    drawing). Gemini-only (no text-model failover); on any failure returns
    mode='vision-unavailable' with no findings. Gate off with PRAMAAN_VISION=0.
    Capability evidence: data/samples/real/VISION_RESULT.md."""
    if os.getenv("PRAMAAN_VISION", "1") == "0":
        return {"available": False, "reason": "vision_disabled"}
    from backend.analyze import run_vision_analysis
    spec_name = spec_file.filename or "spec"
    img_name = submittal_image.filename or "submittal"
    spec_data = _read_capped(spec_file, spec_name)
    img_data = _read_capped(submittal_image, img_name)
    validate_upload(spec_name, spec_file.content_type or "", spec_data)
    validate_upload(img_name, submittal_image.content_type or "", img_data)
    spec_text = (extract_pdf_bytes(spec_data, spec_name)
                 if spec_name.lower().endswith(".pdf")
                 else spec_data.decode("utf-8", errors="replace"))
    mime = submittal_image.content_type or "image/png"
    result = run_vision_analysis(spec_text, img_data, mime, system_id)
    return {
        "system": system_id,
        "submittal_image": img_name,
        "mode": result.mode,
        "deviations": result.deviations,
        "count": len(result.deviations),
        "elapsed_ms": result.elapsed_ms,
        "telemetry": {
            "total_ms": result.elapsed_ms,
            "llm_call_ms": result.llm_call_ms,
            "standards_load_ms": result.standards_load_ms,
            "postprocess_ms": result.postprocess_ms,
            "provider": result.provider,
        },
    }


@router.post("/analyze/upload/stream", dependencies=_PROTECT_UPLOAD)
def analyze_upload_stream(
    spec_file: UploadFile = File(...),
    submittal_file: UploadFile = File(...),
    system_id: str = "CUSTOM",
):
    spec_name = spec_file.filename or "spec"
    sub_name = submittal_file.filename or "submittal"
    spec_data = _read_capped(spec_file, spec_name)
    sub_data = _read_capped(submittal_file, sub_name)
    # Validate synchronously so a bad upload returns a clean 4xx before the SSE
    # stream opens (never a partial event stream on a rejected file).
    validate_upload(spec_name, spec_file.content_type or "", spec_data)
    validate_upload(sub_name, submittal_file.content_type or "", sub_data)

    def generate():
        from backend.agents import ocr_util
        yield f"event: status\ndata: Extracting text from {_sse_safe(spec_name)}...\n\n"
        spec_doc = ocr_util.extract_document(spec_data, spec_name, spec_file.content_type or "")

        yield f"event: status\ndata: Extracting text from {_sse_safe(sub_name)}...\n\n"
        sub_doc = ocr_util.extract_document(sub_data, sub_name, submittal_file.content_type or "")

        spec_text, submittal_text = spec_doc["text"], sub_doc["text"]

        if not spec_text or not submittal_text:
            yield ("event: error\ndata: Could not read one of the files — it may be a "
                   "scanned / image-only PDF or image with OCR unavailable here. Upload a "
                   "text-based PDF or paste the text directly.\n\n")
            yield "event: done\ndata: {}\n\n"
            return

        # Tell the client HOW each document was read, and warn if OCR was used.
        yield ("event: extraction\ndata: "
               f"{json.dumps({'spec': _extraction_meta(spec_doc), 'submittal': _extraction_meta(sub_doc)})}\n\n")
        if spec_doc["ocr_used"] or sub_doc["ocr_used"]:
            yield f"event: status\ndata: {_sse_safe(ocr_util.OCR_WARNING)}\n\n"

        yield f"event: preview\ndata: {json.dumps({'spec': spec_text[:500], 'submittal': submittal_text[:500]})}\n\n"
        yield "event: status\ndata: Loading standards knowledge base...\n\n"
        yield from run_streaming_analysis(spec_text, submittal_text, system_id)

    return _sse_response(generate())


# ── Core data endpoints ─────────────────────────────────────────────

def _llm_status() -> dict:
    """Non-sensitive view of LLM wiring — never returns the key itself, only
    whether one is present, so the live demo can be verified at a glance.

    `ready` now reflects the whole failover chain: true if *any* configured
    provider can answer (the demo has an LLM), false only when every provider
    is unconfigured (the system runs on the deterministic rule-engine floor).
    `provider`/`model` describe the *primary* for display; `chain` lists the
    configured providers in the order they will be tried."""
    import os

    from backend.llm import (
        _gateway_base_url,
        _gateway_model,
        _key,
        _resolve_alias,
        provider_chain,
    )
    provider = _resolve_alias(os.getenv("PRAMAAN_LLM", "gemini").lower())
    chain = provider_chain()
    if provider == "openai":
        base = {
            "provider": "qwen",
            "key_set": bool(_key("openai")),
            "model": _gateway_model(),
            "base_url_set": bool(_gateway_base_url()),
        }
    elif provider == "claude":
        base = {"provider": "claude", "key_set": bool(_key("claude"))}
    elif provider == "ollama":
        base = {"provider": "ollama", "key_set": True,
                "model": os.getenv("OLLAMA_MODEL", "llama3.1")}
    else:
        base = {"provider": "gemini", "key_set": bool(_key("gemini")),
                "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash")}
    base["chain"] = chain
    base["ready"] = len(chain) > 0
    return base


@router.get("/health")
async def health():
    # Preserve the compatibility payload while avoiding worker-pool queueing.
    import os

    from backend.agents import ocr_util
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
        # True only when the tesseract binary is present AND OCR is enabled — so a
        # UI badge built on this can never imply OCR works where it does not.
        # Cached probe (no subprocess per health check). See /ocr-check for detail.
        "ocr_available": ocr_util.tesseract_available_cached() and ocr_util.ocr_enabled(),
        # Public-demo security posture: auth/rate-limit state + upload caps.
        # Booleans/caps only — never the token, never a client IP. See /health
        # consumers and docs/SECURITY_DEMO_RUNBOOK.md.
        "security": security.security_status(),
        # Prototype scalability proof: in-memory cache/job counters + the
        # pipeline signature used in the input hash. No secrets.
        "scalability": _scalability_status(),
    }


def _scalability_status() -> dict:
    from backend import jobs
    return jobs.stats()


@router.get("/ocr-check")
def ocr_check():
    """Report whether scanned-PDF / image OCR will actually run in THIS
    deployment. Unlike a doc claim, this is the ground truth: it live-probes the
    tesseract binary. Returns only booleans / ints / a version string — never a
    stack trace, path, or secret. A frontend OCR-status badge should read this."""
    from backend.agents import ocr_util
    installed = ocr_util.is_tesseract_available()
    enabled = ocr_util.ocr_enabled()
    ready = installed and enabled
    if not enabled:
        status = "disabled"        # turned off via PRAMAAN_OCR / PRAMAAN_OCR_ENABLED
    elif not installed:
        status = "tesseract_not_installed"
    else:
        status = "ready"
    return {
        "ocr_available": ready,
        "ocr_enabled": enabled,
        "tesseract_installed": installed,
        "tesseract_version": ocr_util.get_tesseract_version(),
        "image_ocr_supported": ready,
        "pdf_ocr_supported": ready,
        "max_pdf_pages": ocr_util.max_pdf_pages(),
        "max_image_pixels": ocr_util.max_image_pixels(),
        "status": status,
    }


def _probe_all_llms() -> dict:
    from backend.llm import failover_report, probe_provider

    probes = [probe_provider(provider) for provider in failover_report()["chain"]]
    return {
        "ok": any(probe["ok"] for probe in probes),
        "probe": "per-provider",
        "providers": probes,
        "failover": failover_report(),
    }


def _probe_tiny_llm(status: dict) -> dict:
    from backend.llm import _redact, complete, failover_report

    try:
        output = complete("Reply with the single word: ok", json_mode=False)
        report = failover_report()
        answering = report["last_successful_provider"] or status["provider"]
        answering_model = (report.get("providers", {}).get(answering) or {}).get("model") or status.get("model")
        return {
            "ok": True,
            "probe": "tiny",
            "provider": answering,
            "model": answering_model,
            "sample_response": (output or "").strip()[:80],
            "failover": report,
            "hint": "A tiny probe can pass while demo-sized calls fail on free-tier quotas; use ?deep=1.",
        }
    except Exception as exc:  # noqa: BLE001 - this endpoint reports a redacted provider failure
        return {
            "ok": False,
            "probe": "tiny",
            "provider": status["provider"],
            "model": status.get("model"),
            "error": _redact(str(exc))[:400],
            "failover": failover_report(),
            "hint": "Every configured provider failed; the deterministic rule-engine floor remains available.",
        }


def _enforce_probe_limit(request: Request, deep: bool, probe_all: bool) -> None:
    if any((deep, probe_all)):
        security.enforce_rate_limit(request, "deep_probe", security.deep_probe_limit())


@router.get("/llm-check", dependencies=_PROTECT_LLMCHECK)
def llm_check(request: Request, deep: bool = False, probe_all: bool = False):
    """Make a real LLM call and report the actual outcome. Unlike /health
    (which only checks a key is present), this surfaces the true reason
    analysis falls back — e.g. out of credit, bad model, bad key — without
    ever returning the key itself.

    Reports the full provider failover chain: the configured providers in the
    order they will be tried (gemini → gateway → claude), which one last
    answered, the last failover reason, and — when no provider is configured —
    that the system is running on the deterministic rule-engine floor.

    `?deep=1` sends the *same reconcile-sized prompt the live demo sends* (a
    tiny probe can pass while demo-sized calls 429 on token-weighted quotas),
    bounded by the analyze timeout, and reports honest mode/latency/findings.
    `?probe_all=1` tests every configured provider individually (uses one call
    per provider — spend sparingly on free tiers)."""
    from backend.llm import failover_report
    status = _llm_status()
    if not status.get("ready"):
        return {"ok": False, "reason": "no_key_configured",
                "on_rule_engine_floor": True, "failover": failover_report(),
                **status}
    # The deep / per-provider probes make real (quota-spending) LLM calls, so
    # they carry their own tight rate limit even when auth is off.
    _enforce_probe_limit(request, deep, probe_all)
    if deep:
        out = _llm_check_deep(status)
        out["failover"] = failover_report()  # after the deep call, so it's live
        return out
    if probe_all:
        return _probe_all_llms()
    return _probe_tiny_llm(status)


def _llm_check_deep(status: dict) -> dict:
    """Reconcile-sized probe: the exact prompt shape /analyze sends, so a
    green result means the demo's LLM path will actually fire."""
    import concurrent.futures
    import time as _time

    from backend.agents.reconciliation import (
        PROMPT_TEMPLATE,
        SYSTEM_PROMPT,
        _all_standards_text,
        _validate_deviations,
    )
    from backend.analyze import _LLM_POOL, _LLM_TIMEOUT_S

    demo = CORPUS.parent / "demo"
    try:
        spec = (demo / "sample_spec.md").read_text(encoding="utf-8")
        submittal = (demo / "sample_submittal.md").read_text(encoding="utf-8")
    except OSError:
        return {"ok": False, "probe": "deep", "reason": "demo_pair_missing",
                **{k: status.get(k) for k in ("provider", "model")}}
    prompt = PROMPT_TEMPLATE.format(
        spec=spec, submittal=submittal,
        standards=_all_standards_text(max_chars_per=1800),
    )
    base = {
        "probe": "deep",
        "provider": status["provider"],
        "model": status.get("model"),
        "prompt_chars": len(prompt),
        "timeout_s": _LLM_TIMEOUT_S,
    }
    t0 = _time.time()
    try:
        from backend.llm import complete_json
        raw = _LLM_POOL.submit(complete_json, prompt, SYSTEM_PROMPT).result(
            timeout=_LLM_TIMEOUT_S)
        devs = _validate_deviations(raw)
        return {"ok": True, **base,
                "elapsed_ms": round((_time.time() - t0) * 1000),
                "findings": len(devs)}
    except concurrent.futures.TimeoutError:
        return {"ok": False, **base,
                "elapsed_ms": round((_time.time() - t0) * 1000),
                "error": f"reconcile-sized call exceeded {_LLM_TIMEOUT_S:.0f}s "
                         "- the demo would fall back to the rule-based engine",
                "hint": "Free-tier congestion; retry, or swap in a fresh key."}
    except Exception as exc:  # noqa: BLE001 — we want the raw reason
        return {"ok": False, **base,
                "elapsed_ms": round((_time.time() - t0) * 1000),
                "error": str(exc)[:400],
                "hint": "The tiny probe may still pass - this failure class "
                        "(usually 429 quota) only shows on demo-sized prompts. "
                        "Swap in a fresh GEMINI_API_KEY and re-check."}
