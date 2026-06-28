"""
OCR fallback for scanned / image-only PDFs.

Real EPC submittals are frequently scanned paper emailed as image-only PDFs —
which carry no text layer. These tests prove the pipeline (a) recovers text from
such a PDF via OCR when Tesseract is available, and (b) degrades honestly (empty
string, no crash) when it is not, so the API can surface a clear message.
"""

import io

import pytest

from backend.agents.ingestion import extract_pdf_bytes


def _build_scanned_pdf(lines: list[str]) -> bytes:
    """Render text to an image and embed it as a full-page image in a PDF, so the
    resulting PDF has NO text layer — a faithful scanned-document simulation."""
    fitz = pytest.importorskip("fitz")
    pytest.importorskip("PIL")
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1000, 1300
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 26)
    except Exception:
        font = ImageFont.load_default()
    y = 70
    for ln in lines:
        draw.text((70, y), ln, fill=(15, 15, 15), font=font)
        y += 46

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    doc = fitz.open()
    page = doc.new_page(width=W, height=H)
    page.insert_image(page.rect, stream=buf.read())
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()


def _tesseract_available() -> bool:
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


SAMPLE = [
    "VENDOR SUBMITTAL - UPS",
    "Manufacturer: Vertiv Liebert GXT5",
    "Online efficiency: up to 95.9 percent",
    "Battery runtime at full load: 7 min",
    "Input THD: not stated",
]


def test_scanned_pdf_has_no_text_layer():
    """Sanity: the simulated scan genuinely carries no text layer, so this
    exercises the OCR path rather than plain extraction."""
    from backend.agents.ingestion import _pdf_text_layer

    pdf = _build_scanned_pdf(SAMPLE)
    assert len(_pdf_text_layer(pdf, "scan.pdf").strip()) < 20


@pytest.mark.skipif(not _tesseract_available(), reason="tesseract binary not installed")
def test_ocr_recovers_scanned_pdf():
    pdf = _build_scanned_pdf(SAMPLE)
    text = extract_pdf_bytes(pdf, "scan.pdf")
    assert "Vertiv" in text
    assert "95.9" in text
    assert "7 min" in text.replace("\n", " ")


def test_ocr_disabled_returns_empty_for_scanned(monkeypatch):
    """With OCR turned off, a scanned PDF yields empty (the API then surfaces an
    honest 'scanned PDF' message) — never a crash."""
    monkeypatch.setenv("PRAMAAN_OCR", "0")
    pdf = _build_scanned_pdf(SAMPLE)
    assert extract_pdf_bytes(pdf, "scan.pdf").strip() == ""


def test_ocr_failure_does_not_raise(monkeypatch):
    """A broken tesseract path must degrade to '' rather than raising."""
    monkeypatch.setenv("PRAMAAN_OCR", "1")
    monkeypatch.setenv("TESSERACT_CMD", "/nonexistent/tesseract-binary")
    pdf = _build_scanned_pdf(SAMPLE)
    # Must not raise; empty text layer + failed OCR -> ""
    assert extract_pdf_bytes(pdf, "scan.pdf").strip() == ""
