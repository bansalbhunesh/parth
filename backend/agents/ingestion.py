"""
Ingestion Agent — document intake, parsing, and normalization.
"""

import hashlib
import logging
import pathlib
import re
from typing import Optional

from backend.paths import CORPUS

log = logging.getLogger("pramaan.ingestion")


def _clean_text(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _extract_pdf(path: pathlib.Path) -> str:
    try:
        import pdfplumber
        text_pages = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_pages.append(t)
        if text_pages:
            return "\n\n".join(text_pages)
    except ImportError:
        pass
    except Exception as exc:
        log.warning("pdfplumber failed for %s: %s, trying PyMuPDF", path.name, exc)

    try:
        import fitz
        doc = fitz.open(str(path))
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n\n".join(pages)
    except ImportError:
        log.warning("No PDF library available, cannot extract: %s", path.name)
        return ""
    except Exception as exc:
        log.error("PDF extraction failed for %s: %s", path.name, exc)
        return ""


def extract_pdf_bytes(data: bytes, filename: str = "upload.pdf") -> str:
    try:
        import pdfplumber
        import io
        text_pages = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_pages.append(t)
        if text_pages:
            return _clean_text("\n\n".join(text_pages))
    except ImportError:
        pass
    except Exception as exc:
        log.warning("pdfplumber bytes extraction failed for %s: %s", filename, exc)

    try:
        import fitz
        doc = fitz.open(stream=data, filetype="pdf")
        pages = [page.get_text() for page in doc]
        doc.close()
        return _clean_text("\n\n".join(pages))
    except ImportError:
        log.warning("No PDF library available for bytes extraction")
        return ""
    except Exception as exc:
        log.error("PDF bytes extraction failed for %s: %s", filename, exc)
        return ""


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
