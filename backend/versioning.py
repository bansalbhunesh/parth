"""Register compatibility copies of legacy operations under ``/api/v1``."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Request, Security
from fastapi.params import Depends as DependsParam
from fastapi.routing import APIRoute
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.platform.config import get_platform_settings
from backend.platform.contracts import Principal
from backend.platform.identity import require_supabase_identity

_EXCLUDED_PREFIXES = ("/api/v1", "/health/", "/internal/")
_PROTECTED_ROOTS = (
    "/analyze",
    "/jobs",
    "/cases",
    "/copilot",
    "/export",
    "/ingest",
    "/webhooks",
)
_bearer_scheme = HTTPBearer(auto_error=False)


def require_managed_identity(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> Principal | None:
    """Require Supabase identity in managed environments; retain local demo mode."""
    settings = get_platform_settings()
    if settings.auth_backend == "supabase":
        return require_supabase_identity(request)
    del credentials
    return None


def _is_protected(path: str) -> bool:
    return path.startswith(_PROTECTED_ROOTS)


def _route_kwargs(route: APIRoute, dependency: DependsParam | None) -> dict[str, Any]:
    dependencies = list(route.dependencies or [])
    if dependency is not None:
        dependencies.append(dependency)
    return {
        "response_model": route.response_model,
        "status_code": route.status_code,
        "tags": [*(route.tags or []), "v1"],
        "dependencies": dependencies,
        "summary": route.summary,
        "description": route.description,
        "response_description": route.response_description,
        "responses": route.responses,
        "deprecated": False,
        "methods": route.methods,
        "operation_id": f"v1_{route.operation_id or route.name}",
        "response_model_include": route.response_model_include,
        "response_model_exclude": route.response_model_exclude,
        "response_model_by_alias": route.response_model_by_alias,
        "response_model_exclude_unset": route.response_model_exclude_unset,
        "response_model_exclude_defaults": route.response_model_exclude_defaults,
        "response_model_exclude_none": route.response_model_exclude_none,
        "include_in_schema": route.include_in_schema,
        "response_class": route.response_class,
        "name": f"v1_{route.name}",
        "callbacks": route.callbacks,
        "openapi_extra": route.openapi_extra,
    }


def register_v1_compatibility(app: FastAPI) -> int:
    """Copy every public legacy operation once, preserving its behavior and schema."""
    legacy_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and not route.path.startswith(_EXCLUDED_PREFIXES)
    ]
    router = APIRouter()
    for route in legacy_routes:
        dependency = Depends(require_managed_identity) if _is_protected(route.path) else None
        router.add_api_route(
            f"/api/v1{route.path}",
            route.endpoint,
            **_route_kwargs(route, dependency),
        )
        route.deprecated = True
    app.include_router(router)
    return len(legacy_routes)
