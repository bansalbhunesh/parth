"""Signed durable-webhook primitives with bounded retry scheduling."""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WebhookSignature:
    timestamp: int
    digest: str

    @property
    def header(self) -> str:
        return f"t={self.timestamp},v1={self.digest}"


class WebhookSigner:
    """Sign with the active secret and verify against active plus rotated secrets."""

    def __init__(self, active_secret: str, previous_secrets: tuple[str, ...] = ()) -> None:
        secrets = (active_secret, *previous_secrets)
        if any(len(secret) < 32 for secret in secrets):
            raise ValueError("webhook secrets must contain at least 32 characters")
        self._secrets = tuple(secret.encode() for secret in secrets)

    @staticmethod
    def _payload(timestamp: int, body: bytes) -> bytes:
        return str(timestamp).encode("ascii") + b"." + body

    def sign(self, body: bytes, timestamp: int | None = None) -> WebhookSignature:
        signed_at = int(time.time()) if timestamp is None else timestamp
        digest = hmac.new(self._secrets[0], self._payload(signed_at, body), hashlib.sha256).hexdigest()
        return WebhookSignature(signed_at, digest)

    def verify(self, body: bytes, signature: WebhookSignature, *, now: int | None = None, tolerance: int = 300) -> bool:
        current_time = int(time.time()) if now is None else now
        if abs(current_time - signature.timestamp) > tolerance:
            return False
        payload = self._payload(signature.timestamp, body)
        return any(
            hmac.compare_digest(hmac.new(secret, payload, hashlib.sha256).hexdigest(), signature.digest)
            for secret in self._secrets
        )


@dataclass(frozen=True, slots=True)
class WebhookRetryPolicy:
    max_attempts: int = 8
    initial_delay_seconds: int = 10
    maximum_delay_seconds: int = 3600

    def __post_init__(self) -> None:
        if min(self.max_attempts, self.initial_delay_seconds, self.maximum_delay_seconds) < 1:
            raise ValueError("webhook retry bounds must be positive")

    def delay(self, attempt: int) -> int | None:
        if attempt >= self.max_attempts:
            return None
        delay = int(self.initial_delay_seconds * (2 ** max(0, attempt - 1)))
        return min(delay, self.maximum_delay_seconds)
