"""The streaming analyze path carries the same LLM guards as the sync path.

Found by the 2026-07-16 audit: /analyze/stream called complete_stream directly,
bypassing both the bounded capacity pool and the wall-clock timeout — so
concurrent SSE requests could multiply provider spend without limit, and a
provider that stalled without erroring hung the SSE response forever. These
tests drive run_streaming_analysis / _stream_llm_bounded as plain generators
(no TestClient SSE), so they stay selected under the Mutmut replay.
"""

import concurrent.futures
import threading
import time

import pytest

from backend import analyze

SPEC = "**UPS-02** — battery runtime min: shall be **10 min**"
SUBMITTAL = "**UPS-02** — battery runtime min: **7 min**"


class _NoCapacity:
    def acquire(self, blocking=False):
        assert blocking is False
        return False


def test_stream_degrades_to_rule_floor_when_capacity_full(monkeypatch):
    monkeypatch.setattr(analyze, "_LLM_CAPACITY", _NoCapacity())

    events = "".join(analyze.run_streaming_analysis(SPEC, SUBMITTAL, "UPS"))

    assert '"mode": "deterministic"' in events
    assert "battery_runtime_min" in events
    assert "event: done" in events


def test_stream_capacity_error_raised_before_any_token(monkeypatch):
    monkeypatch.setattr(analyze, "_LLM_CAPACITY", _NoCapacity())

    with pytest.raises(analyze.LLMCapacityError):
        next(analyze._stream_llm_bounded("prompt", "system"))


def test_stream_times_out_instead_of_hanging(monkeypatch):
    started = threading.Event()

    def stalled_stream(prompt, system=""):
        started.set()
        yield "first "
        time.sleep(5)  # provider stalls without erroring
        yield "never delivered"

    monkeypatch.setattr("backend.llm.complete_stream", stalled_stream)

    chunks = []
    with pytest.raises(concurrent.futures.TimeoutError):
        for chunk in analyze._stream_llm_bounded("p", "s", timeout_s=0.3):
            chunks.append(chunk)

    assert started.is_set()
    assert chunks == ["first "]


def test_stream_timeout_falls_back_to_rule_floor(monkeypatch):
    def stalled_stream(prompt, system=""):
        time.sleep(5)
        yield "never delivered"

    monkeypatch.setattr("backend.llm.complete_stream", stalled_stream)
    monkeypatch.setattr(analyze, "_LLM_TIMEOUT_S", 0.3)

    events = "".join(analyze.run_streaming_analysis(SPEC, SUBMITTAL, "UPS"))

    assert '"mode": "deterministic"' in events
    assert "battery_runtime_min" in events
    assert "event: done" in events


def test_stream_worker_releases_capacity_permit(monkeypatch):
    def quick_stream(prompt, system=""):
        yield "token"

    monkeypatch.setattr("backend.llm.complete_stream", quick_stream)
    before = analyze.llm_capacity_status()["available"]

    assert list(analyze._stream_llm_bounded("p", "s", timeout_s=5)) == ["token"]

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if analyze.llm_capacity_status()["available"] == before:
            break
        time.sleep(0.01)
    assert analyze.llm_capacity_status()["available"] == before


def test_stream_provider_error_relayed_to_caller(monkeypatch):
    def failing_stream(prompt, system=""):
        raise RuntimeError("provider exploded")
        yield  # pragma: no cover — makes this a generator

    monkeypatch.setattr("backend.llm.complete_stream", failing_stream)

    with pytest.raises(RuntimeError, match="provider exploded"):
        list(analyze._stream_llm_bounded("p", "s", timeout_s=5))
