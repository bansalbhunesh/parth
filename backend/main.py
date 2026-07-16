"""Pramaan API application assembly — uvicorn backend.main:app."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import security
from backend.http import (
    BodySizeLimitMiddleware,
    RequestContextMiddleware,
    install_exception_handlers,
    problem_response,
)
from backend.platform.observability import configure_observability
from backend.routers import analysis, cases, data, exports, projects, webhooks
from backend.routers.platform import router as platform_router
from backend.versioning import register_v1_compatibility

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pramaan.api")

app = FastAPI(
    title="Pramaan — EPC Deviation Intelligence",
    description="Spec-to-Site Deviation Sentinel for hyperscale data-centre EPC delivery",
    version="2.0.0",
)

_cors_env = os.getenv("PRAMAAN_CORS_ORIGINS", "").strip()
_cors_origins = [origin.strip() for origin in _cors_env.split(",") if origin.strip()] or [
    "https://parth-tan.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Authorization",
        "Content-Type",
        "X-Case-Secret",
        "X-Demo-Token",
        "X-Request-ID",
        "Idempotency-Key",
        "If-Match",
    ],
    expose_headers=["X-Request-ID", "ETag", "Retry-After"],
)
app.add_middleware(RequestContextMiddleware)
MAX_REQUEST_BYTES = security.max_upload_bytes() + 5 * 1024 * 1024
app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_REQUEST_BYTES)
install_exception_handlers(app)
configure_observability(app)


@app.exception_handler(Exception)
async def _never_crash(request: Request, exc: Exception) -> JSONResponse:
    """Return a stable, secret-free response for unexpected failures."""
    log.error("Unhandled error on %s %s: %s", request.method, request.url.path, str(exc)[:300])
    if request.url.path.startswith("/api/v1"):
        return problem_response(
            request,
            status_code=500,
            code="internal_error",
            detail="The service could not complete this request.",
        )
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": "internal_error",
            "detail": "This request failed unexpectedly; the rest of the API is unaffected.",
        },
    )


APPLICATION_ROUTERS = (
    webhooks.router,
    analysis.router,
    data.router,
    exports.router,
    cases.router,
    projects.router,
    platform_router,
)

for application_router in APPLICATION_ROUTERS:
    app.include_router(application_router)

V1_COMPATIBILITY_ROUTE_COUNT = register_v1_compatibility(app, APPLICATION_ROUTERS)
