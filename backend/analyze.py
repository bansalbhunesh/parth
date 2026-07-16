"""Shared analysis logic — used by all /analyze endpoints."""

import concurrent.futures
import json
import logging
import os
import threading
import time
from typing import NamedTuple

from backend.agents.decision import decision_blocks
from backend.agents.reconciliation import (
    SYSTEM_PROMPT,
    _all_standards_text,
    _check_citation_faithfulness,
    _ground_findings,
    _validate_deviations,
    build_reconciliation_prompt,
)

# The deterministic rule floor lives in backend.rule_engine; these names stay
# importable from backend.analyze for existing tests, eval harnesses, and the
# frozen benchmark scripts.
from backend.rule_engine import (  # noqa: F401 — compatibility re-exports
    _deterministic_compare,
    _enrich_cx,
    _freeform_compare,
    _norm_val,
    _resilient_fallback,
)

log = logging.getLogger("pramaan.analyze")

# Hard ceiling on how long the live /analyze path waits for the LLM before it
# degrades to the instant rule-based detector. Free-tier models can 503-retry
# for 40s+; a judge will not wait. Tune with PRAMAAN_LLM_TIMEOUT (seconds).
_LLM_TIMEOUT_S = float(os.getenv("PRAMAAN_LLM_TIMEOUT", "60"))

_LLM_MAX_WORKERS = max(1, int(os.getenv("PRAMAAN_LLM_MAX_WORKERS", "4")))
_LLM_MAX_PENDING = max(0, int(os.getenv("PRAMAAN_LLM_MAX_PENDING", "2")))

# Module-level pool so a timed-out call is abandoned (left to finish in the
# background) rather than blocking the response — a `with` executor would wait
# for the worker on exit and defeat the timeout.
_LLM_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=_LLM_MAX_WORKERS)
_LLM_CAPACITY = threading.BoundedSemaphore(_LLM_MAX_WORKERS + _LLM_MAX_PENDING)
_LLM_STATE_LOCK = threading.Lock()
_LLM_INFLIGHT = 0


class LLMCapacityError(RuntimeError):
    """The bounded LLM queue is full; callers should degrade immediately."""


def _run_with_capacity(fn, args, kwargs):
    global _LLM_INFLIGHT
    try:
        return fn(*args, **kwargs)
    finally:
        with _LLM_STATE_LOCK:
            _LLM_INFLIGHT -= 1
        _LLM_CAPACITY.release()


def _submit_llm(fn, *args, **kwargs):
    """Submit LLM work only when a bounded worker/queue slot is available.

    A timed-out provider call may still be running inside its HTTP client. The
    capacity permit is therefore released by the worker, not by the waiting
    request. Repeated timeouts can no longer create an unbounded executor queue
    or silently multiply provider spend.
    """
    global _LLM_INFLIGHT
    if not _LLM_CAPACITY.acquire(blocking=False):
        raise LLMCapacityError("LLM analysis capacity is currently full")
    with _LLM_STATE_LOCK:
        _LLM_INFLIGHT += 1
    try:
        return _LLM_POOL.submit(_run_with_capacity, fn, args, kwargs)
    except Exception:
        with _LLM_STATE_LOCK:
            _LLM_INFLIGHT -= 1
        _LLM_CAPACITY.release()
        raise


def llm_capacity_status() -> dict:
    with _LLM_STATE_LOCK:
        inflight = _LLM_INFLIGHT
    capacity = _LLM_MAX_WORKERS + _LLM_MAX_PENDING
    return {
        "workers": _LLM_MAX_WORKERS,
        "max_pending": _LLM_MAX_PENDING,
        "inflight": inflight,
        "available": max(0, capacity - inflight),
    }


class AnalysisResult(NamedTuple):
    deviations: list[dict]
    mode: str
    elapsed_ms: int
    standards_load_ms: int = 0
    llm_call_ms: int | None = None
    postprocess_ms: int = 0
    provider: str | None = None


def run_deterministic_analysis(
    spec_text: str,
    submittal_text: str,
    system_id: str = "CUSTOM",
) -> AnalysisResult:
    """Run the bounded rule engine without provider access or persistence."""
    started = time.perf_counter()
    deviations = _resilient_fallback(spec_text, submittal_text, system_id)
    return AnalysisResult(
        deviations=deviations,
        mode="rule-based-deterministic",
        elapsed_ms=round((time.perf_counter() - started) * 1000),
        provider=None,
    )


def run_analysis(
    spec_text: str,
    submittal_text: str,
    system_id: str = "CUSTOM",
) -> AnalysisResult:
    t0 = time.time()
    standards = _all_standards_text(max_chars_per=1800)
    prompt = build_reconciliation_prompt(spec_text, submittal_text, standards)
    standards_load_ms = round((time.time() - t0) * 1000)
    llm_call_ms = None
    provider = None
    t_llm = time.time()
    future = None
    try:
        from backend import llm as llm_module
        from backend.llm import complete_json
        # Bound the wait: a free-tier model that 503-retries for 40s+ would
        # otherwise hang the demo. A timed-out call is abandoned (left running)
        # and we degrade to the instant rule-based detector.
        future = _submit_llm(complete_json, prompt, SYSTEM_PROMPT)
        raw = future.result(timeout=_LLM_TIMEOUT_S)
        llm_call_ms = round((time.time() - t_llm) * 1000)
        provider = llm_module.FAILOVER_STATUS.get("last_successful_provider")
        t_post = time.time()
        devs = _validate_deviations(raw)
        devs = _check_citation_faithfulness(devs, spec_text, submittal_text, standards)
        devs = _ground_findings(devs, spec_text)  # drop hallucinated requirements
        for d in devs:
            _enrich_cx(d, system_id)  # rule-table only — no extra LLM calls
        mode = "llm"
        postprocess_ms = round((time.time() - t_post) * 1000)
    except concurrent.futures.TimeoutError:
        if future is not None:
            future.cancel()
        log.warning("LLM analysis exceeded %.0fs, using rule-based fallback",
                    _LLM_TIMEOUT_S)
        devs = _resilient_fallback(spec_text, submittal_text, system_id)
        mode = "deterministic"
        postprocess_ms = 0
    except Exception as exc:
        log.warning("LLM analysis failed, running rule-based fallback: %s", exc)
        devs = _resilient_fallback(spec_text, submittal_text, system_id)
        mode = "deterministic"
        postprocess_ms = 0
    elapsed = round((time.time() - t0) * 1000)
    return AnalysisResult(
        deviations=devs, mode=mode, elapsed_ms=elapsed,
        standards_load_ms=standards_load_ms, llm_call_ms=llm_call_ms,
        postprocess_ms=postprocess_ms, provider=provider,
    )


_VISION_PROMPT = """You are given a design specification (text) and a vendor
submittal supplied AS AN IMAGE (a datasheet page, table, or drawing). Read the
values directly from the image — do not assume a text transcript exists.

Cross-reference every specified requirement against the values visible in the
image and against the governing standards. Report each genuine deviation.

=== DESIGN SPECIFICATION ===
{spec}

=== GOVERNING STANDARDS ===
{standards}

The vendor submittal is the attached image. Return a JSON array of deviations,
each: component, parameter, required_value, provided_value, unit, standard_ref,
spec_clause, severity (Critical/Major/Minor), rationale. Only real deviations;
if a visible value meets or exceeds the requirement, do not flag it.
"""


def run_vision_analysis(
    spec_text: str,
    image_bytes: bytes,
    mime_type: str,
    system_id: str = "CUSTOM",
) -> AnalysisResult:
    """Reconcile a text spec against an image via the configured multimodal
    provider (not OCR→text). Failures return mode='vision-unavailable' with no
    findings, allowing callers to use the text/OCR path."""
    t0 = time.time()
    standards = _all_standards_text(max_chars_per=1800)
    prompt = _VISION_PROMPT.format(spec=spec_text, standards=standards)
    future = None
    provider = None
    try:
        from backend.llm import _extract_json, complete_vision
        provider = "openai" if (
            os.getenv("PRAMAAN_LLM", "gemini") == "openai"
            and os.environ.get("OPENAI_API_KEY")) else "gemini"
        future = _submit_llm(
            lambda: _extract_json(complete_vision(prompt, image_bytes, mime_type, SYSTEM_PROMPT))
        )
        raw = future.result(timeout=_LLM_TIMEOUT_S)
        devs = _validate_deviations(raw)
        devs = _ground_findings(devs, spec_text)  # drop hallucinated requirements
        for d in devs:
            _enrich_cx(d, system_id)
        mode = "vision"
    except concurrent.futures.TimeoutError:
        if future is not None:
            future.cancel()
        log.warning("Vision analysis exceeded %.0fs", _LLM_TIMEOUT_S)
        devs, mode, provider = [], "vision-unavailable", None
    except Exception as exc:
        log.warning("Vision analysis failed: %s", exc)
        devs, mode, provider = [], "vision-unavailable", None
    elapsed = round((time.time() - t0) * 1000)
    return AnalysisResult(
        deviations=devs, mode=mode, elapsed_ms=elapsed, provider=provider,
    )


def run_streaming_analysis(
    spec_text: str,
    submittal_text: str,
    system_id: str = "CUSTOM",
):
    t0 = time.time()
    standards = _all_standards_text(max_chars_per=1800)
    prompt = build_reconciliation_prompt(spec_text, submittal_text, standards)

    yield "event: status\ndata: Running AI reconciliation engine...\n\n"
    try:
        from backend.llm import _extract_json
        from backend.llm import complete_stream as llm_stream
        full_text = ""
        for chunk in llm_stream(prompt, system=SYSTEM_PROMPT):
            full_text += chunk
            yield f"event: token\ndata: {json.dumps(chunk)}\n\n"

        yield "event: status\ndata: Validating deviations...\n\n"
        raw = _extract_json(full_text)
        devs = _validate_deviations(raw)
        devs = _check_citation_faithfulness(devs, spec_text, submittal_text, standards)
        devs = _ground_findings(devs, spec_text)  # drop hallucinated requirements
        for d in devs:
            _enrich_cx(d, system_id)  # rule-table only — no extra LLM calls
        mode = "llm"
    except Exception as exc:
        log.warning("LLM stream analysis failed, rule-based fallback: %s", exc)
        yield "event: status\ndata: AI engine unavailable — running rule-based detector...\n\n"
        devs = _resilient_fallback(spec_text, submittal_text, system_id)
        mode = "deterministic"

    elapsed = round((time.time() - t0) * 1000)
    result = {
        "system": system_id,
        "deviations": devs,
        "count": len(devs),
        **decision_blocks(devs),
        "mode": mode,
        "elapsed_ms": elapsed,
        "telemetry": {
            "total_ms": elapsed,
            "llm_call_ms": elapsed,  # Stream doesn't currently time segments separately
            "standards_load_ms": 0,
            "postprocess_ms": 0,
            "provider": None,
        }
    }
    yield f"event: result\ndata: {json.dumps(result)}\n\n"
    yield "event: done\ndata: {}\n\n"
