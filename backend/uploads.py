"""
Upload validation for the public demo: MIME/extension allowlist + magic-byte
sniffing, run BEFORE any parsing/OCR touches the bytes.

Contract:
- Accept only what the pipeline actually consumes: text (.txt/.md/...), PDF, and
  raster images (png/jpg/tiff/webp/bmp/gif). Everything else is a clean 415.
- Reject disguised files: an extension/MIME that says "pdf"/"image" but whose
  magic bytes say otherwise is a 400 (content/extension mismatch).
- Reject dangerous containers regardless of name: zip/gzip/tar/rar/7z archives
  and ELF/PE/Mach-O executables are a 415.
- Reject decompression-bomb images by header dimensions (413), before decode.
- Errors are short and user-facing — never a stack trace, path, or byte dump.

This is demo hardening, not a malware scanner. It stops the obvious abuse
(oversized, disguised, executable, archive, bomb) that a public demo attracts.
"""

import io
import os

from fastapi import HTTPException

from backend.security import safe_name

# Accepted extensions per category. Images mirror ocr_util.IMAGE_EXTS (+ .gif,
# which the image-MIME branch also routes through OCR).
_TEXT_EXTS = (".txt", ".md", ".markdown", ".text", ".csv", ".log")
_PDF_EXTS = (".pdf",)
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp", ".gif")

# Magic-byte prefixes for dangerous containers/executables — rejected outright,
# whatever the filename claims. (tar's "ustar" lives at offset 257, checked
# separately.)
_DANGEROUS_PREFIXES: dict[bytes, str] = {
    b"PK\x03\x04": "a zip archive",
    b"PK\x05\x06": "a zip archive",
    b"PK\x07\x08": "a zip archive",
    b"\x1f\x8b": "a gzip archive",
    b"Rar!\x1a\x07": "a rar archive",
    b"7z\xbc\xaf\x27\x1c": "a 7-zip archive",
    b"\x7fELF": "an executable",
    b"MZ": "a Windows executable",
    b"\xca\xfe\xba\xbe": "a compiled binary",
    b"\xfe\xed\xfa\xce": "a Mach-O executable",
    b"\xfe\xed\xfa\xcf": "a Mach-O executable",
    b"\xcf\xfa\xed\xfe": "a Mach-O executable",
    b"\xce\xfa\xed\xfe": "a Mach-O executable",
}


def _looks_like_pdf(data: bytes) -> bool:
    # Standard PDFs start with %PDF-; allow a few leading bytes some tools emit.
    return b"%PDF" in data[:1024]


def _looks_like_image(data: bytes) -> bool:
    return (
        data[:4] == b"\x89PNG"                       # PNG
        or data[:3] == b"\xff\xd8\xff"               # JPEG
        or data[:4] in (b"II*\x00", b"MM\x00*")      # TIFF (LE/BE)
        or data[:2] == b"BM"                          # BMP
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")  # WEBP
        or data[:4] in (b"GIF8",)                     # GIF
    )


def _category(ext: str, content_type: str) -> str | None:
    """Resolve the upload to pdf | image | text | None, mirroring the routing in
    ocr_util.extract_document (extension first, then MIME)."""
    ct = (content_type or "").lower()
    if ext in _PDF_EXTS or ct == "application/pdf":
        return "pdf"
    if ext in _IMAGE_EXTS or ct.startswith("image/"):
        return "image"
    if ext in _TEXT_EXTS or ct.startswith("text/"):
        return "text"
    return None


def _image_too_large(data: bytes) -> bool:
    """True if the image HEADER declares more pixels than the cap — catches a
    decompression bomb before any pixels are decoded. Best-effort: an
    unparseable/partial image returns False (the magic check already gated it,
    and OCR degrades to an honest empty result downstream)."""
    try:
        from PIL import Image

        from backend.agents.ocr_util import max_image_pixels
        with Image.open(io.BytesIO(data)) as im:
            w, h = im.size
        return w * h > max_image_pixels()
    except Exception:
        return False


def validate_upload(filename: str, content_type: str, data: bytes) -> None:
    """Raise a clean HTTPException if an upload is empty, disguised, an archive/
    executable, an oversized-by-dimensions image, or an unsupported type. No-op
    for a valid text / PDF / image upload."""
    disp = safe_name(filename)
    if not data:
        raise HTTPException(400, f"'{disp}' is empty — nothing to analyse.")

    head = data[:64]
    for sig, label in _DANGEROUS_PREFIXES.items():
        if head.startswith(sig):
            raise HTTPException(
                415, f"'{disp}' looks like {label}, which is not an accepted "
                     "document type. Upload a PDF, an image, or a text file.")
    if len(data) >= 262 and data[257:262] == b"ustar":
        raise HTTPException(
            415, f"'{disp}' looks like a tar archive, which is not an accepted "
                 "document type. Upload a PDF, an image, or a text file.")

    name = (filename or "upload").lower()
    ext = os.path.splitext(name)[1]
    category = _category(ext, content_type)
    if category is None:
        raise HTTPException(
            415, f"'{disp}' is an unsupported file type. Accepted: PDF, images "
                 "(PNG/JPG/TIFF/WEBP/BMP/GIF), or text (.txt/.md).")

    if category == "pdf":
        if not _looks_like_pdf(data):
            raise HTTPException(
                400, f"'{disp}' is named like a PDF but its contents are not a "
                     "PDF. Upload the real document or paste its text.")
    elif category == "image":
        if not _looks_like_image(data):
            raise HTTPException(
                400, f"'{disp}' is named like an image but its contents are not "
                     "a recognised image format.")
        if _image_too_large(data):
            raise HTTPException(
                413, f"'{disp}' is too large by dimensions (exceeds the image "
                     "pixel limit). Downscale it and try again.")
    else:  # text
        # A NUL byte in the first block is a strong "this is binary, not text"
        # signal — reject a binary disguised with a .txt/.md name.
        if b"\x00" in data[:8192]:
            raise HTTPException(
                415, f"'{disp}' looks like a binary file, not text. Upload a "
                     "UTF-8 text file, a PDF, or an image.")
