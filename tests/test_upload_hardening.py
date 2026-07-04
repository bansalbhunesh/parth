"""Upload hardening: size / MIME / extension / magic-byte allowlist.

A public demo attracts junk uploads — oversized files, archives, executables,
files disguised behind a friendly extension, and decompression-bomb images.
These prove each is rejected with a clean 4xx (no stack trace, no filesystem
path), while genuine text / PDF / image uploads still flow through, and a
rejected upload never yields a seeded / fake finding.
"""

import io

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

_GOOD_SPEC = ("s.txt", b"**UPS-02** - battery runtime: shall be **10 min**", "text/plain")


def _upload(spec, submittal):
    return client.post("/analyze/upload", files=[
        ("spec_file", spec),
        ("submittal_file", submittal),
    ])


def _clean_error(r):
    """A rejection must be a short JSON detail — no traceback, no path leak."""
    body = r.text
    assert "Traceback" not in body
    assert "C:\\" not in body and "/Users/" not in body and "/home/" not in body
    assert "site-packages" not in body
    detail = r.json().get("detail", "")
    assert isinstance(detail, str) and 0 < len(detail) < 400


def test_oversized_upload_rejected_413(monkeypatch):
    monkeypatch.setenv("PRAMAAN_MAX_UPLOAD_BYTES", "100")  # tiny cap for the test
    big = ("s.txt", b"x" * 500, "text/plain")
    r = _upload(big, _GOOD_SPEC)
    assert r.status_code == 413
    _clean_error(r)


def test_zip_archive_rejected_even_as_txt():
    """A zip disguised with a .txt name is caught by magic bytes → 415."""
    zip_bytes = b"PK\x03\x04" + b"\x00" * 40
    r = _upload(_GOOD_SPEC, ("payload.txt", zip_bytes, "text/plain"))
    assert r.status_code == 415
    assert "archive" in r.json()["detail"].lower()
    _clean_error(r)


def test_windows_executable_rejected():
    exe = b"MZ\x90\x00\x03" + b"\x00" * 40
    r = _upload(_GOOD_SPEC, ("tool.txt", exe, "application/octet-stream"))
    assert r.status_code == 415
    assert "executable" in r.json()["detail"].lower()
    _clean_error(r)


def test_elf_binary_rejected():
    elf = b"\x7fELF" + b"\x00" * 40
    r = _upload(_GOOD_SPEC, ("a.out", elf, "application/octet-stream"))
    assert r.status_code == 415
    _clean_error(r)


def test_fake_pdf_extension_rejected():
    """Named .pdf but the bytes are a PNG → content/extension mismatch → 400."""
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 40
    r = _upload(_GOOD_SPEC, ("disguised.pdf", png_bytes, "application/pdf"))
    assert r.status_code == 400
    assert "pdf" in r.json()["detail"].lower()
    _clean_error(r)


def test_fake_image_extension_rejected():
    """Named .png but the bytes are not any recognised image → 400."""
    r = _upload(_GOOD_SPEC, ("notreally.png", b"this is plain text, not an image", "image/png"))
    assert r.status_code == 400
    _clean_error(r)


def test_unsupported_type_rejected_415():
    r = _upload(_GOOD_SPEC, ("weird.xyz", b"some bytes", "application/x-unknown"))
    assert r.status_code == 415
    _clean_error(r)


def test_binary_disguised_as_text_rejected():
    r = _upload(_GOOD_SPEC, ("data.txt", b"abc\x00\x01\x02binarydef", "text/plain"))
    assert r.status_code == 415
    _clean_error(r)


def test_empty_file_rejected():
    r = _upload(_GOOD_SPEC, ("empty.txt", b"", "text/plain"))
    assert r.status_code == 400
    _clean_error(r)


def test_huge_image_by_dimensions_rejected(monkeypatch):
    """A real PNG whose header declares more pixels than the cap → 413, before
    any decode (decompression-bomb guard)."""
    pytest.importorskip("PIL")
    from PIL import Image
    monkeypatch.setenv("PRAMAAN_MAX_IMAGE_PIXELS", "100")  # 10x10 already exceeds
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buf, format="PNG")
    r = _upload(_GOOD_SPEC, ("big.png", buf.getvalue(), "image/png"))
    assert r.status_code == 413
    assert "large" in r.json()["detail"].lower() or "pixel" in r.json()["detail"].lower()
    _clean_error(r)


def test_rejected_upload_yields_no_findings():
    """A rejected upload must NOT fall through to any seeded/fake result — the
    response is a 4xx error, never a 200 with deviations."""
    r = _upload(_GOOD_SPEC, ("evil.zip", b"PK\x03\x04junk", "application/zip"))
    assert r.status_code >= 400
    assert "deviations" not in r.json()


def test_valid_text_pdf_still_accepted():
    """Regression: a genuine text-layer PDF passes validation and analyses."""
    fitz = pytest.importorskip("fitz")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 96), "UPS-02 battery runtime 7 min", fontsize=14)
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    r = _upload(("spec.txt", b"**UPS-02** - battery runtime: shall be **10 min**", "text/plain"),
                ("submittal.pdf", out.getvalue(), "application/pdf"))
    assert r.status_code == 200
    assert r.json()["extraction"]["submittal"]["method"] == "text_layer"


def test_valid_image_upload_still_accepted(monkeypatch):
    """Regression: a real PNG (small) passes validation; OCR is mocked."""
    import backend.agents.ocr_util as ocr_util
    monkeypatch.setattr(ocr_util, "extract_text_from_image",
                        lambda data, mime="image/png": "**UPS-02** - battery runtime: **7 min**")
    pytest.importorskip("PIL")
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), "white").save(buf, format="PNG")
    r = _upload(("spec.txt", b"**UPS-02** - battery runtime: shall be **10 min**", "text/plain"),
                ("submittal.png", buf.getvalue(), "image/png"))
    assert r.status_code == 200
    assert r.json()["extraction"]["submittal"]["ocr_used"] is True
