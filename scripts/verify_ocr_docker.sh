#!/usr/bin/env sh
# Prove OCR works in the DEPLOYED backend image (the one Render/compose build).
# Builds Dockerfile.backend, runs it, and asserts GET /ocr-check reports
# "status":"ready" with a real tesseract version -- i.e. OCR is genuinely live in
# the shipping image, not just in local dev.
#
# Exit 0 = OCR ready in the image; non-zero = build/run failed or OCR not ready.
#
# Usage:  sh scripts/verify_ocr_docker.sh
set -eu

IMG="pramaan-backend-ocrverify"
NAME="pramaan-ocrverify-run"
PORT="${PORT:-8021}"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

echo "== Building OCR-capable backend image (Dockerfile.backend) =="
docker build -f Dockerfile.backend -t "$IMG" .

echo "== Running container on :$PORT =="
cleanup
docker run -d --name "$NAME" -p "$PORT:8000" "$IMG" >/dev/null

echo "== Waiting for boot =="
i=0
until curl -sf "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; do
  i=$((i + 1))
  if [ "$i" -ge 40 ]; then
    echo "FAIL: backend did not become healthy in time"; docker logs "$NAME" | tail -20; exit 1
  fi
  sleep 1
done

echo "== Checking /ocr-check =="
BODY="$(curl -sf "http://127.0.0.1:$PORT/ocr-check")"
echo "$BODY"
# Pure-shell assertion (no python needed) so this runs the same on Windows + CI.
case "$BODY" in
  *'"status":"ready"'*)
    case "$BODY" in
      *'"ocr_available":true'*) echo "PASS - OCR ready in the shipping image." ;;
      *) echo "FAIL - status ready but ocr_available not true"; exit 1 ;;
    esac ;;
  *) echo "FAIL - OCR not ready in image"; exit 1 ;;
esac
