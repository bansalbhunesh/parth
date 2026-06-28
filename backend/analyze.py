"""Shared analysis logic — used by all /analyze endpoints."""

import concurrent.futures
import logging
import os
import re
import time
from typing import NamedTuple

from backend.agents.reconciliation import (
    _all_standards_text,
    _check_citation_faithfulness,
    _validate_deviations,
    SYSTEM_PROMPT,
    PROMPT_TEMPLATE,
)
from backend.agents.commissioning import predict_cx_impact, _RULES
from backend.agents import cx_graph

log = logging.getLogger("pramaan.analyze")

# Hard ceiling on how long the live /analyze path waits for the LLM before it
# degrades to the instant rule-based detector. Free-tier models can 503-retry
# for 40s+; a judge will not wait. Tune with PRAMAAN_LLM_TIMEOUT (seconds).
_LLM_TIMEOUT_S = float(os.getenv("PRAMAAN_LLM_TIMEOUT", "60"))

# Module-level pool so a timed-out call is abandoned (left to finish in the
# background) rather than blocking the response — a `with` executor would wait
# for the worker on exit and defeat the timeout.
_LLM_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=4)


class AnalysisResult(NamedTuple):
    deviations: list[dict]
    mode: str
    elapsed_ms: int


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
    r"(not\s+stated|upon\s+request|available\s+on\s+request|n/?a|tbd|"
    r"to\s+be\s+(?:advised|confirmed)|pending)", re.I)


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


def _freeform_compare(spec_text: str, submittal_text: str) -> list[dict]:
    devs, seen, seen_sig = [], set(), set()
    for p in _FREEFORM_PARAMS:
        ckey = (p["component"], p["parameter"])
        if ckey in seen:
            continue
        req = prov = None
        for kw in p["kw"]:
            if req is None:
                req = _num_near(spec_text, kw, p["unit_rx"])
            if prov is None:
                prov = _num_near(submittal_text, kw, p["unit_rx"])
        if req is None:
            continue  # spec doesn't constrain this parameter — skip
        if prov is None:
            if not any(_omission_near(submittal_text, kw) for kw in p["kw"]):
                continue
            prov_label, is_dev = "Not stated", True
            rationale = f"Spec requires {p['parameter']} but the submittal omits it"
        else:
            d = p["direction"]
            is_dev = (prov < req if d == "min"
                      else prov > req if d == "max" else prov != req)
            prov_label = _fmt_num(prov)
            rationale = (f"Provided {prov_label} {p['unit']} does not satisfy "
                         f"required {_fmt_num(req)} {p['unit']}")
        if not is_dev:
            continue
        # Value-signature dedup: if two overlapping rules report the SAME
        # required->provided numeric transition (e.g. a busway Icw also matched
        # by the switchgear rule), keep only the first so the fallback never
        # double-counts one physical fact under two component labels.
        sig = (_fmt_num(req), prov_label)
        if sig in seen_sig:
            continue
        seen_sig.add(sig)
        seen.add(ckey)
        devs.append({
            "component": p["component"], "parameter": p["parameter"],
            "required_value": _fmt_num(req), "provided_value": prov_label,
            "unit": p["unit"], "standard_ref": "DESIGN-BASIS", "spec_clause": "",
            "severity": p["severity"], "rationale": rationale,
            "confidence": 0.65, "cx_source": "rule-based",
        })
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


def run_analysis(
    spec_text: str,
    submittal_text: str,
    system_id: str = "CUSTOM",
) -> AnalysisResult:
    t0 = time.time()
    standards = _all_standards_text(max_chars_per=1800)
    prompt = PROMPT_TEMPLATE.format(
        spec=spec_text, submittal=submittal_text, standards=standards,
    )
    try:
        from backend.llm import complete_json
        # Bound the wait: a free-tier model that 503-retries for 40s+ would
        # otherwise hang the demo. A timed-out call is abandoned (left running)
        # and we degrade to the instant rule-based detector.
        raw = _LLM_POOL.submit(complete_json, prompt, SYSTEM_PROMPT).result(
            timeout=_LLM_TIMEOUT_S)
        devs = _validate_deviations(raw)
        devs = _check_citation_faithfulness(devs, spec_text, submittal_text, standards)
        for d in devs:
            _enrich_cx(d, system_id)  # rule-table only — no extra LLM calls
        mode = "llm"
    except concurrent.futures.TimeoutError:
        log.warning("LLM analysis exceeded %.0fs, using rule-based fallback",
                    _LLM_TIMEOUT_S)
        devs = _resilient_fallback(spec_text, submittal_text, system_id)
        mode = "deterministic"
    except Exception as exc:
        log.warning("LLM analysis failed, running rule-based fallback: %s", exc)
        devs = _resilient_fallback(spec_text, submittal_text, system_id)
        mode = "deterministic"
    elapsed = round((time.time() - t0) * 1000)
    return AnalysisResult(deviations=devs, mode=mode, elapsed_ms=elapsed)


def run_streaming_analysis(
    spec_text: str,
    submittal_text: str,
    system_id: str = "CUSTOM",
):
    import json

    standards = _all_standards_text(max_chars_per=1800)
    prompt = PROMPT_TEMPLATE.format(
        spec=spec_text, submittal=submittal_text, standards=standards,
    )

    yield f"event: status\ndata: Running AI reconciliation engine...\n\n"

    try:
        from backend.llm import complete_stream as llm_stream, _extract_json
        full_text = ""
        for chunk in llm_stream(prompt, system=SYSTEM_PROMPT):
            full_text += chunk
            yield f"event: token\ndata: {json.dumps(chunk)}\n\n"

        yield f"event: status\ndata: Validating deviations...\n\n"
        raw = _extract_json(full_text)
        devs = _validate_deviations(raw)
        devs = _check_citation_faithfulness(devs, spec_text, submittal_text, standards)
        for d in devs:
            _enrich_cx(d, system_id)  # rule-table only — no extra LLM calls
        mode = "llm"
    except Exception as exc:
        log.warning("LLM stream analysis failed, rule-based fallback: %s", exc)
        yield f"event: status\ndata: AI engine unavailable — running rule-based detector...\n\n"
        devs = _resilient_fallback(spec_text, submittal_text, system_id)
        mode = "deterministic"

    result = {
        "system": system_id,
        "deviations": devs,
        "count": len(devs),
        "mode": mode,
    }
    yield f"event: result\ndata: {json.dumps(result)}\n\n"
    yield "event: done\ndata: {}\n\n"
