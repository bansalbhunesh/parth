"""Deterministic rule-based deviation detection — the no-LLM floor.

Extracted verbatim from ``backend.analyze`` so the bounded LLM orchestration
and the deterministic engine evolve (and are size/complexity-gated)
independently. Used ONLY by the live /analyze fallback (never by the eval
harness) so the product still catches the headline deviations from real,
un-templated vendor prose when the LLM is unavailable (rate-limited / no key)
— instead of silently returning zero. Conservative by design: it only fires on
a confident numeric mismatch or an explicit omission of a value the spec
constrains.
"""

import operator
import re

from backend.agents import cx_graph
from backend.agents.commissioning import _RULES, predict_cx_impact


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
