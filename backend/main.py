"""Pramaan API — uvicorn backend.main:app --reload"""

import html
import ipaddress
import json
import logging
import os
import socket
import threading
import time
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

from backend import case_store, security
from backend.agents.ingestion import extract_pdf_bytes, ingest_corpus
from backend.agents.rfi_copilot import ask, ask_fallback, ask_stream, draft_rfi
from backend.analyze import run_analysis, run_streaming_analysis
from backend.orchestrator import run_pipeline
from backend.paths import CORPUS, PROJECTS_DIR
from backend.uploads import validate_upload

# Dependency bundles for the expensive / abusable endpoints. Auth is a no-op
# unless DEMO_AUTH_ENABLED + DEMO_AUTH_TOKEN are set; rate limiting is on by
# default with generous per-hour caps (disabled in the test suite via conftest).
_PROTECT_ANALYSIS = [Depends(security.require_demo_auth), Depends(security.rl_analysis)]
_PROTECT_UPLOAD = [Depends(security.require_demo_auth), Depends(security.rl_upload)]
_PROTECT_LLMCHECK = [Depends(security.require_demo_auth)]

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
# CORS is allowlisted by default. The public frontend and local development
# origins are explicit; deployments can replace them with
# PRAMAAN_CORS_ORIGINS. Credentials remain disabled.
_cors_env = os.getenv("PRAMAAN_CORS_ORIGINS", "").strip()
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()] or [
    "https://parth-tan.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Authorization",
        "Content-Type",
        "X-Case-Secret",
        "X-Demo-Token",
    ],
)


@app.exception_handler(Exception)
async def _never_crash(request, exc):  # noqa: ANN001
    """Last-resort guard: any endpoint that raises an unexpected error returns
    a clean JSON 500 with a stable shape (never a stack trace, never a secret
    leaked into the body) so the live demo can't be broken by one bad path.
    HTTPExceptions still flow through FastAPI's own handler."""
    from fastapi.responses import JSONResponse
    log.error("Unhandled error on %s %s: %s",
              request.method, request.url.path, str(exc)[:300])
    return JSONResponse(status_code=500, content={
        "ok": False,
        "error": "internal_error",
        "detail": "This request failed unexpectedly; the rest of the API is unaffected.",
    })

# Reject oversized request bodies before FastAPI buffers them. An UploadFile
# spools the FULL multipart body to a temp file during request parsing — *before*
# the handler's _read_capped runs — so the 15 MB read cap protects memory but not
# disk. This guard rejects on the declared Content-Length (the realistic
# multi-GB-body DoS vector) with a 413 before any spooling happens. Chunked
# uploads that omit Content-Length fall through to uvicorn's own body limits.
# Implemented as pure ASGI (not @app.middleware/BaseHTTPMiddleware) so it never
# wraps or buffers the SSE StreamingResponses the demo relies on.
# Ceiling = the per-file cap plus 5 MB of multipart/field overhead, so a single
# max-size document (plus a small companion) passes while a multi-GB body is
# rejected before spooling. Read at import from the env cap (PRAMAAN_MAX_UPLOAD_MB).
MAX_REQUEST_BYTES = security.max_upload_bytes() + 5 * 1024 * 1024


class BodySizeLimitMiddleware:
    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            for name, value in scope.get("headers", []):
                if name == b"content-length":
                    try:
                        too_big = int(value) > self.max_bytes
                    except ValueError:
                        await JSONResponse(
                            {"detail": "Invalid Content-Length"}, status_code=400
                        )(scope, receive, send)
                        return
                    if too_big:
                        await JSONResponse(
                            {"detail": f"Request body exceeds the "
                                       f"{self.max_bytes // (1024 * 1024)} MB limit"},
                            status_code=413,
                        )(scope, receive, send)
                        return
                    break
        await self.app(scope, receive, send)


app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_REQUEST_BYTES)


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


def _sse_safe(text) -> str:
    """Strip CR/LF (and truncate) so an attacker-controlled value — e.g. an upload
    filename — can't inject forged SSE events by smuggling newlines into a
    `data:` line (SSE event-splitting)."""
    return str(text).replace("\r", " ").replace("\n", " ")[:200]


def _safe_id(value: str, kind: str) -> str:
    """Reject path traversal in identifiers that get joined onto a filesystem
    path (system_id, project_id). Blocks separators, parent refs and NULs so a
    crafted id cannot escape the corpus / projects directory."""
    if not value or "/" in value or "\\" in value or ".." in value or "\x00" in value:
        raise HTTPException(400, f"Invalid {kind} identifier")
    return value


def _count_requirements() -> int:
    f = CORPUS / "extracted" / "requirements.json"
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            return len(data) if isinstance(data, list) else len(data.get("requirements", []))
        except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
            log.warning("Requirements index unavailable at %s: %s", f, exc)
    return 0


def _sse_response(generator):
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _check_size(data: bytes, name: str):
    cap = security.max_upload_bytes()
    if len(data) > cap:
        raise HTTPException(413, f"{security.safe_name(name)} exceeds the "
                                 f"{security.max_upload_mb()} MB upload limit")


def _read_capped(file: UploadFile, name: str) -> bytes:
    """Read at most the byte cap +1 so an oversized upload is rejected before it
    can be fully buffered into memory (size-after-read DoS). The cap is read
    dynamically (env-configurable via PRAMAAN_MAX_UPLOAD_MB)."""
    data = file.file.read(security.max_upload_bytes() + 1)
    _check_size(data, name)
    return data


def _extraction_meta(doc: dict) -> dict:
    """The extraction metadata (method / ocr_used / truncated / warning / chars)
    WITHOUT the text body — safe to return to the client for transparency."""
    return {k: v for k, v in doc.items() if k != "text"}


def _extract_upload_doc(file: UploadFile) -> dict:
    """Read an upload and extract text WITH metadata (via ocr_util.extract_document).
    Raises an honest 400 when a PDF / image yields no text (scanned + OCR
    unavailable, or an illegible image); plain-text uploads pass through as-is.
    Image OCR here is Tesseract-based and SEPARATE from /analyze/vision (LLM)."""
    from backend.agents import ocr_util
    name = file.filename or "upload"
    data = _read_capped(file, name)
    ctype = file.content_type or ""
    validate_upload(name, ctype, data)  # MIME/ext/magic-byte allowlist
    doc = ocr_util.extract_document(data, name, ctype)
    if doc["text"].strip():
        return doc
    lower = name.lower()
    if lower.endswith(".pdf") or ctype == "application/pdf":
        raise HTTPException(
            400,
            f"Could not read '{name}'. It looks like a scanned / image-only PDF "
            "and OCR is unavailable in this deployment. Upload a text-based PDF, "
            "or paste the document text directly into Live Analysis.",
        )
    if lower.endswith(ocr_util.IMAGE_EXTS) or ctype.startswith("image/"):
        raise HTTPException(
            400,
            f"Could not read text from image '{name}'. OCR is unavailable in this "
            "deployment, or the image carries no legible text. Paste the document "
            "text directly, or use Vision mode (/analyze/vision), which reads "
            "values from the image with an LLM.",
        )
    return doc  # plain text (possibly empty) — unchanged legacy behavior


def _extract_upload_text(file: UploadFile) -> str:
    return _extract_upload_doc(file)["text"]


class WebhookSubscribeRequest(BaseModel):
    url: str


# Process-local, case-scoped integrations. Every mutation requires the owning
# case secret; public analysis cannot subscribe a receiver for another case.
SUBSCRIBED_WEBHOOKS: dict[str, list[dict]] = {}
MAX_WEBHOOKS = 10


def _resolved_webhook_addresses(url: str) -> tuple[str, ...]:
    parsed = urlparse(url)
    if not parsed.hostname:
        return ()
    infos = socket.getaddrinfo(
        parsed.hostname,
        parsed.port or (443 if parsed.scheme == "https" else 80),
        proto=socket.IPPROTO_TCP,
    )
    return tuple(sorted({str(ipaddress.ip_address(info[4][0])) for info in infos}))


def _webhook_url_error(url: str) -> str | None:
    """Validate a subscriber URL; return an error message or None if OK.

    Blocks non-HTTP schemes and hosts that resolve to private/loopback/
    link-local addresses so the public demo can't be driven as an SSRF proxy
    into the backend's network (cloud metadata endpoints, localhost services).
    Set PRAMAAN_WEBHOOK_ALLOW_PRIVATE=1 to demo against a local receiver.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return "URL must be http(s) with a hostname"
    if os.getenv("PRAMAAN_WEBHOOK_ALLOW_PRIVATE", "0") == "1":
        return None
    host = parsed.hostname
    if host == "localhost" or host.endswith((".local", ".internal")):
        return "Private/internal hosts are not allowed"
    try:
        addrs = [ipaddress.ip_address(value) for value in _resolved_webhook_addresses(url)]
    except (OSError, ValueError):
        return "Hostname does not resolve"
    if any(a.is_private or a.is_loopback or a.is_link_local or a.is_unspecified for a in addrs):
        return "Private/internal addresses are not allowed"
    return None


def _redact_webhook(url: str) -> str:
    """Subscriber URLs can embed secrets (Slack webhook tokens): show enough
    to recognize the subscription, never enough to replay it."""
    return url if len(url) <= 40 else url[:40] + "…"


def _deliver_webhooks(subscriptions: list[dict], payload: dict, slack_payload: dict) -> None:
    """POST to every subscriber (runs on a worker thread). One dead subscriber
    must never block delivery to the rest."""
    import httpx
    for subscription in subscriptions:
        url = str(subscription.get("url", ""))
        body = slack_payload if "hooks.slack.com" in url else payload
        try:
            if _webhook_url_error(url):
                continue
            pinned = tuple(subscription.get("resolved_ips", ()))
            if not pinned or _resolved_webhook_addresses(url) != pinned:
                log.warning("Webhook destination DNS changed; delivery dropped")
                continue
            httpx.post(url, json=body, timeout=2.0, follow_redirects=False)
        except Exception as exc:
            log.warning(
                "Webhook delivery failed for %s: %s",
                _redact_webhook(url),
                exc,
            )


def trigger_webhooks(
    deviations: list[dict], system_id: str, case_id: str | None = None,
) -> None:
    """Fan out Critical/Major findings to one owned case. Fire-and-forget: the
    payload is built defensively (LLM-produced dicts may miss keys) and
    delivery happens on a daemon thread, so a malformed deviation or a slow
    subscriber can never fail or delay an analysis response."""
    if not case_id:
        return
    try:
        subscriptions = SUBSCRIBED_WEBHOOKS.get(case_id, [])
        critical_or_major = [d for d in deviations if d.get("severity") in ("Critical", "Major")]
        if not critical_or_major or not subscriptions:
            return

        payload = {
            "event": "deviation_detected",
            "case_id": case_id,
            "system": system_id,
            "count": len(critical_or_major),
            "deviations": critical_or_major,
            "rfi_drafts": [
                f"DEVIATION RFI: Component {d.get('component', '?')} fails {d.get('parameter', '?')}. "
                f"Required: {d.get('required_value', '?')} {d.get('unit', '')}, "
                f"Provided: {d.get('provided_value', '?')} {d.get('unit', '')}. "
                f"Please clarify non-compliance."
                for d in critical_or_major
            ],
        }

        slack_text = (
            f"🚨 *Pramaan Alert*: {len(critical_or_major)} Critical/Major deviations "
            f"found in system {system_id}!\n"
            + "\n".join([
                f"• *{d.get('component', '?')}* ({d.get('parameter', '?')}): "
                f"Required {d.get('required_value', '?')} {d.get('unit', '')}, "
                f"got {d.get('provided_value', '?')} {d.get('unit', '')}."
                for d in critical_or_major
            ])
        )
        slack_payload = {"text": slack_text}

        threading.Thread(
            target=_deliver_webhooks,
            args=(list(subscriptions), payload, slack_payload),
            daemon=True,
        ).start()
    except Exception as exc:
        log.warning("Case webhook dispatch could not start for %s: %s", case_id, exc)


@app.post("/webhooks/subscribe")
def subscribe_webhook(req: WebhookSubscribeRequest):
    del req
    raise HTTPException(
        status_code=410,
        detail="Global webhooks were retired. Configure integrations inside an owned case.",
    )


@app.get("/webhooks")
def get_webhooks():
    raise HTTPException(
        status_code=410,
        detail="Global webhooks were retired. Use /cases/{case_id}/webhooks.",
    )


@app.delete("/webhooks")
def clear_webhooks():
    """Retired global mutation endpoint retained as an explicit 410."""
    raise HTTPException(
        status_code=410,
        detail="Global webhooks were retired. Use /cases/{case_id}/webhooks.",
    )


@app.post("/cases/{case_id}/webhooks")
def subscribe_case_webhook(
    case_id: str, req: WebhookSubscribeRequest, request: Request,
):
    secret = _require_case(case_id, request)
    url = req.url.strip()
    err = _webhook_url_error(url)
    if err:
        raise HTTPException(status_code=400, detail=err)
    try:
        resolved_ips = _resolved_webhook_addresses(url)
    except (OSError, ValueError):
        raise HTTPException(status_code=400, detail="Hostname does not resolve") from None

    subscriptions = SUBSCRIBED_WEBHOOKS.setdefault(case_id, [])
    if not any(item["url"] == url for item in subscriptions):
        if len(subscriptions) >= MAX_WEBHOOKS:
            raise HTTPException(
                status_code=429,
                detail=f"Integration limit ({MAX_WEBHOOKS}) reached for this case",
            )
        subscriptions.append({"url": url, "resolved_ips": resolved_ips})
        case_store.append_audit(
            case_id,
            case_store.actor_key_for(secret),
            "webhook_subscribed",
            detail=urlparse(url).hostname or "",
        )
    return {"status": "subscribed", "url": _redact_webhook(url)}


@app.get("/cases/{case_id}/webhooks")
def get_case_webhooks(case_id: str, request: Request):
    _require_case(case_id, request)
    subscriptions = SUBSCRIBED_WEBHOOKS.get(case_id, [])
    return {
        "count": len(subscriptions),
        "urls": [_redact_webhook(str(item["url"])) for item in subscriptions],
    }


@app.delete("/cases/{case_id}/webhooks")
def clear_case_webhooks(case_id: str, request: Request):
    secret = _require_case(case_id, request)
    cleared = len(SUBSCRIBED_WEBHOOKS.pop(case_id, []))
    case_store.append_audit(
        case_id,
        case_store.actor_key_for(secret),
        "webhooks_cleared",
        detail=str(cleared),
    )
    return {"cleared": cleared}


# ── Analysis endpoints ──────────────────────────────────────────────

@app.post("/analyze", dependencies=_PROTECT_ANALYSIS)
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

@app.post("/jobs/analyze", status_code=202, dependencies=_PROTECT_ANALYSIS)
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


@app.get("/jobs/{job_id}", dependencies=[Depends(security.require_demo_auth)])
def get_job(job_id: str):
    """Lightweight status metadata for a job (no result body) — poll this."""
    from backend import jobs
    if not jobs.valid_job_id(job_id):
        raise HTTPException(404, "Unknown or expired job id.")
    st = jobs.job_status(job_id)
    if st is None:
        raise HTTPException(404, "Unknown or expired job id.")
    return st


@app.get("/jobs/{job_id}/result", dependencies=[Depends(security.require_demo_auth)])
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


@app.post("/analyze/stream", dependencies=_PROTECT_ANALYSIS)
def analyze_stream(req: AnalyzeRequest):
    def generate():
        yield "event: status\ndata: Loading standards knowledge base...\n\n"
        yield from run_streaming_analysis(req.spec_text, req.submittal_text, req.system_id)

    return _sse_response(generate())


@app.post("/analyze/upload", dependencies=_PROTECT_UPLOAD)
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


@app.post("/analyze/vision", dependencies=_PROTECT_UPLOAD)
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


@app.post("/analyze/upload/stream", dependencies=_PROTECT_UPLOAD)
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


@app.get("/health")
def health():
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


@app.get("/ocr-check")
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


@app.get("/llm-check", dependencies=_PROTECT_LLMCHECK)
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
    from backend.llm import failover_report, probe_provider
    status = _llm_status()
    if not status.get("ready"):
        return {"ok": False, "reason": "no_key_configured",
                "on_rule_engine_floor": True, "failover": failover_report(),
                **status}
    # The deep / per-provider probes make real (quota-spending) LLM calls, so
    # they carry their own tight rate limit even when auth is off.
    if deep or probe_all:
        security.enforce_rate_limit(request, "deep_probe", security.deep_probe_limit())
    if deep:
        out = _llm_check_deep(status)
        out["failover"] = failover_report()  # after the deep call, so it's live
        return out
    if probe_all:
        probes = [probe_provider(p) for p in failover_report()["chain"]]
        return {"ok": any(p["ok"] for p in probes), "probe": "per-provider",
                "providers": probes, "failover": failover_report()}
    try:
        from backend.llm import complete
        out = complete("Reply with the single word: ok", json_mode=False)
        report = failover_report()  # regenerate so last_successful is this call
        answering = report["last_successful_provider"] or status["provider"]
        # Report the ANSWERING leg's configured model — when a failover leg
        # serves the probe, pairing its provider with the primary's model
        # reads as a contradiction to anyone auditing this JSON.
        answering_model = (report.get("providers", {}).get(answering) or {}).get(
            "model") or status.get("model")
        return {
            "ok": True,
            "probe": "tiny",
            "provider": answering,
            "model": answering_model,
            "sample_response": (out or "").strip()[:80],
            "failover": report,
            "hint": "A tiny probe can pass while demo-sized calls fail on "
                    "free-tier quotas - pre-flight with /llm-check?deep=1.",
        }
    except Exception as exc:  # noqa: BLE001 — we want the raw reason
        from backend.llm import _redact
        return {
            "ok": False,
            "probe": "tiny",
            "provider": status["provider"],
            "model": status.get("model"),
            "error": _redact(str(exc))[:400],
            "failover": failover_report(),
            "hint": "Every configured provider failed. Common causes: all keys "
                    "out of quota/credit, wrong OPENAI_MODEL, or revoked keys. "
                    "The app still serves the deterministic rule-engine floor.",
        }


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


def _corpus_texts(system_id: str) -> tuple[str | None, str | None]:
    """Load the corpus spec + submittal markdown for a system, or (None, None)
    if either is missing. Used to run the INDEPENDENT rule-based detector when
    the LLM pipeline returns empty — never the seeded answer key."""
    spec_p = CORPUS / "specs" / f"{system_id}.md"
    sub_p = CORPUS / "submittals" / f"{system_id}.md"
    if spec_p.exists() and sub_p.exists():
        return spec_p.read_text(encoding="utf-8"), sub_p.read_text(encoding="utf-8")
    return None, None


@app.post("/ingest/{system_id}")
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


@app.get("/deviations")
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

@app.post("/copilot", dependencies=_PROTECT_ANALYSIS)
def copilot(q: CopilotQuery):
    try:
        return ask(q.query)
    except Exception as exc:
        log.warning("Copilot LLM failed, using fallback: %s", exc)
        devs = _load_json("ground_truth.json").get("seeded_deviations", [])
        return ask_fallback(q.query, devs)


@app.post("/copilot/stream", dependencies=_PROTECT_ANALYSIS)
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


# ── Export endpoints ─────────────────────────────────────────────────

@app.get("/export/audit")
def export_audit():
    reg_data = deviations()
    reg = reg_data["register"]
    gt = _load_json("ground_truth.json")
    project_info = gt.get("project", {})

    pack = {
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
    # Integrity block: SHA-256 over the pack's canonical JSON (sorted keys,
    # no whitespace), computed BEFORE this block is attached. Any edit to an
    # exported record is detectable by re-hashing — the property an NCR
    # register needs from an audit trail. Detectable-after-the-fact, not
    # tamper-PROOF: the hash travels with the document.
    import hashlib
    canonical = json.dumps(pack, sort_keys=True, separators=(",", ":"),
                           default=str)
    pack["integrity"] = {
        "algo": "sha256",
        "content_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "how_to_verify": "remove the 'integrity' key, re-serialise with "
                         "sort_keys=True and separators=(',',':'), sha256 the "
                         "UTF-8 bytes, compare to content_hash",
    }
    return pack


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
          <span class="bar-label">{_esc(d.get('component',''))}</span>
          <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{sev_color}"></div></div>
          <span class="bar-val">{lt}w</span>
        </div>"""

    proj_e, tier_e = _esc(data['project']), _esc(data['tier'])
    loc_e, week_e = _esc(data['location']), _esc(data['generated_week'])
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Pramaan Compliance Evidence Pack — {_esc(data['project'])}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
body {{ font-family: 'Sora', -apple-system, system-ui, sans-serif; margin: 0; background: #fafbfc; color: #1a1a2e; }}
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
  <p>{proj_e} &middot; {tier_e} &middot; {loc_e} &middot; Week {week_e}</p>
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
    <h3>Lead-Time Window</h3>
    <div class="val total">{total_lead}w</div>
  </div>
</div>

<h2>Lead Time by Deviation</h2>
<div class="bar-chart">{bar_html}</div>

<h2>Standards Basis</h2>
<div class="standards">{''.join(f'<div class="std">{_esc(s)}</div>' for s in data['standard_basis'])}</div>

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
  Combined lead-time window: <b>{total_lead} weeks</b> across all findings (scenario figure, not a measured saving).<br>
  Evidence-pack integrity (SHA-256 of the JSON export at <code>/export/audit</code>):
  <code>{_esc(data.get('integrity', {}).get('content_hash', ''))}</code>
  — re-hash to detect any post-export edit.
</div>
</body></html>"""


# ── Cases: persisted, tenant-isolated submittal -> RFI workflow ──────
#
# Everything above this point is either in-memory (jobs.py's result cache)
# or static/read-only (the /projects/{project_id}/* demo fixtures). This is
# the one workflow the project chose to deepen with real persistence instead
# of adding more surface area — see backend/case_store.py's module docstring
# for the honest scope (SQLite, single-instance, tenant-isolated by a
# per-case bearer secret, not real user accounts).

class CreateCaseRequest(BaseModel):
    name: str = Field(default="", max_length=200)


class AddFindingRequest(BaseModel):
    component: str = Field(default="", max_length=200)
    parameter: str = Field(default="", max_length=200)
    required_value: str = Field(default="", max_length=500)
    provided_value: str = Field(default="", max_length=500)
    unit: str = Field(default="", max_length=50)
    severity: str = Field(default="", max_length=50)
    standard_ref: str = Field(default="", max_length=200)
    spec_clause: str = Field(default="", max_length=200)
    predicted_cx_test: str = Field(default="", max_length=200)
    lead_time_weeks: float | None = None
    rationale: str = Field(default="", max_length=2000)


class UpdateFindingRequest(BaseModel):
    status: str | None = Field(default=None, max_length=30)
    owner: str | None = Field(default=None, max_length=120)
    resolution_note: str | None = Field(default=None, max_length=2000)


class UpdateRfiRequest(BaseModel):
    status: str = Field(max_length=30)
    response_text: str | None = Field(default=None, max_length=4000)


_FINDING_TRANSITIONS = {
    "open": {"accepted", "rfi_drafted", "dismissed"},
    "accepted": {"open", "rfi_drafted", "resolved", "dismissed"},
    "rfi_drafted": {"accepted", "resolved"},
    "resolved": {"open"},
    "dismissed": {"open"},
}
_RFI_TRANSITIONS = {
    "draft": {"issued"},
    "issued": {"answered"},
    "answered": {"closed"},
    "closed": set(),
}


def _require_case(case_id: str, request: Request) -> str:
    """Tenant-isolation gate for every /cases/{case_id}/* route. A wrong or
    missing X-Case-Secret returns 404, identical to a nonexistent case_id —
    this deliberately does not distinguish "case doesn't exist" from "wrong
    secret" so a caller can't probe for valid case IDs. Returns the presented
    secret (needed by the caller to compute the audit actor_key)."""
    secret = request.headers.get("x-case-secret", "")
    if not case_store.verify_case(case_id, secret):
        raise HTTPException(status_code=404, detail="No such case.")
    return secret


@app.post("/cases", dependencies=[Depends(security.rl_case_create)])
def create_case(req: CreateCaseRequest):
    """Create a new case. The returned `secret` is shown exactly once — it
    is the only credential for every /cases/{case_id}/* route on this case
    and cannot be recovered if lost, the same way a demo token can't be."""
    case_id, secret = case_store.create_case(req.name)
    return {"case_id": case_id, "secret": secret,
            "warning": "This secret is shown once and cannot be recovered. "
                       "Store it now — it is required for every request "
                       "against this case."}


@app.get("/cases/{case_id}")
def get_case(case_id: str, request: Request):
    _require_case(case_id, request)
    summary = case_store.case_summary(case_id)
    return {
        **summary,
        "findings_count": len(case_store.list_findings(case_id)),
        "rfis_count": len(case_store.list_rfis(case_id)),
    }


@app.post("/cases/{case_id}/findings")
def add_case_finding(case_id: str, req: AddFindingRequest, request: Request):
    secret = _require_case(case_id, request)
    finding = req.model_dump()
    finding_id = case_store.add_finding(case_id, finding)
    case_store.append_audit(case_id, case_store.actor_key_for(secret),
                            "finding_added", detail=f"{req.component}.{req.parameter}")
    trigger_webhooks(
        [finding],
        (req.component.split("-", 1)[0] or "CUSTOM"),
        case_id=case_id,
    )
    return {"finding_id": finding_id}


@app.get("/cases/{case_id}/findings")
def list_case_findings(case_id: str, request: Request):
    _require_case(case_id, request)
    return {"findings": case_store.list_findings(case_id)}


@app.patch("/cases/{case_id}/findings/{finding_id}")
def update_case_finding(case_id: str, finding_id: str,
                        req: UpdateFindingRequest, request: Request):
    secret = _require_case(case_id, request)
    finding = case_store.get_finding(case_id, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="No such finding on this case.")
    if req.status is None and req.owner is None and req.resolution_note is None:
        raise HTTPException(status_code=422, detail="Provide a workflow field to update.")

    next_status = req.status or finding["status"]
    if next_status not in _FINDING_TRANSITIONS:
        raise HTTPException(status_code=422, detail="Unknown finding status.")
    current_status = finding["status"]
    if (
        next_status != current_status
        and next_status not in _FINDING_TRANSITIONS[current_status]
    ):
        raise HTTPException(
            status_code=409,
            detail=f"Finding cannot move from {current_status} to {next_status}.",
        )

    next_owner = (req.owner if req.owner is not None else finding["owner"]).strip()
    next_note = (
        req.resolution_note
        if req.resolution_note is not None
        else finding["resolution_note"]
    ).strip()
    if next_status in {"accepted", "rfi_drafted", "resolved"} and not next_owner:
        raise HTTPException(
            status_code=422,
            detail="Assign an owner before accepting or progressing a finding.",
        )
    if next_status in {"resolved", "dismissed"} and not next_note:
        raise HTTPException(
            status_code=422,
            detail="Record resolution evidence before closing a finding.",
        )
    if next_status == "resolved" and current_status == "rfi_drafted":
        related_rfis = [
            rfi
            for rfi in case_store.list_rfis(case_id)
            if rfi["finding_id"] == finding_id
        ]
        if not related_rfis or related_rfis[-1]["status"] not in {"answered", "closed"}:
            raise HTTPException(
                status_code=409,
                detail="Record the RFI response before resolving this finding.",
            )

    updated = case_store.update_finding(
        case_id,
        finding_id,
        status=next_status,
        owner=next_owner,
        resolution_note=next_note,
    )
    changes = []
    if next_status != current_status:
        changes.append(f"status={current_status}->{next_status}")
    if next_owner != finding["owner"]:
        changes.append(f"owner={next_owner or 'unassigned'}")
    if next_note != finding["resolution_note"]:
        changes.append("resolution_evidence=updated")
    case_store.append_audit(
        case_id,
        case_store.actor_key_for(secret),
        "finding_workflow_updated",
        detail=f"finding={finding_id} {' '.join(changes)}",
    )
    return {"finding": updated}


@app.post("/cases/{case_id}/findings/{finding_id}/rfi", dependencies=[Depends(security.rl_analysis)])
def draft_case_rfi(case_id: str, finding_id: str, request: Request):
    secret = _require_case(case_id, request)
    finding = case_store.get_finding(case_id, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="No such finding on this case.")
    if finding["status"] in {"resolved", "dismissed"}:
        raise HTTPException(
            status_code=409,
            detail="Reopen the finding before drafting an RFI.",
        )
    if not finding["owner"]:
        raise HTTPException(
            status_code=422,
            detail="Assign an owner before drafting an RFI.",
        )
    active_rfi = next(
        (
            rfi
            for rfi in case_store.list_rfis(case_id)
            if rfi["finding_id"] == finding_id and rfi["status"] != "closed"
        ),
        None,
    )
    if active_rfi is not None:
        raise HTTPException(
            status_code=409,
            detail="This finding already has an active RFI.",
        )
    draft = draft_rfi(finding)
    rfi_id = case_store.add_rfi(case_id, finding_id, draft["question"],
                                draft["drafted_text"], draft["sources"], draft["mode"])
    case_store.append_audit(case_id, case_store.actor_key_for(secret),
                            "rfi_drafted", detail=f"finding={finding_id} mode={draft['mode']}")
    if finding["status"] != "rfi_drafted":
        case_store.update_finding(case_id, finding_id, status="rfi_drafted")
    return {"rfi_id": rfi_id, **draft}


@app.get("/cases/{case_id}/rfis")
def list_case_rfis(case_id: str, request: Request):
    _require_case(case_id, request)
    return {"rfis": case_store.list_rfis(case_id)}


@app.patch("/cases/{case_id}/rfis/{rfi_id}")
def update_case_rfi(case_id: str, rfi_id: str, req: UpdateRfiRequest,
                    request: Request):
    secret = _require_case(case_id, request)
    rfi = case_store.get_rfi(case_id, rfi_id)
    if rfi is None:
        raise HTTPException(status_code=404, detail="No such RFI on this case.")
    next_status = req.status.strip().lower()
    if next_status not in _RFI_TRANSITIONS:
        raise HTTPException(status_code=422, detail="Unknown RFI status.")
    current_status = rfi["status"]
    if next_status != current_status and next_status not in _RFI_TRANSITIONS[current_status]:
        raise HTTPException(
            status_code=409,
            detail=f"RFI cannot move from {current_status} to {next_status}.",
        )
    next_response = (
        req.response_text
        if req.response_text is not None
        else rfi["response_text"]
    ).strip()
    if next_status in {"answered", "closed"} and not next_response:
        raise HTTPException(
            status_code=422,
            detail="Record the formal response before answering or closing an RFI.",
        )
    updated = case_store.update_rfi(
        case_id, rfi_id, status=next_status, response_text=next_response
    )
    if next_status != current_status or next_response != rfi["response_text"]:
        case_store.append_audit(
            case_id,
            case_store.actor_key_for(secret),
            "rfi_workflow_updated",
            detail=f"rfi={rfi_id} status={current_status}->{next_status}",
        )
    return {"rfi": updated}


@app.get("/cases/{case_id}/rfis/{rfi_id}/export", response_class=HTMLResponse)
def export_case_rfi(case_id: str, rfi_id: str, request: Request):
    secret = _require_case(case_id, request)
    rfi = case_store.get_rfi(case_id, rfi_id)
    if rfi is None:
        raise HTTPException(status_code=404, detail="No such RFI on this case.")
    finding = case_store.get_finding(case_id, rfi["finding_id"]) or {}
    case = case_store.case_summary(case_id) or {}
    case_store.append_audit(case_id, case_store.actor_key_for(secret),
                            "rfi_exported", detail=rfi_id)
    sources_html = "".join(f"<li>{_esc(s)}</li>" for s in rfi.get("sources", []))
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>RFI Export — {_esc(case.get('name') or case_id)}</title>
<style>
body {{ font-family: -apple-system, system-ui, sans-serif; margin: 0; background: #fafbfc; color: #1a1a2e; }}
.header {{ background: #0c0f13; color: #e7ecf3; padding: 32px 40px; }}
.header h1 {{ font-size: 22px; margin: 0 0 6px; }}
.header p {{ color: #7a8899; font-size: 13px; margin: 0; }}
.content {{ max-width: 800px; margin: 0 auto; padding: 32px 40px; }}
.finding {{ background: #f0f2f5; border-radius: 8px; padding: 16px 20px; margin-bottom: 24px; font-size: 13px; }}
.drafted {{ white-space: pre-wrap; line-height: 1.6; font-size: 14px; }}
h2 {{ font-size: 14px; text-transform: uppercase; letter-spacing: 0.04em; color: #555; }}
</style></head>
<body>
<div class="header">
  <h1>RFI Export</h1>
  <p>Case: {_esc(case.get('name') or case_id)} · RFI {_esc(rfi_id)} · Mode: {_esc(rfi.get('mode', ''))}</p>
</div>
<div class="content">
  <h2>Finding</h2>
  <div class="finding">
    <b>{_esc(finding.get('component', ''))}</b> — {_esc(finding.get('parameter', '').replace('_', ' '))}<br>
    Required: {_esc(finding.get('required_value', ''))} {_esc(finding.get('unit', ''))} ·
    Submitted: {_esc(finding.get('provided_value', ''))} {_esc(finding.get('unit', ''))} ·
    Severity: {_esc(finding.get('severity', ''))}<br>
    Standard: {_esc(finding.get('standard_ref', ''))} {_esc(finding.get('spec_clause', ''))}
  </div>
  <h2>Drafted RFI</h2>
  <div class="drafted">{_esc(rfi.get('drafted_text', ''))}</div>
  <h2>Cited Sources</h2>
  <ul>{sources_html or '<li>none</li>'}</ul>
</div>
</body></html>"""


@app.get("/cases/{case_id}/export/itp.pdf")
def export_case_itp_pdf(case_id: str, request: Request):
    """A physically-signable Inspection & Test Plan, distinct from the
    JSON/HTML exports — a commissioning authority can print and hand this
    off rather than work from a screen. Built from the case's own findings
    against the same commissioning-test catalog `backend/agents/commissioning.py`
    uses; adds no new AI reasoning, just a different export format."""
    secret = _require_case(case_id, request)
    case = case_store.case_summary(case_id) or {}
    findings = case_store.list_findings(case_id)
    from backend.agents.itp_export import build_itp_pdf
    pdf_bytes = build_itp_pdf(case, findings)
    case_store.append_audit(case_id, case_store.actor_key_for(secret),
                            "itp_pdf_exported", detail=f"{len(findings)} findings")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="itp_{case_id[:8]}.pdf"'},
    )


@app.get("/cases/{case_id}/audit-log")
def get_case_audit_log(case_id: str, request: Request):
    _require_case(case_id, request)
    return {"audit_log": case_store.get_audit_log(case_id)}


@app.delete("/cases/{case_id}", status_code=200)
def delete_case_endpoint(case_id: str, request: Request):
    """Permanently delete a case and all its findings, RFIs, and audit log.

    Requires the X-Case-Secret header. Returns 404 for wrong/missing secret
    (indistinguishable from a nonexistent case).
    """
    _require_case(case_id, request)
    SUBSCRIBED_WEBHOOKS.pop(case_id, None)
    case_store.delete_case(case_id)
    return {"deleted": True, "case_id": case_id}


# ── Pipeline info endpoint ───────────────────────────────────────────

@app.get("/pipeline")
def pipeline_info():
    return {
        "name": "Pramaan Compliance Reasoning Graph (with bounded retrieval + critique cycles)",
        "framework": "LangGraph",
        "llm_footprint": "single LLM reasoning core at node_reconcile; other nodes are deterministic-first",
        "nodes": [
            {"id": "ingest", "node": "Ingestion", "kind": "deterministic",
             "description": "Document intake, parsing, normalization"},
            {"id": "load_standards", "node": "Standards Loader", "kind": "deterministic",
             "description": "Load governing standards corpus"},
            {"id": "validate", "node": "Validation Gate", "kind": "deterministic",
             "description": "Check spec+submittal exist; conditional routing"},
            {"id": "reconcile", "node": "Reconciliation", "kind": "llm_core",
             "description": "Cross-document deviation reasoning"},
            {"id": "retrieve", "node": "Standards Retrieval Tool", "kind": "deterministic",
             "description": "Fetches a cited standard absent from context; loops back to reconcile (tool-call cycle)"},
            {"id": "critique", "node": "Self-Critique Gate", "kind": "deterministic_by_default",
             "description": "Verifies its own findings; loops back to reconcile on a failed self-check (reflexion)"},
            {"id": "cx_predict", "node": "Cx Predictor", "kind": "rule_graph_first",
             "description": "Map deviations to commissioning tests"},
            {"id": "format_output", "node": "Output Formatter", "kind": "deterministic",
             "description": "Enrich and structure findings"},
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
        "services": [
            {"id": "extraction", "service": "Extraction service", "description": "Raw document to structured triples"},
            {"id": "rfi_copilot", "service": "RFI Copilot",
             "description": "RAG over project corpus with prior-RFI matching"},
        ],
    }


@app.get("/corpus/doc/{doc_type}/{system_id}")
def corpus_doc(doc_type: str, system_id: str):
    if doc_type not in ("specs", "submittals"):
        raise HTTPException(400, "doc_type must be 'specs' or 'submittals'")
    system_id = _safe_id(system_id, "system_id")
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
        "total_systems": result.get("total_systems", len(result.get("systems", []))),
        "total_standards": result.get("total_standards", len(result.get("standards", []))),
        "total_documents": result.get("total_documents", 0),
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
    project_id = _safe_id(project_id, "project_id")
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


# ── PS4 capability layers: schedule risk · supply chain · unified graph ──────
# Each is gated by an env flag (default on) and returns {"available": false}
# instead of 404/500 when its data file or flag is absent, so the existing 19
# sections and the 315-test baseline are never affected.

# Per-project memo cache for the PS4 layers. The analysis is a pure function of
# static on-disk JSON that never changes during a demo, so the first hit pays the
# Monte-Carlo cost (~1-2s on a free-tier box) and every subsequent hit is instant —
# and immune to concurrent-judge-click stalls.
_PS4_CACHE: dict = {}


def _project_dir(project_id: str):
    project_id = _safe_id(project_id, "project_id")
    return CORPUS if project_id == "meghdoot" else PROJECTS_DIR / project_id


def _load_project_file(project_id: str, name: str):
    p = _project_dir(project_id) / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


@app.get("/projects/{project_id}/schedule")
def project_schedule(project_id: str):
    if os.getenv("PRAMAAN_SCHEDULE", "1") == "0":
        return {"available": False}
    cache_key = ("schedule", project_id)
    if cache_key in _PS4_CACHE:
        return _PS4_CACHE[cache_key]
    try:
        sch = _load_project_file(project_id, "schedule.json")
        if not sch:
            return {"available": False}
        from backend.agents import schedule_risk
        gt = _load_project_file(project_id, "ground_truth.json") or {}
        sch = {**sch, "risks": schedule_risk.derive_risks(sch, gt.get("seeded_deviations", []))}
        analysis = schedule_risk.analyze_schedule(sch, n=5000, seed=42)
        analysis["available"] = True
        analysis["narrative"] = schedule_risk.narrate(analysis)
        _PS4_CACHE[cache_key] = analysis
        return analysis
    except Exception as exc:
        log.warning("Schedule analysis failed for %s: %s", project_id, exc)
        return {"available": False, "error": str(exc)}


@app.get("/projects/{project_id}/supply-chain")
def project_supply_chain(project_id: str):
    if os.getenv("PRAMAAN_SUPPLY", "1") == "0":
        return {"available": False}
    try:
        sup = _load_project_file(project_id, "supply_chain.json")
        if not sup:
            return {"available": False}
        from backend.agents import supply_chain
        analysis = supply_chain.analyze_supply_chain(sup)
        analysis["available"] = True
        analysis["narrative"] = supply_chain.narrate(analysis)
        return analysis
    except Exception as exc:
        log.warning("Supply-chain analysis failed for %s: %s", project_id, exc)
        return {"available": False, "error": str(exc)}


def _assemble_project_graph(project_id: str):
    from backend.agents import project_graph
    gt = _load_project_file(project_id, "ground_truth.json")
    if not gt:
        return None, None
    g = project_graph.assemble(
        gt.get("seeded_deviations", []),
        cx_plan=_load_project_file(project_id, "commissioning/cx_plan.json"),
        supply_chain=_load_project_file(project_id, "supply_chain.json"),
        schedule=_load_project_file(project_id, "schedule.json"),
    )
    return project_graph, g


@app.get("/projects/{project_id}/graph")
def project_graph_view(project_id: str):
    if os.getenv("PRAMAAN_GRAPH", "1") == "0":
        return {"available": False}
    try:
        pg, g = _assemble_project_graph(project_id)
        if g is None:
            return {"available": False}
        return {"available": True, "stats": pg.graph_stats(g), "graph": pg.as_graph(g)}
    except Exception as exc:
        log.warning("Project graph failed for %s: %s", project_id, exc)
        return {"available": False, "error": str(exc)}


@app.get("/projects/{project_id}/blast-radius/{dev_id}")
def project_blast_radius(project_id: str, dev_id: str):
    if os.getenv("PRAMAAN_GRAPH", "1") == "0":
        return {"available": False}
    try:
        dev_id = _safe_id(dev_id, "dev_id")
        pg, g = _assemble_project_graph(project_id)
        if g is None:
            return {"available": False}
        br = pg.blast_radius(g, dev_id)
        if br is None:
            return {"available": False}
        return {"available": True, **br}
    except Exception as exc:
        log.warning("Blast radius failed for %s/%s: %s", project_id, dev_id, exc)
        return {"available": False, "error": str(exc)}


@app.get("/projects/{project_id}/remediation/{dev_id}")
def project_remediation(project_id: str, dev_id: str, cost_per_week_lakh: float = 200.0):
    """What-if remediation simulator: how the schedule slip (and cost) of a
    deviation changes with the week it is caught — flat-zero until the cliff,
    then climbing one-for-one. Deterministic; the LLM never touches it."""
    if os.getenv("PRAMAAN_GRAPH", "1") == "0":
        return {"available": False}
    try:
        dev_id = _safe_id(dev_id, "dev_id")
        pg, g = _assemble_project_graph(project_id)
        if g is None:
            return {"available": False}
        sim = pg.simulate_remediation(g, dev_id, cost_per_week_lakh=cost_per_week_lakh)
        if sim is None:
            return {"available": False}
        return {"available": True, **sim}
    except Exception as exc:
        log.warning("Remediation sim failed for %s/%s: %s", project_id, dev_id, exc)
        return {"available": False, "error": str(exc)}


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
