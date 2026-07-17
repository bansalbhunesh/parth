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
    def stalled_stream(prompt, system="", **kwargs):
        time.sleep(5)
        return []

    monkeypatch.setattr("backend.agents.reconciliation.complete_json", stalled_stream)
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


def test_stream_zero_timeout_raises_before_reading(monkeypatch):
    def quick_stream(prompt, system=""):
        yield "token"

    monkeypatch.setattr("backend.llm.complete_stream", quick_stream)

    with pytest.raises(concurrent.futures.TimeoutError):
        list(analyze._stream_llm_bounded("p", "s", timeout_s=0))


def test_abandoned_worker_stops_consuming_provider(monkeypatch):
    resume = threading.Event()
    consumed = []

    def slow_stream(prompt, system=""):
        yield "a"
        resume.wait(timeout=5)
        yield "b"
        consumed.append("b was pulled")  # runs only if the worker keeps iterating
        yield "c"

    monkeypatch.setattr("backend.llm.complete_stream", slow_stream)
    before = analyze.llm_capacity_status()["available"]

    stream = analyze._stream_llm_bounded("p", "s", timeout_s=5)
    assert next(stream) == "a"
    stream.close()  # consumer walks away -> abandoned flag set
    resume.set()

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if analyze.llm_capacity_status()["available"] == before:
            break
        time.sleep(0.01)
    assert analyze.llm_capacity_status()["available"] == before
    assert consumed == []  # the worker returned at the abandoned check


def test_streaming_success_path_reports_llm_mode_and_provenance(monkeypatch):
    import json

    import backend.llm as llm_mod

    payload = (
        '[{"component": "UPS-02", "parameter": "battery_runtime_min", '
        '"required_value": "10", "provided_value": "7", "unit": "min", '
        '"standard_ref": "DESIGN-BASIS", "spec_clause": "", '
        '"severity": "Critical", "rationale": "runtime below requirement"}]'
    )

    def json_stream(prompt, system="", **kwargs):
        import json
        return json.loads(payload)

    monkeypatch.setattr("backend.agents.reconciliation.complete_json", json_stream)
    monkeypatch.setitem(llm_mod.FAILOVER_STATUS, "last_successful_provider", "groq")

    events = "".join(analyze.run_streaming_analysis(SPEC, SUBMITTAL, "UPS"))

    assert "event: token" in events
    assert '"mode": "llm"' in events
    assert "battery_runtime_min" in events
    assert "event: done" in events
    # The streamed result carries the same provenance contract as /analyze:
    # the answering failover leg and a real LLM-segment timing, not placeholders.
    result_line = next(
        line for line in events.splitlines()
        if line.startswith("data: ") and "telemetry" in line
    )
    telemetry = json.loads(result_line[len("data: "):])["telemetry"]
    assert telemetry["provider"] == "groq"
    assert telemetry["llm_call_ms"] is not None
    assert telemetry["standards_load_ms"] >= 0


def test_streaming_fallback_reports_null_provenance(monkeypatch):
    import json

    def failing_stream(prompt, system="", **kwargs):
        from backend.llm import LLMError
        raise LLMError("no provider")

    monkeypatch.setattr("backend.agents.reconciliation.complete_json", failing_stream)

    events = "".join(analyze.run_streaming_analysis(SPEC, SUBMITTAL, "UPS"))

    result_line = next(
        line for line in events.splitlines()
        if line.startswith("data: ") and "telemetry" in line
    )
    telemetry = json.loads(result_line[len("data: "):])["telemetry"]
    assert telemetry["provider"] is None
    assert telemetry["llm_call_ms"] is None


def test_submit_failure_releases_capacity_permit(monkeypatch):
    class BrokenPool:
        def submit(self, *args, **kwargs):
            raise RuntimeError("pool is shut down")

    monkeypatch.setattr(analyze, "_LLM_POOL", BrokenPool())
    before = analyze.llm_capacity_status()["available"]

    with pytest.raises(RuntimeError, match="pool is shut down"):
        analyze._submit_llm(lambda: None)

    assert analyze.llm_capacity_status()["available"] == before
