# Scanned-PDF Robustness — OCR Fallback

Real EPC submittals are rarely clean digital PDFs. They are **paper documents,
stamped and signed, scanned to image-only PDFs and emailed.** A pipeline that
only reads a PDF's embedded text layer silently returns nothing on these — the
single most common real-world input, and exactly the failure a judge can trigger
by uploading their own scanned file.

Pramaan handles it: when a PDF carries no usable text layer, it falls back to
**OCR** (PyMuPDF rasterization → Tesseract). The same Tesseract path also reads
**directly-uploaded raster images** (`.png/.jpg/.tiff/.webp`) through the normal
text-reconcile upload. When the OCR toolchain is absent it degrades to an
**honest, actionable message** rather than a silent zero or a 500.

All of this lives in one dependency-guarded module, [`backend/agents/ocr_util.py`](../backend/agents/ocr_util.py),
and **`GET /ocr-check` reports whether OCR is actually live in a given deployment**
(`{"status":"ready", ...}` when the tesseract binary is present and OCR is enabled)
— so a claim is never stronger than the running environment. Note the image OCR
here (Tesseract → text) is distinct from the `/analyze/vision` path, where a
vision LLM reads values straight from the picture.

## Try it

A real, messy, image-only sample ships in the repo:
[`../data/samples/real/scanned/submittal_ups_scanned.pdf`](../data/samples/real/scanned/submittal_ups_scanned.pdf)
— a skewed, noised, JPEG-compressed scan of a Vertiv GXT5 UPS submittal (no text
layer). Pair it with [`../data/samples/real/design_basis_helios.md`](../data/samples/real/design_basis_helios.md).

```python
import pathlib
from backend.agents.ingestion import _pdf_text_layer, extract_pdf_bytes
data = pathlib.Path("data/samples/real/scanned/submittal_ups_scanned.pdf").read_bytes()
print(len(_pdf_text_layer(data, "scan.pdf").strip()))   # -> 0  (no text layer)
print(extract_pdf_bytes(data, "scan.pdf")[:80])         # -> OCR-recovered text
```

## Result — text fully recovered from an image-only scan

| Check | Text-layer only (before) | With OCR fallback |
|-------|--------------------------|-------------------|
| Characters extracted | **0** | **404** |
| `Online efficiency: 95.9%` | ✗ | ✅ recovered |
| `Battery runtime: 7 min` | ✗ | ✅ recovered |
| `Input THD: not stated` | ✗ | ✅ recovered |
| Pipeline outcome | HTTP 400, unusable | deviations detected normally |

**Honesty note:** OCR is not lossless — on this sample the model name rendered as
`GXTS` instead of `GXT5` (a classic 5/S confusion). Every *numeric* fact the
deviation engine needs (95.9 %, 7 min, THD omission) came through clean, so
detection is unaffected; but we don't claim pixel-perfect transcription.

## Honest degradation (the "no silent zeros" promise, extended to paper)

| Situation | Behaviour |
|-----------|-----------|
| Digital PDF with text layer | Read directly (pdfplumber → PyMuPDF) |
| Scanned / image-only PDF, **Tesseract present** | OCR recovers the text |
| Scanned PDF, **OCR toolchain absent** | Clear message: *"looks like a scanned / image-only PDF and OCR is unavailable — upload a text-based PDF or paste the text."* Never a silent zero or crash |

## Deployment

- **Local / Docker / docker-compose:** [`Dockerfile.backend`](../Dockerfile.backend)
  and the root [`Dockerfile`](../Dockerfile) backend stage both `apt-get install
  tesseract-ocr`, so OCR works out of the box.
- **Render:** `render.yaml` now builds from `Dockerfile.backend`
  (`runtime: docker`), so the hosted backend ships Tesseract and OCR runs in
  production. *(Deploy step: after this change is merged, redeploy the Render
  service and confirm `GET /ocr-check` returns `"status":"ready"`.)* A plain
  Python buildpack cannot `apt-get`, so on any non-Docker host OCR degrades to
  the honest "OCR unavailable" message above — `GET /ocr-check` tells you which
  case you are in.
- **Config:** `PRAMAAN_OCR_ENABLED=0` (alias `PRAMAAN_OCR=0`) disables OCR;
  `TESSERACT_CMD` points at the binary; `TESSDATA_PREFIX` at the language data;
  `PRAMAAN_OCR_DPI` (default 300) trades speed for accuracy; `PRAMAAN_MAX_PDF_PAGES`
  (default 30) caps pages OCR'd per PDF; `PRAMAAN_MAX_IMAGE_PIXELS` (default 20M)
  rejects oversize images (decompression-bomb guard).

Tests: [`../tests/test_ocr.py`](../tests/test_ocr.py) — builds an image-only PDF
in-memory, asserts OCR recovery (skipped where Tesseract is absent), and asserts
graceful empty-string degradation when OCR is disabled or broken. Prove it in
your environment with `make verify-ocr` (local) or `make verify-ocr-docker` (the
shipping image). Deploy/verify steps: [`../docs/OCR_DEPLOYMENT_CHECKLIST.md`](../docs/OCR_DEPLOYMENT_CHECKLIST.md).
