#!/usr/bin/env python3
"""Prove OCR behaves correctly in THIS environment (local or in-container).

Runs the same code path the API uses (backend.agents.ocr_util) against tiny
in-memory fixtures and reports, honestly:
  - whether the tesseract binary is present and OCR is enabled,
  - that a raster image and an image-only PDF are actually recovered via OCR
    (with the metadata: method / ocr_used / warning),
  - that OCR degrades to empty (never crashes) when disabled.

Exit codes:
  0  all applicable checks passed (OCR verified, or cleanly skipped when the
     tesseract binary is absent and --require-tesseract was NOT set)
  1  a real failure (OCR present but not working, or --require-tesseract set and
     the binary is missing)

Usage:
  python scripts/verify_ocr.py                 # local: skip OCR checks if no binary
  python scripts/verify_ocr.py --require-tesseract   # CI/Docker: binary MUST be present
"""
import argparse
import io
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from backend.agents import ocr_util  # noqa: E402


def _build_text_image(lines):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (1000, 300), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except Exception:
        font = ImageFont.load_default()
    y = 50
    for ln in lines:
        draw.text((50, y), ln, fill=(10, 10, 10), font=font)
        y += 56
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _build_scanned_pdf(lines):
    import fitz
    png = _build_text_image(lines)
    doc = fitz.open()
    page = doc.new_page(width=1000, height=300)
    page.insert_image(page.rect, stream=png)
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-tesseract", action="store_true",
                    help="fail (exit 1) if the tesseract binary is absent")
    args = ap.parse_args()

    installed = ocr_util.is_tesseract_available()
    version = ocr_util.get_tesseract_version()
    enabled = ocr_util.ocr_enabled()
    print("== OCR environment ==")
    print(f"  tesseract_installed : {installed}")
    print(f"  tesseract_version   : {version}")
    print(f"  ocr_enabled         : {enabled}")
    print(f"  max_pdf_pages       : {ocr_util.max_pdf_pages()}")
    print(f"  max_image_pixels    : {ocr_util.max_image_pixels()}")

    if not installed:
        msg = "tesseract binary NOT installed - OCR will be unavailable here."
        if args.require_tesseract:
            print(f"FAIL: {msg} (--require-tesseract was set)")
            return 1
        print(f"SKIP: {msg}")
        print("      (graceful 'OCR unavailable' path still applies - not a crash.)")
        return 0

    failures = []

    # 1) raster image -> OCR
    img_doc = ocr_util.extract_document(_build_text_image(["SWGR ICW 50 kA"]),
                                        "s.png", "image/png")
    ok_img = (img_doc["method"] == "ocr_image" and img_doc["ocr_used"]
              and "50" in img_doc["text"])
    print(f"\n[{'PASS' if ok_img else 'FAIL'}] image OCR -> method={img_doc['method']} "
          f"ocr_used={img_doc['ocr_used']} text={img_doc['text']!r}")
    if not ok_img:
        failures.append("image OCR did not recover text")

    # 2) image-only PDF -> OCR
    pdf_doc = ocr_util.extract_document(
        _build_scanned_pdf(["VENDOR UPS", "Runtime 7 min"]), "scan.pdf", "application/pdf")
    ok_pdf = (pdf_doc["method"] == "ocr_pdf" and pdf_doc["ocr_used"]
              and pdf_doc["warning"] and pdf_doc["text"].strip())
    print(f"[{'PASS' if ok_pdf else 'FAIL'}] scanned-PDF OCR -> method={pdf_doc['method']} "
          f"ocr_used={pdf_doc['ocr_used']} chars={pdf_doc['chars']}")
    if not ok_pdf:
        failures.append("scanned-PDF OCR did not recover text")

    # 3) graceful disable
    os.environ["PRAMAAN_OCR"] = "0"
    try:
        off = ocr_util.extract_document(_build_text_image(["ICW 50 kA"]), "s.png", "image/png")
    finally:
        os.environ.pop("PRAMAAN_OCR", None)
    ok_off = off["method"] == "none" and off["text"] == ""
    print(f"[{'PASS' if ok_off else 'FAIL'}] disabled (PRAMAAN_OCR=0) -> "
          f"method={off['method']} text={off['text']!r}")
    if not ok_off:
        failures.append("disabled OCR did not degrade to empty")

    if failures:
        print("\nRESULT: FAIL - " + "; ".join(failures))
        return 1
    print("\nRESULT: PASS - OCR verified live in this environment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
