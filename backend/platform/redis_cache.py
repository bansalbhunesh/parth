"""Short-lived Redis cache and idempotency leases; never authoritative data."""

from __future__ import annotations

from typing import Any


class RedisCache:
    def __init__(self, client: Any, prefix: str = "pramaan") -> None:
        self._client = client
        self._prefix = prefix

    @classmethod
    def from_url(cls, url: str) -> "RedisCache":
        from redis import Redis

        return cls(
            Redis.from_url(
                url,
                decode_responses=False,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
        )

    def _key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def get(self, key: str) -> bytes | None:
        value = self._client.get(self._key(key))
        return bytes(value) if value is not None else None

    def set(self, key: str, value: bytes, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self._client.set(self._key(key), value, ex=ttl_seconds)

    def acquire(self, key: str, value: bytes, ttl_seconds: int) -> bool:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        return bool(self._client.set(self._key(key), value, ex=ttl_seconds, nx=True))
