"""Unversioned platform probes and bounded v1 public demo operations."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend import security
from backend.analyze import run_deterministic_analysis
from backend.platform.config import PlatformConfigurationError, get_platform_settings
from backend.platform.readiness import readiness_report

router = APIRouter()


class DemoAnalyzeRequest(BaseModel):
    spec_text: str = Field(..., min_length=10, max_length=20_000)
    submittal_text: str = Field(..., min_length=10, max_length=20_000)
    system_id: str = Field(default="CUSTOM", min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")


@router.get("/health/live", tags=["platform"], include_in_schema=True)
async def live() -> dict[str, str]:
    # No dependency I/O or thread-pool work belongs in the liveness path.
    return {"status": "ok"}


@router.get("/health/ready", tags=["platform"], include_in_schema=True)
def ready() -> JSONResponse:
    try:
        settings = get_platform_settings()
        is_ready, report = readiness_report(settings)
    except PlatformConfigurationError:
        is_ready, report = False, {"status": "not_ready", "checks": {"configuration": {"status": "invalid"}}}
    return JSONResponse(status_code=200 if is_ready else 503, content=report)


@router.get("/internal/metrics", tags=["platform"], include_in_schema=False)
def internal_metrics(request: Request) -> dict[str, object]:
    token = security.metrics_token()
    presented = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
    if not token or not secrets.compare_digest(presented, token):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    from backend import jobs
    from backend.analyze import llm_capacity_status

    return {"jobs": jobs.stats(), "analysis_capacity": llm_capacity_status()}


@router.post(
    "/api/v1/demo/analyze",
    tags=["demo"],
    dependencies=[Depends(security.rl_analysis)],
)
def demo_analyze(payload: DemoAnalyzeRequest) -> dict[str, object]:
    """Deterministic, bounded, non-persistent judge path."""
    result = run_deterministic_analysis(payload.spec_text, payload.submittal_text, payload.system_id)
    return {
        "deviations": result.deviations,
        "provenance": {
            "mode": result.mode,
            "provider": None,
            "durable_retention": False,
            "deterministic": True,
        },
        "elapsed_ms": result.elapsed_ms,
    }
