"""HTTP boundary helpers: request correlation and v1 problem details."""

from __future__ import annotations

import logging
import re
import time
import uuid
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

log = logging.getLogger("pramaan.http")

_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
_STATUS_CODES = {
    400: "invalid_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    412: "precondition_failed",
    413: "payload_too_large",
    422: "validation_failed",
    429: "rate_limited",
    500: "internal_error",
    502: "dependency_failed",
    503: "dependency_unavailable",
}


def problem_response(
    request: Request,
    *,
    status_code: int,
    detail: str,
    code: str | None = None,
    errors: list[dict[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Return RFC 9457-compatible problem details with stable extensions."""
    error_code = code or _STATUS_CODES.get(status_code, "request_failed")
    body: dict[str, Any] = {
        "type": f"https://pramaan.dev/problems/{error_code}",
        "title": error_code.replace("_", " ").title(),
        "status": status_code,
        "detail": detail,
        "instance": request.url.path,
        "request_id": getattr(request.state, "request_id", uuid.uuid4().hex),
        "code": error_code,
    }
    if errors:
        body["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=body,
        headers=headers,
        media_type="application/problem+json",
    )


def _safe_detail(detail: object, status_code: int) -> str:
    if isinstance(detail, str) and status_code < 500:
        return detail
    if status_code >= 500:
        return "The service could not complete this request."
    return "The request could not be completed."


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def _http_error(request: Request, exc: HTTPException) -> Response:
        if not request.url.path.startswith("/api/v1"):
            return await http_exception_handler(request, exc)
        return problem_response(
            request,
            status_code=exc.status_code,
            detail=_safe_detail(exc.detail, exc.status_code),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> Response:
        if not request.url.path.startswith("/api/v1"):
            return await request_validation_exception_handler(request, exc)
        errors = [
            {
                "field": ".".join(str(part) for part in item["loc"] if part not in {"body", "query", "path"}),
                "message": item["msg"],
                "code": item["type"],
            }
            for item in exc.errors()
        ]
        return problem_response(
            request,
            status_code=422,
            code="validation_failed",
            detail="One or more request fields are invalid.",
            errors=errors,
        )


class RequestContextMiddleware:
    """Pure-ASGI correlation middleware that does not buffer streaming bodies."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = next(
            (value.decode("latin-1") for name, value in scope.get("headers", []) if name == b"x-request-id"),
            "",
        )
        request_id = incoming if _REQUEST_ID.fullmatch(incoming) else uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        started = time.perf_counter()
        status_code = 500

        async def send_with_context(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = headers
            if message["type"] == "http.response.body" and not message.get("more_body", False):
                duration_ms = round((time.perf_counter() - started) * 1000, 2)
                log.info(
                    "request_complete method=%s path=%s status=%d duration_ms=%.2f request_id=%s",
                    scope.get("method"),
                    scope.get("path"),
                    status_code,
                    duration_ms,
                    request_id,
                )
            await send(message)

        await self.app(scope, receive, send_with_context)


class BodySizeLimitMiddleware:
    """Reject declared oversized bodies before multipart parsing/spooling."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            for name, value in scope.get("headers", []):
                if name != b"content-length":
                    continue
                try:
                    too_big = int(value) > self.max_bytes
                except ValueError:
                    await JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)(scope, receive, send)
                    return
                if too_big:
                    await JSONResponse(
                        {"detail": f"Request body exceeds the {self.max_bytes // (1024 * 1024)} MB limit"},
                        status_code=413,
                    )(scope, receive, send)
                    return
                break
        await self.app(scope, receive, send)
