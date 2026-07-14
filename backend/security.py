"""
Public-demo security controls: optional token auth + process-local rate limiting.

This is **demo hardening**, not production security. The rate limiter is an
in-process sliding-window counter — correct for a single-instance demo, but it
does NOT share state across replicas or survive a restart. A real deployment
would key limits off a shared store (Redis) behind a trusted proxy. See
`docs/SECURITY_DEMO_RUNBOOK.md`.

Design rules:
- Everything is env-gated and OFF-by-default-safe: with no env set, auth is
  disabled (open demo) and rate limiting uses generous defaults.
- Secrets never leave this module: the demo token is compared in constant time
  and is never logged, echoed, or placed in any response or status payload.
- Config is read per-request (not cached at import) so tests can toggle it.
"""

import logging
import os
import secrets
import threading
import time

from fastapi import HTTPException, Request

log = logging.getLogger("pramaan.security")

_WINDOW_S = 3600  # rate-limit window: per hour


def _truthy(v) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes", "on"} if v is not None else False


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (ValueError, TypeError):
        return default


def safe_name(name: str) -> str:
    """Sanitize a user-supplied filename for safe echo in an error message:
    drop control chars / path separators and truncate. Keeps errors readable
    without reflecting attacker-controlled newlines or long payloads."""
    base = os.path.basename(str(name or "upload").replace("\\", "/"))
    cleaned = "".join(c for c in base if c.isprintable() and c not in "\r\n")
    return (cleaned or "upload")[:80]


# ── Demo token auth ─────────────────────────────────────────────────

def _demo_token() -> str:
    return os.getenv("DEMO_AUTH_TOKEN", "").strip()


def auth_required() -> bool:
    """Return whether protected endpoints require authentication.

    Enabling the gate is authoritative. A missing token is handled as a
    configuration error by ``require_demo_auth``; it never turns a protected
    deployment back into an open one.
    """
    return _truthy(os.getenv("DEMO_AUTH_ENABLED", "false"))


def _presented_token(request: Request) -> str:
    """Read a token from a header only.

    Query-string tokens are intentionally rejected because URLs leak into
    browser history, referrers, analytics, and access logs.
    """
    hdr = request.headers.get("x-demo-token")
    if hdr:
        return hdr.strip()
    auth = request.headers.get("authorization", "")
    if auth[:7].lower() == "bearer ":
        return auth[7:].strip()
    return ""


def require_demo_auth(request: Request) -> None:
    """FastAPI dependency: enforce the demo token on protected endpoints.
    No-op when auth is not active. 401 = no token supplied, 403 = wrong token.
    The token value is never included in the error or logged."""
    if not auth_required():
        return
    configured = _demo_token()
    if not configured:
        log.error("DEMO_AUTH_ENABLED is true but DEMO_AUTH_TOKEN is empty")
        raise HTTPException(
            status_code=503,
            detail="Protected analysis is temporarily unavailable because access control is not configured.",
        )
    presented = _presented_token(request)
    if not presented:
        raise HTTPException(
            status_code=401,
            detail="This demo endpoint requires an access token "
                   "(send it in the 'X-Demo-Token' or Authorization header).",
        )
    if not secrets.compare_digest(presented, configured):
        raise HTTPException(status_code=403, detail="Invalid demo access token.")


# ── Rate limiting (process-local sliding window) ────────────────────

def rate_limit_enabled() -> bool:
    return _truthy(os.getenv("PRAMAAN_RATE_LIMIT_ENABLED", "true"))


def analysis_limit() -> int:
    return _int_env("PRAMAAN_ANALYSIS_LIMIT_PER_HOUR", 20)


def upload_limit() -> int:
    return _int_env("PRAMAAN_UPLOAD_LIMIT_PER_HOUR", 10)


def deep_probe_limit() -> int:
    return _int_env("PRAMAAN_DEEP_PROBE_LIMIT_PER_HOUR", 3)


def case_create_limit() -> int:
    return _int_env("PRAMAAN_CASE_CREATE_LIMIT_PER_HOUR", 10)


_store: dict[str, list[float]] = {}
_lock = threading.Lock()
_redis_limiter = None
_redis_limiter_url = ""


def reset_rate_limits() -> None:
    """Clear all counters — used by the test suite between cases so limits do
    not leak across tests. Not wired to any endpoint."""
    global _redis_limiter, _redis_limiter_url
    with _lock:
        _store.clear()
        _redis_limiter = None
        _redis_limiter_url = ""


def _distributed_limiter():
    global _redis_limiter, _redis_limiter_url
    url = os.getenv("PRAMAAN_REDIS_URL", "").strip()
    if not url:
        return None
    with _lock:
        if _redis_limiter is None or _redis_limiter_url != url:
            from backend.platform.redis_limits import RedisRateLimiter

            _redis_limiter = RedisRateLimiter.from_url(url)
            _redis_limiter_url = url
        return _redis_limiter


def _client_key(request: Request) -> str:
    """Best-effort client identity for bucketing. Prefers the first hop of
    X-Forwarded-For only when PRAMAAN_TRUST_PROXY_HEADERS is explicitly enabled;
    otherwise it falls back to the socket peer.
    If a demo token is presented it is folded in so distinct tokens get distinct
    buckets. A shared store behind a trusted proxy remains the production answer."""
    xff = (
        request.headers.get("x-forwarded-for", "")
        if _truthy(os.getenv("PRAMAAN_TRUST_PROXY_HEADERS", "false"))
        else ""
    )
    ip = xff.split(",")[0].strip() if xff else (
        request.client.host if request.client else "unknown")
    tok = _presented_token(request)
    # Fold a HASH of the token into the key (never the raw token) so distinct
    # tokens get distinct buckets without the value ever landing in the store.
    tok_tag = ""
    if tok:
        import hashlib
        tok_tag = hashlib.sha256(tok.encode()).hexdigest()[:12]
    return f"{ip}|{tok_tag}"


def enforce_rate_limit(request: Request, bucket: str, limit: int) -> None:
    """Sliding-window limiter: at most `limit` hits per hour per client per
    bucket. Raises a clean 429 with a Retry-After header when exceeded. No-op
    when rate limiting is disabled. Never logs client identity or secrets."""
    if not rate_limit_enabled() or limit <= 0:
        return
    client_key = _client_key(request)
    distributed = _distributed_limiter()
    if distributed is not None:
        from backend.platform.redis_limits import DistributedLimitUnavailable

        try:
            decision = distributed.check(
                client_key,
                bucket,
                limit,
                int(_WINDOW_S),
                fail_closed=True,
            )
        except DistributedLimitUnavailable as exc:
            raise HTTPException(
                status_code=503,
                detail="The distributed abuse-control service is unavailable; expensive work was not started.",
                headers={"Retry-After": "5"},
            ) from exc
        if not decision.allowed:
            retry = max(1, int((decision.reset_at_ms / 1000) - time.time()) + 1)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit reached ({limit} {bucket} requests/hour).",
                headers={"Retry-After": str(retry)},
            )
        return

    key = f"{bucket}:{client_key}"
    now = time.time()
    cutoff = now - _WINDOW_S
    with _lock:
        hits = _store.setdefault(key, [])
        hits[:] = [t for t in hits if t > cutoff]
        if len(hits) >= limit:
            retry = max(1, int(hits[0] + _WINDOW_S - now) + 1)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit reached for this demo ({limit} {bucket} "
                       f"requests/hour). Please retry in about {retry} seconds.",
                headers={"Retry-After": str(retry)},
            )
        hits.append(now)


# Dependency wrappers so endpoints can declare `dependencies=[Depends(...)]`
# without changing their signatures.
def rl_analysis(request: Request) -> None:
    enforce_rate_limit(request, "analysis", analysis_limit())


def rl_upload(request: Request) -> None:
    enforce_rate_limit(request, "upload", upload_limit())


def rl_deep_probe(request: Request) -> None:
    enforce_rate_limit(request, "deep_probe", deep_probe_limit())


def rl_case_create(request: Request) -> None:
    enforce_rate_limit(request, "case_create", case_create_limit())


# ── Upload size caps (shared with the upload validator) ─────────────

def max_upload_mb() -> int:
    return _int_env("PRAMAAN_MAX_UPLOAD_MB", 20)


def max_upload_bytes() -> int:
    """Per-file byte cap. PRAMAAN_MAX_UPLOAD_BYTES (raw bytes) overrides
    PRAMAAN_MAX_UPLOAD_MB when set — handy for byte-granular tests."""
    raw = os.getenv("PRAMAAN_MAX_UPLOAD_BYTES", "")
    if raw.strip().isdigit():
        return int(raw.strip())
    return max_upload_mb() * 1024 * 1024


# ── Safe status for /health (no secrets) ────────────────────────────

def security_status() -> dict:
    """Non-secret snapshot of the demo's security posture for /health. Reports
    only booleans / caps / counts — never the token, never a client IP."""
    from backend.agents import ocr_util
    from backend.llm import provider_chain
    rl_on = rate_limit_enabled()
    return {
        "auth_required": auth_required(),
        "rate_limit_enabled": rl_on,
        "rate_limit_backend": "redis" if os.getenv("PRAMAAN_REDIS_URL", "").strip() else "process-local",
        "rate_limits_per_hour": {
            "analysis": analysis_limit(),
            "upload": upload_limit(),
            "deep_probe": deep_probe_limit(),
            "case_create": case_create_limit(),
        } if rl_on else None,
        "max_upload_mb": max_upload_mb(),
        "max_pdf_pages": ocr_util.max_pdf_pages(),
        "max_image_pixels": ocr_util.max_image_pixels(),
        "cors_locked": bool(os.getenv("PRAMAAN_CORS_ORIGINS", "").strip()),
        "ocr_available": ocr_util.tesseract_available_cached() and ocr_util.ocr_enabled(),
        # Availability, not accuracy: >1 configured provider means live failover;
        # the deterministic rule engine is always the floor regardless.
        "llm_providers_configured": len(provider_chain()),
        "llm_failover_available": len(provider_chain()) > 1,
        "deterministic_fallback_available": True,
    }
# Private operational metrics are deliberately separate from public product
# benchmark metrics. An unset token keeps the route undiscoverable (404).
def metrics_token() -> str:
    return os.getenv("PRAMAAN_METRICS_TOKEN", "").strip()
