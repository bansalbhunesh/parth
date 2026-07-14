"""Bounded dependency probes used by the readiness endpoint."""

from __future__ import annotations

from typing import Any

from backend.platform.config import PlatformSettings


def _postgres_ready(database_url: str) -> tuple[bool, str]:
    try:
        import psycopg

        with psycopg.connect(database_url, connect_timeout=2) as conn:
            with conn.cursor() as cursor:
                cursor.execute("select 1")
                cursor.fetchone()
        return True, "ok"
    except Exception:
        return False, "unavailable"


def _redis_ready(redis_url: str) -> tuple[bool, str]:
    try:
        from redis import Redis

        client = Redis.from_url(
            redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
        )
        client.ping()
        client.close()
        return True, "ok"
    except Exception:
        return False, "unavailable"


def readiness_report(settings: PlatformSettings) -> tuple[bool, dict[str, Any]]:
    checks: dict[str, dict[str, str]] = {}
    if settings.case_backend == "postgres" or settings.queue_backend == "supabase":
        ready, state = _postgres_ready(settings.database_url or "")
        checks["postgres"] = {"status": state}
    else:
        ready = True
        checks["sqlite"] = {"status": "ok"}

    if settings.cache_backend == "redis":
        cache_ready, state = _redis_ready(settings.redis_url or "")
        checks["redis"] = {"status": state}
        ready = ready and cache_ready
    else:
        checks["process_cache"] = {"status": "ok"}

    checks["identity"] = {
        "status": "configured" if settings.auth_backend == "supabase" else "local_demo",
    }
    return ready, {"status": "ready" if ready else "not_ready", "checks": checks}
