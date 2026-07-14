"""Branch-complete tests for production boundary adapters."""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Request

from backend import security
from backend.http import RequestContextMiddleware, _safe_detail, problem_response, request_id_from_scope
from backend.platform import identity, readiness
from backend.platform.config import PlatformConfigurationError, PlatformSettings
from backend.platform.contracts import Principal
from backend.platform.redis_limits import DistributedLimitUnavailable, RateLimitDecision, RedisRateLimiter
from backend.platform.supabase_queue import SupabaseJobQueue


def _settings(**changes) -> PlatformSettings:
    values = {
        "environment": "local",
        "auth_backend": "supabase",
        "case_backend": "sqlite",
        "queue_backend": "memory",
        "cache_backend": "memory",
        "database_url": None,
        "redis_url": None,
        "supabase_url": "https://tenant.supabase.co",
        "supabase_jwt_audience": "authenticated",
    }
    values.update(changes)
    return PlatformSettings(**values)


def _request(path: str = "/api/v1/test", authorization: str = "") -> Request:
    headers = [(b"authorization", authorization.encode())] if authorization else []
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": headers,
            "client": ("127.0.0.1", 1000),
            "server": ("testserver", 80),
        }
    )


def test_request_id_scope_and_problem_defaults() -> None:
    scope: dict = {}
    generated = request_id_from_scope(scope)
    assert request_id_from_scope(scope) == generated
    request = _request()
    response = problem_response(request, status_code=418, detail="No tea", errors=[{"field": "cup"}])
    body = json.loads(response.body)
    assert body["code"] == "request_failed"
    assert body["errors"] == [{"field": "cup"}]
    assert len(body["request_id"]) == 32
    assert _safe_detail({"unsafe": "detail"}, 400) == "The request could not be completed."
    assert _safe_detail("secret dependency detail", 500) == "The service could not complete this request."


def test_platform_choice_and_identity_require_valid_configuration(monkeypatch) -> None:
    monkeypatch.setenv("PRAMAAN_ENV", "invalid")
    with pytest.raises(PlatformConfigurationError, match="must be one of"):
        PlatformSettings.from_env()
    with pytest.raises(identity.IdentityVerificationError, match="SUPABASE_URL"):
        identity.SupabaseIdentityProvider.from_settings(_settings(supabase_url=None))
    monkeypatch.setenv("PRAMAAN_ENV", "local")
    monkeypatch.setenv("PRAMAAN_RAW_UPLOAD_RETENTION_DAYS", "forever")
    with pytest.raises(PlatformConfigurationError, match="must be an integer"):
        PlatformSettings.from_env()


def test_platform_retention_bounds_are_enforced() -> None:
    with pytest.raises(PlatformConfigurationError, match="RAW_UPLOAD"):
        _settings(raw_upload_retention_days=0).validate()
    with pytest.raises(PlatformConfigurationError, match="AUDIT_RETENTION"):
        _settings(audit_retention_days=10).validate()


@pytest.mark.asyncio
async def test_request_context_passes_non_http_scopes_through() -> None:
    observed = []

    async def downstream(scope, receive, send):  # noqa: ANN001
        observed.append(scope["type"])

    async def noop():
        return {}

    await RequestContextMiddleware(downstream)({"type": "lifespan"}, noop, noop)
    assert observed == ["lifespan"]


def test_identity_provider_builds_jwks_client_and_validates_claims(monkeypatch) -> None:
    created = {}

    class FakeJwkClient:
        def __init__(self, url, **kwargs):
            created.update(url=url, **kwargs)

        def get_signing_key_from_jwt(self, token):
            assert token == "signed-token"
            return SimpleNamespace(key="public-key")

    monkeypatch.setattr("jwt.PyJWKClient", FakeJwkClient)
    monkeypatch.setattr(
        "jwt.decode",
        lambda *args, **kwargs: {
            "sub": "user-1",
            "role": "authenticated",
            "session_id": "session-1",
            "aal": "aal2",
            "is_anonymous": False,
        },
    )
    provider = identity.SupabaseIdentityProvider.from_settings(_settings())
    principal = provider.verify("signed-token")
    assert created["url"].endswith("/auth/v1/.well-known/jwks.json")
    assert created["lifespan"] == 600
    assert principal == Principal("user-1", "session-1", "aal2", False)


@pytest.mark.parametrize(
    "claims, message",
    [
        ({"sub": "", "role": "authenticated"}, "no subject"),
        ({"sub": "user-1", "role": "anon"}, "not an authenticated-user"),
    ],
)
def test_identity_provider_rejects_unsafe_claims(monkeypatch, claims, message) -> None:
    client = SimpleNamespace(get_signing_key_from_jwt=lambda _token: SimpleNamespace(key="key"))
    monkeypatch.setattr("jwt.decode", lambda *args, **kwargs: claims)
    provider = identity.SupabaseIdentityProvider("issuer", "audience", client)
    with pytest.raises(identity.IdentityVerificationError, match=message):
        provider.verify("token")


def test_identity_provider_wraps_signature_failures(monkeypatch) -> None:
    client = SimpleNamespace(get_signing_key_from_jwt=lambda _token: (_ for _ in ()).throw(ValueError("bad")))
    provider = identity.SupabaseIdentityProvider("issuer", "audience", client)
    with pytest.raises(identity.IdentityVerificationError, match="verification failed"):
        provider.verify("token")


def test_identity_dependency_modes_and_anonymous_rejection(monkeypatch) -> None:
    monkeypatch.setattr(identity, "get_platform_settings", lambda: _settings(auth_backend="demo"))
    with pytest.raises(HTTPException) as unconfigured:
        identity.require_supabase_identity(_request(authorization="Bearer token"))
    assert unconfigured.value.status_code == 503

    monkeypatch.setattr(identity, "get_platform_settings", lambda: _settings())
    with pytest.raises(HTTPException) as missing:
        identity.bearer_token(_request())
    assert missing.value.status_code == 401

    anonymous = Principal("user-1", None, None, True)
    monkeypatch.setattr(identity, "get_identity_provider", lambda: SimpleNamespace(verify=lambda _token: anonymous))
    with pytest.raises(HTTPException) as rejected:
        identity.require_supabase_identity(_request(authorization="Bearer token"))
    assert rejected.value.status_code == 403

    permanent = Principal("user-1", None, "aal1", False)
    monkeypatch.setattr(identity, "get_identity_provider", lambda: SimpleNamespace(verify=lambda _token: permanent))
    request = _request(authorization="bearer token")
    assert identity.require_supabase_identity(request) == permanent
    assert request.state.principal == permanent


def test_identity_dependency_normalizes_verification_failure(monkeypatch) -> None:
    monkeypatch.setattr(identity, "get_platform_settings", lambda: _settings())
    monkeypatch.setattr(
        identity,
        "get_identity_provider",
        lambda: SimpleNamespace(
            verify=lambda _token: (_ for _ in ()).throw(identity.IdentityVerificationError("secret detail"))
        ),
    )
    with pytest.raises(HTTPException) as rejected:
        identity.require_supabase_identity(_request(authorization="Bearer token"))
    assert rejected.value.status_code == 401
    assert "secret detail" not in rejected.value.detail


class _Cursor:
    def __init__(self, rows=None):
        self.rows = rows or [(1,)]
        self.executions = []

    def execute(self, query, params=None):
        self.executions.append((query, params))

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Connection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Pool:
    def __init__(self, cursor):
        self.cursor = cursor

    @contextmanager
    def connection(self):
        yield _Connection(self.cursor)


def test_bounded_readiness_probes_success_and_failure(monkeypatch) -> None:
    cursor = _Cursor()
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=lambda *_a, **_kw: _Connection(cursor)))
    assert readiness._postgres_ready("postgresql://db") == (True, "ok")
    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=lambda *_a, **_kw: (_ for _ in ()).throw(TimeoutError())),
    )
    assert readiness._postgres_ready("postgresql://db") == (False, "unavailable")

    closed = []
    redis_client = SimpleNamespace(ping=lambda: True, close=lambda: closed.append(True))
    redis_type = SimpleNamespace(from_url=lambda *_a, **_kw: redis_client)
    monkeypatch.setitem(sys.modules, "redis", SimpleNamespace(Redis=redis_type))
    assert readiness._redis_ready("redis://cache") == (True, "ok")
    assert closed == [True]
    redis_type.from_url = lambda *_a, **_kw: (_ for _ in ()).throw(TimeoutError())
    assert readiness._redis_ready("redis://cache") == (False, "unavailable")


def test_readiness_report_combines_managed_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(readiness, "_postgres_ready", lambda _url: (True, "ok"))
    monkeypatch.setattr(readiness, "_redis_ready", lambda _url: (False, "unavailable"))
    ready, report = readiness.readiness_report(
        _settings(
            case_backend="postgres",
            queue_backend="supabase",
            cache_backend="redis",
            database_url="db",
            redis_url="r",
        )
    )
    assert ready is False
    assert report["status"] == "not_ready"
    assert report["checks"]["redis"]["status"] == "unavailable"


def test_supabase_queue_all_paths(monkeypatch) -> None:
    made = {}

    class PoolFactory:
        def __init__(self, url, **kwargs):
            made.update(url=url, **kwargs)

    monkeypatch.setitem(sys.modules, "psycopg_pool", SimpleNamespace(ConnectionPool=PoolFactory))
    created = SupabaseJobQueue.from_database_url("postgresql://db")
    assert isinstance(created, SupabaseJobQueue)
    assert made == {"url": "postgresql://db", "min_size": 1, "max_size": 5, "open": True}

    cursor = _Cursor([(77,)])
    queue = SupabaseJobQueue(_Pool(cursor))
    assert queue.enqueue({"case_id": "case-1"}, delay_seconds=5) == 77
    cursor.rows = []
    with pytest.raises(RuntimeError, match="message id"):
        queue.enqueue({"case_id": "case-1"})

    now = datetime.now(UTC)
    cursor.rows = [(7, 2, now.isoformat(), now.isoformat(), {"job_id": "job-1"})]
    message = queue.read(60)[0]
    assert message.enqueued_at == now
    assert message.payload == {"job_id": "job-1"}
    cursor.rows = []
    assert queue.archive(7) is False


def test_distributed_security_limit_allowed_denied_and_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("PRAMAAN_RATE_LIMIT_ENABLED", "1")
    monkeypatch.setenv("PRAMAAN_REDIS_URL", "redis://cache")
    allowed = SimpleNamespace(check=lambda *_a, **_kw: RateLimitDecision(True, 1, 9_999_999_999_999))
    monkeypatch.setattr(security, "_distributed_limiter", lambda: allowed)
    security.enforce_rate_limit(_request(), "analysis", 2)

    denied = SimpleNamespace(check=lambda *_a, **_kw: RateLimitDecision(False, 0, 9_999_999_999_999))
    monkeypatch.setattr(security, "_distributed_limiter", lambda: denied)
    with pytest.raises(HTTPException) as rate_limited:
        security.enforce_rate_limit(_request(), "analysis", 2)
    assert rate_limited.value.status_code == 429

    unavailable = SimpleNamespace(
        check=lambda *_a, **_kw: (_ for _ in ()).throw(DistributedLimitUnavailable("down"))
    )
    monkeypatch.setattr(security, "_distributed_limiter", lambda: unavailable)
    with pytest.raises(HTTPException) as failed_closed:
        security.enforce_rate_limit(_request(), "analysis", 2)
    assert failed_closed.value.status_code == 503


def test_distributed_limiter_is_cached_per_url(monkeypatch) -> None:
    built = []
    monkeypatch.setenv("PRAMAAN_REDIS_URL", "redis://one")
    monkeypatch.setattr(RedisRateLimiter, "from_url", lambda url: built.append(url) or object())
    security.reset_rate_limits()
    first = security._distributed_limiter()
    assert security._distributed_limiter() is first
    monkeypatch.setenv("PRAMAAN_REDIS_URL", "redis://two")
    assert security._distributed_limiter() is not first
    assert built == ["redis://one", "redis://two"]


def test_redis_limiter_factory_uses_bounded_socket_timeouts(monkeypatch) -> None:
    calls = {}

    class RedisFactory:
        @staticmethod
        def from_url(url, **kwargs):
            calls.update(url=url, **kwargs)
            return object()

    monkeypatch.setitem(sys.modules, "redis", SimpleNamespace(Redis=RedisFactory))
    limiter = RedisRateLimiter.from_url("redis://cache")
    assert isinstance(limiter, RedisRateLimiter)
    assert calls == {
        "url": "redis://cache",
        "decode_responses": False,
        "socket_connect_timeout": 1,
        "socket_timeout": 1,
    }
