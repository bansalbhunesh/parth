"""
Ingestion Agent — document intake, parsing, and normalization.

Handles raw document ingestion (PDF, Markdown, plain text), extracts clean
text content, and prepares it for downstream extraction and reconciliation.

Supports:
  - Markdown pass-through (specs, submittals, standards)
  - PDF extraction via PyMuPDF (fitz)
  - Metadata tagging (system_id, doc_type, page_count, word_count)
"""

import hashlib
import logging
import pathlib
import re
from typing import Optional

log = logging.getLogger("pramaan.ingestion")

CORPUS = pathlib.Path(__file__).parent.parent.parent / "data" / "corpus"


def _clean_text(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _extract_pdf(path: pathlib.Path) -> str:
    try:
        import fitz
        doc = fitz.open(str(path))
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n\n".join(pages)
    except ImportError:
        log.warning("PyMuPDF not installed, cannot extract PDF: %s", path.name)
        return ""
    except Exception as exc:
        log.error("PDF extraction failed for %s: %s", path.name, exc)
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
