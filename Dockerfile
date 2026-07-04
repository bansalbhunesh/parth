# NOTE: the backend image is built from Dockerfile.backend (it apt-installs the
# tesseract-ocr binary for OCR). That single image is used by Render, docker-compose,
# and CI, so there is exactly one OCR-capable backend definition. This file builds
# only the frontend (docker-compose targets the `frontend` stage below).

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
