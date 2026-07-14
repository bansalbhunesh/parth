"""Private storage, Redis cache, and durable worker contract tests."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from backend.platform.contracts import QueueMessage
from backend.platform.durable_worker import DurableWorker, WorkerBatchResult
from backend.platform.redis_cache import RedisCache
from backend.platform.storage import (
    PostgresMembershipAuthorizer,
    StorageAuthorizationError,
    StorageSigningError,
    SupabaseDocumentStorage,
)

ORG = "11111111-1111-4111-8111-111111111111"
CASE = "22222222-2222-4222-8222-222222222222"
USER = "33333333-3333-4333-8333-333333333333"


class FakeAuthorizer:
    def __init__(self, *, read: bool = True, write: bool = True) -> None:
        self.read = read
        self.write = write
        self.calls = []

    def can_read(self, organization_id, case_id, user_id):  # noqa: ANN001
        self.calls.append(("read", organization_id, case_id, user_id))
        return self.read

    def can_write(self, organization_id, case_id, user_id):  # noqa: ANN001
        self.calls.append(("write", organization_id, case_id, user_id))
        return self.write


class FakeBucket:
    def __init__(self) -> None:
        self.upload_result = {"token": "upload-token", "signedURL": "https://storage/upload"}
        self.download_result = {"signed_url": "https://storage/download"}
        self.calls = []

    def create_signed_upload_url(self, path):  # noqa: ANN001
        self.calls.append(("upload", path))
        return self.upload_result

    def create_signed_url(self, path, expires):  # noqa: ANN001
        self.calls.append(("download", path, expires))
        return self.download_result


def _storage(authorizer: FakeAuthorizer | None = None):
    bucket = FakeBucket()
    client = SimpleNamespace(from_=lambda name: bucket if name == "case-documents" else None)
    return SupabaseDocumentStorage(client, authorizer or FakeAuthorizer()), bucket


def test_upload_signing_uses_authorized_random_case_path() -> None:
    storage, bucket = _storage()
    signed = storage.signed_upload_url(ORG, CASE, USER, "../unsafe proposal (rev A).pdf")
    assert signed["token"] == "upload-token"
    assert signed["signed_url"] == "https://storage/upload"
    assert signed["path"].startswith(f"{ORG}/{CASE}/")
    assert signed["path"].endswith("/unsafe-proposal-rev-A-.pdf")
    assert ".." not in signed["path"]
    assert bucket.calls == [("upload", signed["path"])]


def test_upload_signing_rejects_unauthorized_or_invalid_input() -> None:
    denied, _ = _storage(FakeAuthorizer(write=False))
    with pytest.raises(StorageAuthorizationError):
        denied.signed_upload_url(ORG, CASE, USER, "document.pdf")
    allowed, bucket = _storage()
    with pytest.raises(ValueError, match="organization_id"):
        allowed.signed_upload_url("not-a-uuid", CASE, USER, "document.pdf")
    with pytest.raises(ValueError, match="filename"):
        allowed.signed_upload_url(ORG, CASE, USER, "...")
    bucket.upload_result = {"token": ""}
    with pytest.raises(StorageSigningError):
        allowed.signed_upload_url(ORG, CASE, USER, "document.pdf")


def test_download_signing_is_case_scoped_and_short_lived() -> None:
    storage, bucket = _storage()
    path = f"{ORG}/{CASE}/44444444-4444-4444-8444-444444444444/document.pdf"
    assert storage.signed_download_url(ORG, CASE, USER, path, 60) == "https://storage/download"
    assert bucket.calls[-1] == ("download", path, 60)
    with pytest.raises(StorageAuthorizationError, match="outside"):
        storage.signed_download_url(ORG, CASE, USER, f"{ORG}/other/document.pdf")
    with pytest.raises(ValueError, match="between 30 and 900"):
        storage.signed_download_url(ORG, CASE, USER, path, 901)

    denied, _ = _storage(FakeAuthorizer(read=False))
    with pytest.raises(StorageAuthorizationError, match="read"):
        denied.signed_download_url(ORG, CASE, USER, path)
    bucket.download_result = {}
    with pytest.raises(StorageSigningError):
        storage.signed_download_url(ORG, CASE, USER, path)


class FakeCursor:
    def __init__(self, row=(1,)) -> None:
        self.row = row
        self.executions = []

    def execute(self, query, params):
        self.executions.append((query, params))

    def fetchone(self):
        return self.row

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakePool:
    def __init__(self, cursor) -> None:
        self.cursor = cursor

    @contextmanager
    def connection(self):
        yield SimpleNamespace(cursor=lambda: self.cursor)


def test_postgres_authorizer_checks_case_membership_and_roles() -> None:
    cursor = FakeCursor()
    authorizer = PostgresMembershipAuthorizer(FakePool(cursor))
    assert authorizer.can_read(ORG, CASE, USER) is True
    query, params = cursor.executions[-1]
    assert "join public.cases" in query
    assert "deleted_at is null" in query
    assert params == [ORG, CASE, USER]
    assert authorizer.can_write(ORG, CASE, USER) is True
    assert cursor.executions[-1][1][-1] == ["owner", "engineer"]
    cursor.row = None
    assert authorizer.can_read(ORG, CASE, USER) is False


class FakeRedis:
    def __init__(self) -> None:
        self.values = {}
        self.calls = []

    def get(self, key):  # noqa: ANN001
        self.calls.append(("get", key))
        return self.values.get(key)

    def set(self, key, value, **kwargs):  # noqa: ANN001
        self.calls.append(("set", key, value, kwargs))
        if kwargs.get("nx") and key in self.values:
            return False
        self.values[key] = value
        return True


def test_redis_cache_is_ttl_bounded_and_supports_idempotency_leases(monkeypatch) -> None:
    client = FakeRedis()
    cache = RedisCache(client, prefix="test")
    assert cache.get("missing") is None
    cache.set("result", b"value", 10)
    assert cache.get("result") == b"value"
    assert cache.acquire("lock", b"owner", 5) is True
    assert cache.acquire("lock", b"other", 5) is False
    with pytest.raises(ValueError, match="positive"):
        cache.set("bad", b"value", 0)
    with pytest.raises(ValueError, match="positive"):
        cache.acquire("bad", b"value", 0)

    calls = {}

    class RedisFactory:
        @staticmethod
        def from_url(url, **kwargs):
            calls.update(url=url, **kwargs)
            return client

    monkeypatch.setitem(sys.modules, "redis", SimpleNamespace(Redis=RedisFactory))
    assert isinstance(RedisCache.from_url("redis://cache"), RedisCache)
    assert calls["socket_timeout"] == 1


class FakeQueue:
    def __init__(self, messages=(), archive_result=True) -> None:
        self.messages = list(messages)
        self.archive_result = archive_result
        self.read_calls = []
        self.archived = []
        self.enqueued = []

    def read(self, visibility_seconds, batch_size=1):  # noqa: ANN001
        self.read_calls.append((visibility_seconds, batch_size))
        return list(self.messages)

    def archive(self, message_id):  # noqa: ANN001
        self.archived.append(message_id)
        return self.archive_result

    def enqueue(self, payload, delay_seconds=0):  # noqa: ANN001
        self.enqueued.append((payload, delay_seconds))
        return len(self.enqueued)


def _message(message_id: int, read_count: int) -> QueueMessage:
    now = datetime.now(UTC)
    return QueueMessage(message_id, read_count, now, now, {"job_id": f"job-{message_id}"})


def test_worker_archives_only_successful_messages_and_retries_failures() -> None:
    queue = FakeQueue([_message(1, 1), _message(2, 2)])
    dead = FakeQueue()

    def handler(payload):  # noqa: ANN001
        if payload["job_id"] == "job-2":
            raise RuntimeError("provider down")

    worker = DurableWorker(queue, dead, handler, visibility_seconds=45, max_attempts=3)
    assert worker.run_once(2) == WorkerBatchResult(completed=1, retrying=1, dead_lettered=0)
    assert queue.read_calls == [(45, 2)]
    assert queue.archived == [1]
    assert dead.enqueued == []


def test_worker_dead_letters_at_bound_and_checks_archive_results() -> None:
    message = _message(7, 3)
    queue = FakeQueue([message])
    dead = FakeQueue()
    worker = DurableWorker(queue, dead, lambda _payload: (_ for _ in ()).throw(RuntimeError()), max_attempts=3)
    assert worker.run_once() == WorkerBatchResult(dead_lettered=1)
    assert dead.enqueued[0][0]["source_message_id"] == 7
    assert queue.archived == [7]

    broken = DurableWorker(FakeQueue([_message(8, 1)], archive_result=False), dead, lambda _payload: None)
    with pytest.raises(RuntimeError, match="completed"):
        broken.run_once()
    with pytest.raises(ValueError, match="positive"):
        DurableWorker(queue, dead, lambda _payload: None, visibility_seconds=0)

    dead_archive = FakeQueue([_message(9, 5)], archive_result=False)
    broken_dead = DurableWorker(
        dead_archive,
        dead,
        lambda _payload: (_ for _ in ()).throw(RuntimeError()),
        max_attempts=2,
    )
    with pytest.raises(RuntimeError, match="dead-lettered"):
        broken_dead.run_once()
