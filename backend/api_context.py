from __future__ import annotations

import html
import json
import logging

from fastapi import Depends, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend import case_store, security
from backend.paths import CORPUS
from backend.uploads import validate_upload

log = logging.getLogger("pramaan.api_context")

# Dependency bundles for the expensive / abusable endpoints. Auth is a no-op
# unless DEMO_AUTH_ENABLED + DEMO_AUTH_TOKEN are set; rate limiting is on by
# default with generous per-hour caps (disabled in the test suite via conftest).
_PROTECT_ANALYSIS = [Depends(security.require_demo_auth), Depends(security.rl_analysis)]
_PROTECT_UPLOAD = [Depends(security.require_demo_auth), Depends(security.rl_upload)]
_PROTECT_LLMCHECK = [Depends(security.require_demo_auth)]


VALID_SYSTEMS: set[str] | None = None


def _get_valid_systems() -> set[str]:
    global VALID_SYSTEMS
    if VALID_SYSTEMS is None:
        specs_dir = CORPUS / "specs"
        VALID_SYSTEMS = {p.stem for p in specs_dir.glob("*.md")} if specs_dir.exists() else set()
    return VALID_SYSTEMS



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


def _require_case(case_id: str, request: Request) -> str:
    """Hide case existence unless the caller presents its local/demo secret."""
    secret = request.headers.get("x-case-secret", "")
    if not case_store.verify_case(case_id, secret):
        raise HTTPException(status_code=404, detail="No such case.")
    return secret
