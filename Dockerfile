# NOTE: the backend image is built from Dockerfile.backend (it apt-installs the
# tesseract-ocr binary for OCR). That single image is used by Render, docker-compose,
# and CI, so there is exactly one OCR-capable backend definition. This file builds
# only the frontend (docker-compose targets the `frontend` stage below).

FROM node:24.17.0-alpine3.23@sha256:7c70d1235c0b4c2bc9eeed5393d19f1bbdde6885ba0d58ba62bb385d7b0f3ff1 AS frontend-build

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --prefer-offline
COPY frontend/ .
RUN npm run build

FROM node:24.17.0-alpine3.23@sha256:7c70d1235c0b4c2bc9eeed5393d19f1bbdde6885ba0d58ba62bb385d7b0f3ff1 AS frontend

WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000
COPY --chown=node:node --from=frontend-build /app/public ./public
COPY --chown=node:node --from=frontend-build /app/.next/standalone ./
COPY --chown=node:node --from=frontend-build /app/.next/static ./.next/static

USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:3000/').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]
CMD ["node", "server.js"]
