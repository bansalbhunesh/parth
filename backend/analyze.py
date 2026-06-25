"""Shared analysis logic — used by all /analyze endpoints."""

import logging
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
from backend.agents.commissioning import predict_cx_impact

log = logging.getLogger("pramaan.analyze")


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


def run_analysis(
    spec_text: str,
    submittal_text: str,
    system_id: str = "CUSTOM",
) -> AnalysisResult:
    t0 = time.time()
    standards = _all_standards_text()
    prompt = PROMPT_TEMPLATE.format(
        spec=spec_text, submittal=submittal_text, standards=standards,
    )
    try:
        from backend.llm import complete_json
        raw = complete_json(prompt, system=SYSTEM_PROMPT)
        devs = _validate_deviations(raw)
        devs = _check_citation_faithfulness(devs, spec_text, submittal_text, standards)
        for d in devs:
            d.update(predict_cx_impact(d))
            d["system"] = system_id
        mode = "llm"
    except Exception as exc:
        log.warning("LLM analysis failed, running deterministic: %s", exc)
        devs = _deterministic_compare(spec_text, submittal_text)
        mode = "deterministic"
    elapsed = round((time.time() - t0) * 1000)
    return AnalysisResult(deviations=devs, mode=mode, elapsed_ms=elapsed)


def run_streaming_analysis(
    spec_text: str,
    submittal_text: str,
    system_id: str = "CUSTOM",
):
    import json

    standards = _all_standards_text()
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
            d.update(predict_cx_impact(d))
            d["system"] = system_id
        mode = "llm"
    except Exception as exc:
        log.warning("LLM stream analysis failed, deterministic fallback: %s", exc)
        yield f"event: status\ndata: Falling back to deterministic analysis...\n\n"
        devs = _deterministic_compare(spec_text, submittal_text)
        mode = "deterministic"

    result = {
        "system": system_id,
        "deviations": devs,
        "count": len(devs),
        "mode": mode,
    }
    yield f"event: result\ndata: {json.dumps(result)}\n\n"
    yield "event: done\ndata: {}\n\n"
