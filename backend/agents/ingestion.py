"""
Ingestion Agent — document intake, parsing, and normalization.
"""

import hashlib
import io
import logging
import os
import pathlib
import re
from typing import Optional

from backend.paths import CORPUS

log = logging.getLogger("pramaan.ingestion")

# A PDF whose text layer yields fewer than this many characters is treated as
# scanned / image-only and routed to the OCR fallback.
_OCR_MIN_CHARS = 20


def _clean_text(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _pdf_text_layer(data: bytes, filename: str) -> str:
    """Pull the embedded text layer (pdfplumber, then PyMuPDF). Returns "" for
    scanned/image-only PDFs, which carry no text layer."""
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
        doc = fitz.open(stream=data, filetype="pdf")
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n\n".join(pages)
    except ImportError:
        log.warning("No PDF library available, cannot extract: %s", filename)
        return ""
    except Exception as exc:
        log.warning("PyMuPDF text-layer extraction failed for %s: %s", filename, exc)
        return ""


def _ocr_pdf_bytes(data: bytes, filename: str) -> str:
    """OCR fallback for scanned / image-only PDFs — the messy paper-scan-emailed
    submittals EPCs actually deal with.

    Best-effort by design: rasterizes each page with PyMuPDF (no Poppler needed)
    and runs Tesseract via pytesseract. If the OCR toolchain is missing (no
    pytesseract, no tesseract binary, no language data) it returns "" rather than
    raising, so the caller can surface an honest message instead of a 500. This
    keeps the "no silent zeros" promise: a scanned PDF either gets read, or the
    user is told plainly why it could not be.

    Disable with PRAMAAN_OCR=0. Point at a tesseract binary with TESSERACT_CMD
    and at language data with TESSDATA_PREFIX. DPI via PRAMAAN_OCR_DPI (default 300).
    """
    if os.getenv("PRAMAAN_OCR", "1") == "0":
        return ""
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        log.warning("OCR unavailable (missing %s) for %s", getattr(exc, "name", exc), filename)
        return ""

    cmd = os.getenv("TESSERACT_CMD")
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd

    try:
        dpi = int(os.getenv("PRAMAAN_OCR_DPI", "300"))
    except ValueError:
        dpi = 300

    try:
        doc = fitz.open(stream=data, filetype="pdf")
        pages = []
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            pages.append(pytesseract.image_to_string(img))
        doc.close()
        text = "\n\n".join(pages)
        if text.strip():
            log.info("OCR recovered %d chars from scanned PDF %s", len(text), filename)
        return text
    except Exception as exc:
        log.warning("OCR failed for %s: %s", filename, exc)
        return ""


def extract_pdf_bytes(data: bytes, filename: str = "upload.pdf") -> str:
    """Extract text from PDF bytes. Tries the embedded text layer first; if that
    is empty or near-empty (a scanned/image-only PDF), falls back to OCR."""
    text = _pdf_text_layer(data, filename)
    if len(text.strip()) >= _OCR_MIN_CHARS:
        return _clean_text(text)

    # Text layer is empty or near-empty -> likely scanned. Try OCR.
    ocr = _ocr_pdf_bytes(data, filename)
    if len(ocr.strip()) > len(text.strip()):
        return _clean_text(ocr)
    return _clean_text(text)


def _extract_pdf(path: pathlib.Path) -> str:
    return extract_pdf_bytes(path.read_bytes(), path.name)


def _extract_markdown(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def ingest_file(path: pathlib.Path) -> dict:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        raw = _extract_pdf(path)
    elif suffix in (".md", ".txt"):
        raw = _extract_markdown(path)
    else:
        log.warning("Unsupported file type: %s", suffix)
        return {"error": f"Unsupported file type: {suffix}", "path": str(path)}

    text = _clean_text(raw)
    content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

    return {
        "path": str(path),
        "filename": path.name,
        "suffix": suffix,
        "text": text,
        "word_count": len(text.split()),
        "line_count": text.count("\n") + 1,
        "content_hash": content_hash,
    }


def ingest_system(system_id: str) -> dict:
    result = {"system_id": system_id, "documents": []}

    for sub_dir, doc_type in [("specs", "spec"), ("submittals", "submittal")]:
        doc_dir = CORPUS / sub_dir
        if not doc_dir.exists():
            continue
        for ext in ("*.md", "*.pdf", "*.txt"):
            for f in sorted(doc_dir.glob(ext)):
                if f.stem == system_id or f.stem.startswith(system_id):
                    doc = ingest_file(f)
                    doc["system_id"] = system_id
                    doc["doc_type"] = doc_type
                    result["documents"].append(doc)
                    log.info("Ingested %s/%s: %d words",
                             sub_dir, f.name, doc.get("word_count", 0))

    result["total_documents"] = len(result["documents"])
    result["total_words"] = sum(d.get("word_count", 0) for d in result["documents"])
    return result


def ingest_standards() -> list[dict]:
    standards_dir = CORPUS / "standards"
    if not standards_dir.exists():
        return []

    docs = []
    for f in sorted(standards_dir.glob("*.md")):
        doc = ingest_file(f)
        doc["doc_type"] = "standard"
        doc["standard_id"] = f.stem
        docs.append(doc)
        log.info("Ingested standard %s: %d words", f.name, doc.get("word_count", 0))
    return docs


def ingest_corpus() -> dict:
    specs_dir = CORPUS / "specs"
    if not specs_dir.exists():
        return {"systems": [], "standards": [], "total_documents": 0}

    systems = sorted(p.stem for p in specs_dir.glob("*.md"))
    system_results = {}
    total_docs = 0

    for sys_id in systems:
        result = ingest_system(sys_id)
        system_results[sys_id] = result
        total_docs += result["total_documents"]

    standards = ingest_standards()
    total_docs += len(standards)

    log.info("Corpus ingestion complete: %d systems, %d standards, %d total documents",
             len(systems), len(standards), total_docs)

    return {
        "systems": system_results,
        "standards": standards,
        "total_documents": total_docs,
        "total_systems": len(systems),
        "total_standards": len(standards),
    }


def get_document_text(system_id: str, doc_type: str = "spec") -> Optional[str]:
    sub_dir = "specs" if doc_type == "spec" else "submittals"
    path = CORPUS / sub_dir / f"{system_id}.md"
    if not path.exists():
        return None
    doc = ingest_file(path)
    return doc.get("text")
