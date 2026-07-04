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


# ── ocr_util layer: probes, scanned detection, image OCR, caps ──────

def _build_text_image(lines: list[str]) -> bytes:
    """A raster PNG with legible text — the directly-uploaded-image OCR input."""
    pytest.importorskip("PIL")
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1000, 420
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except Exception:
        font = ImageFont.load_default()
    y = 50
    for ln in lines:
        draw.text((50, y), ln, fill=(12, 12, 12), font=font)
        y += 56
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _build_text_pdf(text: str) -> bytes:
    """A digital PDF WITH a real text layer (not scanned)."""
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 96), text, fontsize=14)
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()


def test_probes_never_raise():
    """Capability probes return honest, correctly-typed values on any host —
    with or without the tesseract binary — and never raise."""
    from backend.agents import ocr_util

    assert isinstance(ocr_util.is_tesseract_available(), bool)
    assert isinstance(ocr_util.ocr_enabled(), bool)
    v = ocr_util.get_tesseract_version()
    assert v is None or isinstance(v, str)
    assert ocr_util.max_pdf_pages() > 0
    assert ocr_util.max_image_pixels() > 0


def test_ocr_enabled_flag_both_aliases(monkeypatch):
    from backend.agents import ocr_util

    monkeypatch.delenv("PRAMAAN_OCR", raising=False)
    monkeypatch.delenv("PRAMAAN_OCR_ENABLED", raising=False)
    assert ocr_util.ocr_enabled() is True
    monkeypatch.setenv("PRAMAAN_OCR", "0")
    assert ocr_util.ocr_enabled() is False
    monkeypatch.setenv("PRAMAAN_OCR", "1")
    monkeypatch.setenv("PRAMAAN_OCR_ENABLED", "0")
    assert ocr_util.ocr_enabled() is False


def test_is_scanned_pdf_true_for_scanned():
    from backend.agents import ocr_util

    assert ocr_util.is_scanned_pdf(_build_scanned_pdf(SAMPLE), "scan.pdf") is True


def test_is_scanned_pdf_false_for_text_pdf():
    from backend.agents import ocr_util

    pdf = _build_text_pdf("UPS-02 battery runtime minimum shall be 10 minutes at full load")
    assert ocr_util.is_scanned_pdf(pdf, "digital.pdf") is False


def test_image_ocr_disabled_returns_empty(monkeypatch):
    from backend.agents import ocr_util

    monkeypatch.setenv("PRAMAAN_OCR", "0")
    assert ocr_util.extract_text_from_image(_build_text_image(["ICW 50 kA"]), "image/png") == ""


def test_image_ocr_oversize_returns_empty(monkeypatch):
    """The pixel cap rejects an oversize image before OCR — no binary needed."""
    from backend.agents import ocr_util

    monkeypatch.setenv("PRAMAAN_MAX_IMAGE_PIXELS", "100")  # any real image exceeds this
    assert ocr_util.extract_text_from_image(_build_text_image(["ICW 50 kA"]), "image/png") == ""


def test_image_ocr_garbage_does_not_raise():
    from backend.agents import ocr_util

    assert ocr_util.extract_text_from_image(b"not an image", "image/png") == ""


@pytest.mark.skipif(not _tesseract_available(), reason="tesseract binary not installed")
def test_image_ocr_recovers_text():
    from backend.agents import ocr_util

    png = _build_text_image(["SWGR ICW 50 kA", "BRANCH B1 40 A"])
    text = ocr_util.extract_text_from_image(png, "image/png").replace("\n", " ")
    assert "50" in text
    assert "kA" in text or "KA" in text.upper()


@pytest.mark.skipif(not _tesseract_available(), reason="tesseract binary not installed")
def test_pdf_page_cap_limits_pages(monkeypatch):
    """With the page cap at 1, only the first page of a 2-page scan is OCR'd."""
    from backend.agents import ocr_util

    monkeypatch.setenv("PRAMAAN_MAX_PDF_PAGES", "1")
    fitz = pytest.importorskip("fitz")
    pytest.importorskip("PIL")
    from PIL import Image, ImageDraw

    def _page_png(word):
        img = Image.new("RGB", (900, 500), "white")
        ImageDraw.Draw(img).text((60, 200), word, fill=(0, 0, 0))
        b = io.BytesIO()
        img.save(b, format="PNG")
        return b.getvalue()

    doc = fitz.open()
    for word in ("ALPHAWORD", "BETAWORD"):
        pg = doc.new_page(width=900, height=500)
        pg.insert_image(pg.rect, stream=_page_png(word))
    out = io.BytesIO()
    doc.save(out)
    doc.close()

    text = ocr_util.ocr_pdf_bytes(out.getvalue(), "twopager.pdf")
    # Page 2 must be excluded by the cap (OCR may be imperfect, so only assert
    # the second page's text is absent, not that the first is perfectly read).
    assert "BETAWORD" not in text.upper()
