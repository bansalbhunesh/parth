import pytest

from backend.platform import webhook_delivery
from backend.platform.webhook_delivery import WebhookRetryPolicy, WebhookSignature, WebhookSigner

ACTIVE = "a" * 32
PREVIOUS = "b" * 32


def test_webhook_signature_binds_timestamp_and_body() -> None:
    signer = WebhookSigner(ACTIVE)
    signature = signer.sign(b'{"event":"finding.created"}', timestamp=1_000)
    assert signature.header.startswith("t=1000,v1=")
    assert signer.verify(b'{"event":"finding.created"}', signature, now=1_100)
    assert not signer.verify(b'{"event":"other"}', signature, now=1_100)


def test_rotated_secret_remains_verifiable_during_overlap() -> None:
    old_signature = WebhookSigner(PREVIOUS).sign(b"payload", timestamp=5_000)
    rotated = WebhookSigner(ACTIVE, (PREVIOUS,))
    assert rotated.verify(b"payload", old_signature, now=5_100)


def test_stale_and_malformed_signatures_fail() -> None:
    signer = WebhookSigner(ACTIVE)
    assert not signer.verify(b"payload", signer.sign(b"payload", timestamp=10), now=1_000)
    assert not signer.verify(b"payload", WebhookSignature(1_000, "invalid"), now=1_000)


def test_signer_payload_default_clock_and_tolerance_boundaries(monkeypatch) -> None:
    signer = WebhookSigner(ACTIVE)
    assert signer._payload(123, b"body") == b"123.body"

    monkeypatch.setattr(webhook_delivery.time, "time", lambda: 2_000.9)
    signature = signer.sign(b"payload")
    assert signature.timestamp == 2_000
    assert signer.verify(b"payload", signature)

    boundary = signer.sign(b"payload", timestamp=1_000)
    assert signer.verify(b"payload", boundary, now=1_300)
    assert not signer.verify(b"payload", boundary, now=1_301)


def test_signer_short_secret_error_is_stable() -> None:
    with pytest.raises(ValueError) as error:
        WebhookSigner("short")
    assert str(error.value) == "webhook secrets must contain at least 32 characters"


def test_retry_policy_is_bounded_exponential() -> None:
    policy = WebhookRetryPolicy(max_attempts=5, initial_delay_seconds=10, maximum_delay_seconds=25)
    assert [policy.delay(attempt) for attempt in range(1, 6)] == [10, 20, 25, 25, None]
