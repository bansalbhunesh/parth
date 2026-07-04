"""
OCR utility layer — the single place all OCR + PDF-text logic goes through.

Design contract (do not weaken):
- Every function returns a safe empty/false value on ANY missing toolchain or
  runtime error. Nothing here raises for a missing dependency, a missing
  ``tesseract`` binary, or a malformed document — callers convert an empty
  result into an honest HTTP 400 / SSE error, never a 500.
- The only EXTERNAL dependency is the ``tesseract`` system binary (via
  pytesseract). PDF rasterization uses PyMuPDF/fitz — no Poppler, no pdf2image.
- English-only, best-effort. No lang/psm tuning this phase.

Env flags (all optional, safe defaults):
- ``PRAMAAN_OCR`` / ``PRAMAAN_OCR_ENABLED``  — "0" on either disables OCR everywhere.
- ``PRAMAAN_OCR_DPI``          — rasterization DPI for scanned-PDF OCR (default 300).
- ``PRAMAAN_MAX_PDF_PAGES``    — cap on pages OCR'd per PDF (default 30).
- ``PRAMAAN_MAX_IMAGE_PIXELS`` — reject images larger than this (default 20,000,000)
                                 to bound memory / block PIL decompression bombs.
- ``TESSERACT_CMD``            — path to the tesseract binary.
- ``TESSDATA_PREFIX``          — language-data dir (consumed by tesseract itself).
"""

import io
import logging
import os
import re

log = logging.getLogger("pramaan.ocr")

# A PDF whose text layer yields fewer than this many characters is treated as
# scanned / image-only and routed to the OCR fallback.
_OCR_MIN_CHARS = 20

_DEFAULT_OCR_DPI = 300
_DEFAULT_MAX_PDF_PAGES = 30
_DEFAULT_MAX_IMAGE_PIXELS = 20_000_000  # ~20 MP; a 4000x5000 scan is 20 MP

# Raster-image extensions that route to Tesseract OCR (text-reconcile path).
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp")

# Shown whenever text was produced by OCR rather than a native text layer, so a
# reviewer knows to double-check figures. OCR is best-effort, not lossless.
OCR_WARNING = ("Read via OCR — OCR is best-effort and not lossless (e.g. a 5 can "
               "read as an S); verify critical values against the source document.")

# Process-lifetime cache of the tesseract-availability probe, keyed by the
# TESSERACT_CMD env value so a test/deploy that repoints the binary re-probes.
# The binary's presence does not change during a process, so /health can read
# this without shelling out to `tesseract --version` on every request.
_avail_cache: dict[str, bool] = {}


# ── config helpers ──────────────────────────────────────────────────

def ocr_enabled() -> bool:
    """OCR is on unless explicitly disabled via PRAMAAN_OCR=0 (legacy) or
    PRAMAAN_OCR_ENABLED=0 (canonical). Either turns it off everywhere."""
    if os.getenv("PRAMAAN_OCR", "1") == "0":
        return False
    if os.getenv("PRAMAAN_OCR_ENABLED", "1") == "0":
        return False
    return True


def ocr_dpi() -> int:
    try:
        return int(os.getenv("PRAMAAN_OCR_DPI", str(_DEFAULT_OCR_DPI)))
    except ValueError:
        return _DEFAULT_OCR_DPI


def max_pdf_pages() -> int:
    try:
        return int(os.getenv("PRAMAAN_MAX_PDF_PAGES", str(_DEFAULT_MAX_PDF_PAGES)))
    except ValueError:
        return _DEFAULT_MAX_PDF_PAGES


def max_image_pixels() -> int:
    try:
        return int(os.getenv("PRAMAAN_MAX_IMAGE_PIXELS", str(_DEFAULT_MAX_IMAGE_PIXELS)))
    except ValueError:
        return _DEFAULT_MAX_IMAGE_PIXELS


def clean_text(text: str) -> str:
    """Normalize whitespace/newlines (same rules the ingestion path uses)."""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _apply_tesseract_cmd(pytesseract) -> None:
    """Point pytesseract at TESSERACT_CMD, or back at the PATH default when it is
    unset. Setting it in BOTH cases keeps the binary path fully determined by the
    current environment — pytesseract's tesseract_cmd is a module global, so a
    one-way `if cmd:` set would let a stale path leak across calls/requests."""
    cmd = os.getenv("TESSERACT_CMD")
    pytesseract.pytesseract.tesseract_cmd = cmd if cmd else "tesseract"


# ── capability probes ───────────────────────────────────────────────

def get_tesseract_version() -> str | None:
    """The installed tesseract version as a string, or None if pytesseract or
    the binary is unavailable. Live probe (shells out to tesseract)."""
    try:
        import pytesseract
    except ImportError:
        return None
    _apply_tesseract_cmd(pytesseract)
    try:
        return str(pytesseract.get_tesseract_version())
    except Exception:
        return None


def is_tesseract_available() -> bool:
    """True when the tesseract binary can be reached (live probe)."""
    return get_tesseract_version() is not None


def tesseract_available_cached() -> bool:
    """Memoized availability, keyed by TESSERACT_CMD — cheap enough for /health
    to call on every request without spawning a subprocess each time."""
    key = os.getenv("TESSERACT_CMD", "")
    if key not in _avail_cache:
        _avail_cache[key] = is_tesseract_available()
    return _avail_cache[key]


# ── PDF text layer + scanned detection ──────────────────────────────

def extract_text_from_pdf(data: bytes, filename: str = "upload.pdf") -> str:
    """Pull the embedded text layer (pdfplumber, then PyMuPDF). Returns "" for
    scanned/image-only PDFs, which carry no text layer. Raw (uncleaned) text."""
    try:
        import pdfplumber
        text_pages = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_pages.append(t)
        if text_pages:
            return "\n\n".join(text_pages)
    except ImportError:
        pass
    except Exception as exc:
        log.warning("pdfplumber failed for %s: %s, trying PyMuPDF", filename, exc)

    try:
        import fitz
        with fitz.open(stream=data, filetype="pdf") as doc:
            pages = [page.get_text() for page in doc]
        return "\n\n".join(pages)
    except ImportError:
        log.warning("No PDF library available, cannot extract: %s", filename)
        return ""
    except Exception as exc:
        log.warning("PyMuPDF text-layer extraction failed for %s: %s", filename, exc)
        return ""


def is_scanned_pdf(data: bytes, filename: str = "upload.pdf") -> bool:
    """Heuristic: a PDF is treated as scanned when its whole-document text layer
    is shorter than _OCR_MIN_CHARS. This is deliberately crude — a mostly-image
    PDF carrying a few stray characters (headers/form fields) is NOT detected as
    scanned. Per-page image detection is a known limitation, not fixed here."""
    return len(extract_text_from_pdf(data, filename).strip()) < _OCR_MIN_CHARS


# ── OCR: scanned PDF ────────────────────────────────────────────────

def ocr_pdf_bytes(data: bytes, filename: str = "upload.pdf") -> str:
    """OCR fallback for scanned / image-only PDFs — the messy paper-scan-emailed
    submittals EPCs actually deal with.

    Best-effort by design: rasterizes each page with PyMuPDF (no Poppler needed)
    and runs Tesseract via pytesseract. If the OCR toolchain is missing (no
    pytesseract, no tesseract binary, no language data) it returns "" rather than
    raising, so the caller can surface an honest message instead of a 500. OCRs
    at most ``PRAMAAN_MAX_PDF_PAGES`` pages (default 30) to bound latency/memory.

    Disable with PRAMAAN_OCR=0. Point at a tesseract binary with TESSERACT_CMD
    and at language data with TESSDATA_PREFIX. DPI via PRAMAAN_OCR_DPI (default 300).
    """
    if not ocr_enabled():
        return ""
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        log.warning("OCR unavailable (missing %s) for %s", getattr(exc, "name", exc), filename)
        return ""

    _apply_tesseract_cmd(pytesseract)
    dpi = ocr_dpi()
    page_cap = max_pdf_pages()

    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            pages = []
            for i, page in enumerate(doc):
                if i >= page_cap:
                    log.warning("OCR truncated at %d pages for %s (document has %d)",
                                page_cap, filename, doc.page_count)
                    break
                pix = page.get_pixmap(dpi=dpi)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                pages.append(pytesseract.image_to_string(img))
        text = "\n\n".join(pages)
        if text.strip():
            log.info("OCR recovered %d chars from scanned PDF %s", len(text), filename)
        return text
    except Exception as exc:
        log.warning("OCR failed for %s: %s", filename, exc)
        return ""


# ── OCR: raster image (png/jpg/…) ───────────────────────────────────

def extract_text_from_image(data: bytes, mime: str = "image/png") -> str:
    """OCR a directly-uploaded raster image (.png/.jpg/.tiff/…) via Tesseract.

    This is a SEPARATE capability from the Gemini vision path (/analyze/vision):
    that reads values from the picture with a vision LLM; this transcribes the
    image to text with Tesseract for the normal text-reconcile path. Returns ""
    on any failure, a missing toolchain, or an oversize image (pixel cap), never
    raising. The pixel cap (PRAMAAN_MAX_IMAGE_PIXELS, default 20 MP) blocks PIL
    decompression-bomb / OOM inputs before the image is decoded."""
    if not ocr_enabled():
        return ""
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        log.warning("Image OCR unavailable (missing %s)", getattr(exc, "name", exc))
        return ""

    _apply_tesseract_cmd(pytesseract)
    cap = max_image_pixels()
    try:
        img = Image.open(io.BytesIO(data))
        w, h = img.size
        if w * h > cap:
            log.warning("image %dx%d (%d px) exceeds pixel cap %d; skipping OCR",
                        w, h, w * h, cap)
            return ""
        img.load()  # decode now, inside the guard
        return pytesseract.image_to_string(img)
    except Exception as exc:
        log.warning("image OCR failed (%s): %s", mime, exc)
        return ""


# ── orchestrator (text-first, OCR-fallback) ─────────────────────────

def extract_text_with_fallback(data: bytes, filename: str = "upload.pdf") -> str:
    """Text-first PDF extraction with an OCR fallback, preserving today's
    semantics exactly: return the embedded text layer when it has >= _OCR_MIN_CHARS
    characters; otherwise OCR the pages and return the OCR text only if it is
    longer than the text layer. Raw (uncleaned) — the caller normalizes."""
    text = extract_text_from_pdf(data, filename)
    if len(text.strip()) >= _OCR_MIN_CHARS:
        return text
    ocr = ocr_pdf_bytes(data, filename)
    if len(ocr.strip()) > len(text.strip()):
        return ocr
    return text


def _pdf_page_count(data: bytes) -> int:
    try:
        import fitz
        with fitz.open(stream=data, filetype="pdf") as doc:
            return doc.page_count
    except Exception:
        return 0


def _doc_result(text: str, method: str, *, ocr_used: bool = False,
                truncated: bool = False, warning: str | None = None) -> dict:
    return {
        "text": text,
        "method": method,          # text_layer | ocr_pdf | ocr_image | plain_text | none
        "chars": len(text),
        "ocr_used": ocr_used,
        "truncated": truncated,    # OCR stopped at the page cap
        "warning": warning,        # human-readable caveat, or None
    }


def extract_document(data: bytes, filename: str = "upload", content_type: str = "") -> dict:
    """Single entry point for upload extraction: routes PDFs, raster images, and
    plain text to the right path and returns the cleaned text PLUS metadata
    (extraction method, char count, whether OCR was used, whether it was
    truncated at the page cap, and a warning to surface when OCR was used).

    Never raises — an unreadable input returns method="none" with empty text so
    the caller can emit an honest 400 / SSE error rather than a 500."""
    name = filename or "upload"
    lower = name.lower()
    ctype = content_type or ""

    if lower.endswith(".pdf") or ctype == "application/pdf":
        text_layer = extract_text_from_pdf(data, name)
        if len(text_layer.strip()) >= _OCR_MIN_CHARS:
            return _doc_result(clean_text(text_layer), "text_layer")
        ocr = ocr_pdf_bytes(data, name)
        if len(ocr.strip()) > len(text_layer.strip()):
            truncated = _pdf_page_count(data) > max_pdf_pages()
            warning = OCR_WARNING
            if truncated:
                warning += f" Only the first {max_pdf_pages()} pages were OCR'd."
            return _doc_result(clean_text(ocr), "ocr_pdf", ocr_used=True,
                               truncated=truncated, warning=warning)
        cleaned = clean_text(text_layer)
        return _doc_result(cleaned, "text_layer" if cleaned else "none")

    if lower.endswith(IMAGE_EXTS) or ctype.startswith("image/"):
        img = clean_text(extract_text_from_image(data, ctype or "image/png"))
        if img:
            return _doc_result(img, "ocr_image", ocr_used=True, warning=OCR_WARNING)
        return _doc_result("", "none")

    return _doc_result(data.decode("utf-8", errors="replace"), "plain_text")
