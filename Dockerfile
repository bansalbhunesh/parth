FROM python:3.11-slim AS backend

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY eval/ eval/
COPY data/ data/

EXPOSE 8099
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8099"]

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
