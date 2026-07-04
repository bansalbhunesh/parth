# OCR Deployment Checklist

Pramaan reads scanned / image-only PDFs **and** directly-uploaded images
(`.png/.jpg/.tiff/.webp`) via **Tesseract OCR**, text-first with an OCR fallback.
OCR is best-effort (not lossless) and needs the `tesseract` **system binary**.
This checklist makes OCR demo-safe: it either works and is proven, or it is
honestly reported as unavailable — never a silent zero and never a false claim.

## The one rule

> A deployment may only imply OCR works if `GET /ocr-check` returns
> `"status": "ready"`. That endpoint live-probes the tesseract binary, so it is
> the single source of truth — the UI badge and docs defer to it.

## Where OCR runs

| Target | OCR binary? | How |
|---|---|---|
| Local dev (`make run`) | only if `tesseract` is on PATH | install Tesseract locally, or set `TESSERACT_CMD` |
| Docker (`Dockerfile.backend`) | ✅ yes | `apt-get install tesseract-ocr` in the image |
| docker-compose (`make docker`) | ✅ yes | backend service builds `Dockerfile.backend` |
| Render (`render.yaml`) | ✅ yes | `runtime: docker` → builds `Dockerfile.backend` |
| Plain Python buildpack | ❌ no | buildpack can't `apt-get` → graceful "OCR unavailable" |

There is **one** OCR-capable backend image (`Dockerfile.backend`); Render,
compose, and CI all use it, so they can't drift apart.

## Verify locally

```bash
make verify-ocr          # in-process: probes + image/scanned-PDF recovery + disable path
# or, prove the shipping image:
make verify-ocr-docker   # builds Dockerfile.backend, asserts /ocr-check == ready
```

`make verify-ocr` **skips cleanly** (exit 0) when no binary is installed — pass
`python scripts/verify_ocr.py --require-tesseract` to make its absence a failure
(CI/Docker use this expectation via the docker-build smoke test).

## Deploy to Render (enables OCR in production)

1. Merge the branch so `render.yaml` (Docker runtime → `Dockerfile.backend`) is on `main`.
2. Render → the `pramaan-backend` service → **Manual Deploy → latest commit**.
   (First Docker build is slower than the buildpack — it apt-installs Tesseract.)
3. Confirm the live backend:
   ```bash
   curl -s https://<your-backend>.onrender.com/ocr-check
   # expect: {"status":"ready","ocr_available":true,"tesseract_version":"5.x.x",...}
   curl -s https://<your-backend>.onrender.com/health   # ok:true, ocr_available:true
   ```
4. In Judge Mode, the upload panel shows **"OCR ready — scanned PDFs & images
   supported (Tesseract 5.x)"**. Upload a scanned PDF; the result carries an
   amber **"Read via OCR — verify critical values"** caveat.

## Config (env)

| Var | Default | Meaning |
|---|---|---|
| `PRAMAAN_OCR_ENABLED` (alias `PRAMAAN_OCR`) | `1` | `0` disables OCR everywhere |
| `PRAMAAN_OCR_DPI` | `300` | scanned-PDF rasterization DPI |
| `PRAMAAN_MAX_PDF_PAGES` | `30` | cap on pages OCR'd per PDF |
| `PRAMAAN_MAX_IMAGE_PIXELS` | `20000000` | reject larger images (bomb guard) |
| `TESSERACT_CMD` | — | path to the binary if not on PATH |
| `TESSDATA_PREFIX` | — | language-data dir |

## If OCR becomes risky near a deadline — disable honestly

Prefer honest disabling over half-working OCR. Any of these makes the product
truthful with OCR off, with **no false claims** (the UI badge, `/ocr-check`, and
docs all report "unavailable"):

- Set `PRAMAAN_OCR_ENABLED=0` (badge shows "OCR disabled", uploads of scanned
  PDFs/images return the honest 400 message), **or**
- Revert `render.yaml` to the Python buildpack (badge shows "OCR unavailable").

Either way, text-based PDFs and pasted text keep working, and nothing in the UI
or docs claims OCR that the runtime can't deliver.

## What OCR does NOT claim

- Not lossless (e.g. `GXT5` can read as `GXTS`) — hence the verify-values warning.
- English-only, best-effort; no per-page scanned detection (whole-document
  20-char heuristic). See [`../eval/OCR_SCANNED_PDF.md`](../eval/OCR_SCANNED_PDF.md)
  and claims-register rows 20–21 in [`CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md).
- Image OCR here (Tesseract → text) is distinct from `/analyze/vision` (an LLM
  reads the picture) — different paths, different contracts.
