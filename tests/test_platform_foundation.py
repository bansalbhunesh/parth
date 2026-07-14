from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import UTC, datetime

import pytest

from backend.platform.config import PlatformConfigurationError, PlatformSettings
from backend.platform.redis_limits import DistributedLimitUnavailable, RedisRateLimiter
from backend.platform.supabase_queue import SupabaseJobQueue


def test_production_configuration_rejects_every_local_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRAMAAN_ENV", "production")
    with pytest.raises(PlatformConfigurationError, match="production refuses local-only backends"):
        PlatformSettings.from_env()


def test_managed_configuration_requires_each_external_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRAMAAN_AUTH_BACKEND", "supabase")
    monkeypatch.setenv("PRAMAAN_CASE_BACKEND", "postgres")
    monkeypatch.setenv("PRAMAAN_QUEUE_BACKEND", "supabase")
    monkeypatch.setenv("PRAMAAN_CACHE_BACKEND", "redis")
    with pytest.raises(PlatformConfigurationError) as error:
        PlatformSettings.from_env()
    assert "DATABASE_URL" in str(error.value)
    assert "PRAMAAN_REDIS_URL" in str(error.value)
    assert "SUPABASE_URL" in str(error.value)


class FakeRedis:
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result or [1, 1, 1000]
        self.error = error
        self.calls = []

    def eval(self, *args):
        self.calls.append(args)
        if self.error:
            raise self.error
        return self.result


def test_redis_limiter_returns_remaining_capacity_without_storing_raw_identity() -> None:
    client = FakeRedis([1, 3, 9_999_999_999_999])
    decision = RedisRateLimiter(client).check("hashed-client", "analysis", 10, fail_closed=True)
    assert decision.allowed is True
    assert decision.remaining == 7
    assert "hashed-client" in client.calls[0][2]


def test_expensive_rate_limit_fails_closed_when_redis_is_down() -> None:
    limiter = RedisRateLimiter(FakeRedis(error=TimeoutError("down")))
    with pytest.raises(DistributedLimitUnavailable):
        limiter.check("client", "analysis", 10, fail_closed=True)
    assert limiter.check("client", "read", 10, fail_closed=False).degraded is True


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executions = []

    def execute(self, query, params):
        self.executions.append((query, params))

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakePool:
    def __init__(self, cursor):
        self._connection = FakeConnection(cursor)

    @contextmanager
    def connection(self):
        yield self._connection


def test_supabase_queue_uses_send_read_and_archive_not_destructive_pop() -> None:
    now = datetime.now(UTC)
    cursor = FakeCursor([(42, 1, now, now, json.dumps({"job_id": "job-1"}))])
    queue = SupabaseJobQueue(FakePool(cursor))
    messages = queue.read(visibility_seconds=60, batch_size=1)
    assert messages[0].payload == {"job_id": "job-1"}
    assert "pgmq.read" in cursor.executions[0][0]
    assert "pop" not in cursor.executions[0][0]

    cursor.rows = [(True,)]
    assert queue.archive(42) is True
    assert "pgmq.archive" in cursor.executions[-1][0]
