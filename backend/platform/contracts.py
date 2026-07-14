"""Stable interfaces separating domain behavior from local/managed adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    session_id: str | None
    assurance_level: str | None
    is_anonymous: bool


class IdentityProvider(Protocol):
    def verify(self, token: str) -> Principal: ...


@dataclass(frozen=True, slots=True)
class QueueMessage:
    message_id: int
    read_count: int
    enqueued_at: datetime
    visible_at: datetime
    payload: Mapping[str, Any]


class JobQueue(Protocol):
    def enqueue(self, payload: Mapping[str, Any], delay_seconds: int = 0) -> int: ...

    def read(self, visibility_seconds: int, batch_size: int = 1) -> Sequence[QueueMessage]: ...

    def archive(self, message_id: int) -> bool: ...


class CacheStore(Protocol):
    def get(self, key: str) -> bytes | None: ...

    def set(self, key: str, value: bytes, ttl_seconds: int) -> None: ...

    def acquire(self, key: str, value: bytes, ttl_seconds: int) -> bool: ...


class DocumentStorage(Protocol):
    def signed_upload_url(
        self,
        organization_id: str,
        case_id: str,
        user_id: str,
        filename: str,
    ) -> dict[str, str]: ...

    def signed_download_url(
        self,
        organization_id: str,
        case_id: str,
        user_id: str,
        object_name: str,
        expires_in: int = 300,
    ) -> str: ...


class CaseRepository(Protocol):
    def create_case(self, name: str = "") -> tuple[str, str]: ...

    def verify_case(self, case_id: str, secret: str) -> bool: ...

    def case_summary(self, case_id: str) -> dict[str, Any] | None: ...

    def delete_case(self, case_id: str) -> bool: ...
