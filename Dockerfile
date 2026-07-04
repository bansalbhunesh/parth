FROM python:3.11-slim AS backend

# tesseract-ocr powers the scanned/image-only PDF + image OCR fallback
# (backend/agents/ocr_util.py). Without it the app still runs and degrades to an
# honest "OCR unavailable" message; with it, scanned submittals are read via OCR.
# Kept in sync with Dockerfile.backend so docker-compose has the same capability.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY eval/ eval/
COPY data/ data/

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM node:20-alpine AS frontend-build

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --prefer-offline 2>/dev/null || npm install
COPY frontend/ .
RUN npm run build

FROM node:20-alpine AS frontend

WORKDIR /app
COPY --from=frontend-build /app/.next .next
COPY --from=frontend-build /app/public public
COPY --from=frontend-build /app/node_modules node_modules
COPY --from=frontend-build /app/package.json package.json

EXPOSE 3000
CMD ["npm", "start"]
