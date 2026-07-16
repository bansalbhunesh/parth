"""Shared analysis logic — used by all /analyze endpoints."""

import concurrent.futures
import json
import logging
import operator
import os
import re
import threading
import time
from typing import NamedTuple

from backend.agents import cx_graph
from backend.agents.commissioning import _RULES, predict_cx_impact
from backend.agents.decision import decision_blocks
from backend.agents.reconciliation import (
    SYSTEM_PROMPT,
    _all_standards_text,
    _check_citation_faithfulness,
    _ground_findings,
    _validate_deviations,
    build_reconciliation_prompt,
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


def _deterministic_compare(spec_text: str, submittal_text: str) -> list[dict]:
    spec_values: dict[tuple[str, str], tuple[str, str]] = {}
    for match in re.finditer(
        r'\*\*([A-Z][\w-]*)\*\*\s*[—–-]\s*([\w\s]+?):\s*(?:shall be\s*)?\*\*(\S+)\s*(\S*)\*\*',
        spec_text,
    ):
        component, param, value, unit = match.groups()
        param_key = param.strip().lower().replace(' ', '_')
        spec_values[(component, param_key)] = (value, unit.strip('()'))

    sub_values: dict[tuple[str, str], tuple[str, str]] = {}
    for match in re.finditer(
        r'\*\*([A-Z][\w-]*)\*\*\s*[—–-]\s*([\w\s]+?):\s*\*\*(\S+)\s*(\S*)\*\*',
        submittal_text,
    ):
        component, param, value, unit = match.groups()
        param_key = param.strip().lower().replace(' ', '_')
        sub_values[(component, param_key)] = (value, unit.strip('()'))

    devs = []
    for key, (req_val, unit) in spec_values.items():
        if key in sub_values:
            prov_val, _ = sub_values[key]
            if str(prov_val) != str(req_val):
                devs.append({
                    "component": key[0],
                    "parameter": key[1],
                    "required_value": req_val,
                    "provided_value": prov_val,
                    "unit": unit,
                    "standard_ref": "DESIGN-BASIS",
                    "spec_clause": "",
                    "severity": "Major",
                    "rationale": f"Provided value {prov_val} does not match required {req_val} {unit}",
                    "confidence": 0.7,
                    "cx_source": "deterministic",
                })
    return devs


# ── Free-form rule-based detector ────────────────────────────────────
# Used ONLY by the live /analyze fallback (never by the eval harness) so the
# product still catches the headline deviations from real, un-templated vendor
# prose when the LLM is unavailable (rate-limited / no key) — instead of
# silently returning zero. Conservative by design: it only fires on a confident
# numeric mismatch or an explicit omission of a value the spec constrains.
# direction: "min" provided<required is a deviation · "max" provided>required ·
#            "ne" any difference.
_FREEFORM_PARAMS = [
    dict(component="UPS-02", parameter="battery_runtime_min", severity="Critical",
         direction="min", unit_rx=r"(?:min|minute)", unit="min",
         kw=[r"battery\s+(?:autonomy|runtime)", r"autonomy", r"battery", r"runtime"]),
    dict(component="UPS-02", parameter="efficiency_pct", severity="Major",
         direction="min", unit_rx=r"(?:%|percent)", unit="%",
         kw=[r"(?:online|double[-\s]?conversion)[^.]{0,40}efficiency",
             r"efficiency[^.]{0,40}(?:online|double[-\s]?conversion)",
             r"efficiency"]),
    dict(component="UPS-02", parameter="input_thd_pct", severity="Major",
         direction="max", unit_rx=r"(?:%|percent)", unit="%",
         kw=[r"(?:input\s+)?(?:thd|harmonic\s+distortion)"]),
    dict(component="GEN-FUEL", parameter="onsite_fuel_hours", severity="Critical",
         direction="min", unit_rx=r"(?:h|hr|hour)", unit="h",
         kw=[r"fuel[^.]{0,30}(?:autonomy|hours|storage)", r"fuel\s+autonomy"]),
    dict(component="GEN-01", parameter="start_time_sec", severity="Critical",
         direction="max", unit_rx=r"(?:s|sec|second)", unit="s",
         kw=[r"start[^.]{0,20}time", r"start\s+time"]),
    dict(component="SWGR-MV", parameter="short_circuit_rating_ka", severity="Critical",
         direction="min", unit_rx=r"kA", unit="kA",
         kw=[r"(?:fault|short[-\s]?circuit)[^.]{0,30}rating",
             r"(?:fault|short[-\s]?circuit)"]),
    dict(component="COOL-LOOP", parameter="delta_t_c", severity="Major",
         direction="ne", unit_rx=r"(?:°?C|degrees?\s*C)", unit="C",
         kw=[r"delta[-\s]?t", r"temperature\s+(?:rise|difference)"]),
    dict(component="FLOOR", parameter="load_rating_kpa", severity="Critical",
         direction="min", unit_rx=r"kPa", unit="kPa",
         kw=[r"(?:floor\s+)?load[^.]{0,20}(?:rating|capacity)", r"load\s+rating"]),
    # Structural raised-floor concentrated (CISCA) load, expressed in lbf on real
    # access-floor datasheets (e.g. Tate ConCore 1250 = 1250 lbf design load).
    dict(component="FLOOR-01", parameter="concentrated_load_lbf", severity="Major",
         direction="min", unit_rx=r"lbf", unit="lbf",
         kw=[r"concentrated[^.]{0,20}load", r"point\s+load"]),
    # LV busbar trunking (busway) short-time withstand current Icw, in kA. Kept
    # distinct from SWGR-MV: busway datasheets say "short-time withstand current"
    # rather than "short-circuit rating" (e.g. Schneider Canalis KTA10 = 50 kA/1s).
    dict(component="BUSWAY-01", parameter="short_time_withstand_ka", severity="Critical",
         direction="min", unit_rx=r"kA", unit="kA",
         kw=[r"short[-\s]?time\s+withstand", r"withstand\s+current"]),
]

_OMISSION_RX = re.compile(
    r"(not\s+stated|upon\s+request|available\s+on\s+request|\bn/?a\b|\btbd\b|"
    r"to\s+be\s+(?:advised|confirmed)|\bpending\b)", re.I)


def _num_near(text: str, kw: str, unit_rx: str, window: int = 50):
    """First number+unit AFTER the keyword (preferred), else BEFORE it."""
    fwd = re.search(kw + r"[^.]{0,%d}?(\d+(?:\.\d+)?)\s*%s" % (window, unit_rx),
                    text, re.I)
    if fwd:
        return float(fwd.group(1))
    bwd = re.search(r"(\d+(?:\.\d+)?)\s*%s[^.]{0,%d}?%s" % (unit_rx, window, kw),
                    text, re.I)
    if bwd:
        return float(bwd.group(1))
    return None


def _omission_near(text: str, kw: str) -> bool:
    m = re.search(kw + r"[^.]{0,60}", text, re.I)
    return bool(m and _OMISSION_RX.search(m.group(0)))


def _fmt_num(x: float) -> str:
    return str(int(x)) if x == int(x) else str(x)


_DEVIATES = {"min": operator.lt, "max": operator.gt, "ne": operator.ne}


def _parameter_value(text: str, parameter: dict) -> float | None:
    for keyword in parameter["kw"]:
        value = _num_near(text, keyword, parameter["unit_rx"])
        if value is not None:
            return value
    return None


def _omitted_value(parameter: dict, submittal_text: str) -> tuple[str, str] | None:
    if not any(_omission_near(submittal_text, keyword) for keyword in parameter["kw"]):
        return None
    return "Not stated", f"Spec requires {parameter['parameter']} but the submittal omits it"


def _freeform_deviation(parameter: dict, spec_text: str, submittal_text: str) -> dict | None:
    required = _parameter_value(spec_text, parameter)
    if required is None:
        return None
    provided = _parameter_value(submittal_text, parameter)
    if provided is None:
        omitted = _omitted_value(parameter, submittal_text)
        if omitted is None:
            return None
        provided_label, rationale = omitted
    else:
        if not _DEVIATES[parameter["direction"]](provided, required):
            return None
        provided_label = _fmt_num(provided)
        rationale = (
            f"Provided {provided_label} {parameter['unit']} does not satisfy "
            f"required {_fmt_num(required)} {parameter['unit']}"
        )
    return {
        "component": parameter["component"],
        "parameter": parameter["parameter"],
        "required_value": _fmt_num(required),
        "provided_value": provided_label,
        "unit": parameter["unit"],
        "standard_ref": "DESIGN-BASIS",
        "spec_clause": "",
        "severity": parameter["severity"],
        "rationale": rationale,
        "confidence": 0.65,
        "cx_source": "rule-based",
    }


def _freeform_compare(spec_text: str, submittal_text: str) -> list[dict]:
    devs, seen, seen_sig = [], set(), set()
    for parameter in _FREEFORM_PARAMS:
        ckey = (parameter["component"], parameter["parameter"])
        if ckey in seen:
            continue
        deviation = _freeform_deviation(parameter, spec_text, submittal_text)
        if deviation is None:
            continue  # spec doesn't constrain this parameter — skip
        sig = (deviation["required_value"], deviation["provided_value"])
        if sig in seen_sig:
            continue
        seen_sig.add(sig)
        seen.add(ckey)
        devs.append(deviation)
    return devs


def _norm_val(s) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).strip().lower())


def _enrich_cx(d: dict, system_id: str) -> dict:
    """Attach commissioning test + lead time via the rule table only — never an
    LLM call. (LLM-based Cx prediction for ad-hoc parameters multiplied live
    latency by one extra call per deviation.) Unmapped parameters keep no Cx."""
    key = (d.get("component"), d.get("parameter"))
    if key in _RULES or cx_graph.explain(*key):
        d.update(predict_cx_impact(d))
    d.setdefault("severity", "Major")
    d["system"] = system_id
    return d


def _resilient_fallback(spec_text: str, submittal_text: str,
                        system_id: str = "CUSTOM") -> list[dict]:
    """No-LLM detector for the live path: free-form rules (canonical, Cx-mapped)
    plus the strict template parser, de-duplicated by value signature. Enriches
    rule-table hits with their commissioning test + lead time WITHOUT any LLM
    call, so the audit chain still renders during an LLM outage."""
    devs = _freeform_compare(spec_text, submittal_text)
    sigs = {(_norm_val(d["required_value"]), _norm_val(d["provided_value"]))
            for d in devs}
    for d in _deterministic_compare(spec_text, submittal_text):
        sig = (_norm_val(d["required_value"]), _norm_val(d["provided_value"]))
        if sig not in sigs:
            devs.append(d)
            sigs.add(sig)
    for d in devs:
        _enrich_cx(d, system_id)
    return devs


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
