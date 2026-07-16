"""Bounded LLM execution prevents timeout-driven queue and spend growth."""

import concurrent.futures

from backend import analyze

SPEC = "UPS battery runtime shall be 10 min at full load."
SUBMITTAL = "UPS battery runtime is 7 min at full load."


class _NoCapacity:
    def acquire(self, blocking=False):
        assert blocking is False
        return False


def test_saturated_llm_queue_degrades_without_submitting(monkeypatch):
    monkeypatch.setattr(analyze, "_LLM_CAPACITY", _NoCapacity())

    result = analyze.run_analysis(SPEC, SUBMITTAL, "UPS")

    assert result.mode == "deterministic"
    assert any(d["parameter"] == "battery_runtime_min" for d in result.deviations)


def test_timed_out_future_is_cancelled_before_fallback(monkeypatch):
    class TimedOutFuture:
        cancelled = False

        def result(self, timeout):
            assert timeout == analyze._LLM_TIMEOUT_S
            raise concurrent.futures.TimeoutError

        def cancel(self):
            self.cancelled = True
            return True

    future = TimedOutFuture()
    monkeypatch.setattr(analyze, "_submit_llm", lambda *_args, **_kwargs: future)

    result = analyze.run_analysis(SPEC, SUBMITTAL, "UPS")

    assert future.cancelled is True
    assert result.mode == "deterministic"


def test_timeout_before_submit_still_degrades(monkeypatch):
    """A TimeoutError raised before any future exists (capacity contention
    surfaced as a timeout) must fall back without touching a None future."""
    def raise_timeout(*_args, **_kwargs):
        raise concurrent.futures.TimeoutError

    monkeypatch.setattr(analyze, "_submit_llm", raise_timeout)

    result = analyze.run_analysis(SPEC, SUBMITTAL, "UPS")

    assert result.mode == "deterministic"


def test_vision_timeout_reports_unavailable(monkeypatch):
    class TimedOutFuture:
        cancelled = False

        def result(self, timeout):
            raise concurrent.futures.TimeoutError

        def cancel(self):
            self.cancelled = True
            return True

    future = TimedOutFuture()
    monkeypatch.setattr(analyze, "_submit_llm", lambda *_args, **_kwargs: future)

    result = analyze.run_vision_analysis(SPEC, b"not-an-image", "image/png", "UPS")

    assert future.cancelled is True
    assert result.mode == "vision-unavailable"
    assert result.deviations == []
    assert result.provider is None


def test_capacity_status_never_reports_negative_availability():
    status = analyze.llm_capacity_status()

    assert status["workers"] >= 1
    assert status["max_pending"] >= 0
    assert 0 <= status["available"] <= status["workers"] + status["max_pending"]
