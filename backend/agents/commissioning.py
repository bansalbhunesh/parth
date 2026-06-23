"""
Commissioning Risk Predictor.

Maps a confirmed deviation to the specific commissioning test it will jeopardise
and computes the LEAD TIME — how many weeks earlier Pramaan caught it vs when it
would have surfaced in commissioning.

v2: Added LLM fallback for unmapped deviations + risk scoring.
"""

import json
import pathlib

from backend.llm import complete_json

CORPUS = pathlib.Path(__file__).parent.parent.parent / "data" / "corpus"
CURRENT_WEEK = 11

_RULES = {
    ("UPS-02", "battery_runtime_min"): ("IST-07", 4, 38, "Critical"),
    ("GEN-FUEL", "onsite_fuel_hours"): ("IST-11", 4, 41, "Critical"),
    ("COOL-LOOP", "redundancy"): ("IST-09", 4, 39, "Critical"),
    ("SWGR-MV", "short_circuit_rating_ka"): ("FAT-03", 3, 30, "Critical"),
    ("CABLE-DC", "fire_rating"): ("ITP-02", 2, 22, "Major"),
    ("BMS", "critical_alarm_points"): ("IST-14", 4, 40, "Major"),
    ("FLOOR", "height_mm"): ("ITP-01", 1, 16, "Major"),
}


def _load_cx_plan():
    path = CORPUS / "commissioning" / "cx_plan.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"tests": []}


def _cx_name(test_id):
    plan = _load_cx_plan()
    for t in plan["tests"]:
        if t["id"] == test_id:
            return t["name"]
    return None


def _llm_predict(deviation: dict) -> dict:
    cx_plan = _load_cx_plan()
    prompt = f"""\
Given this EPC deviation in a Tier IV data centre, predict which commissioning
test it will cause to fail.

Deviation:
- Component: {deviation.get('component')}
- Parameter: {deviation.get('parameter')}
- Required: {deviation.get('required_value')} {deviation.get('unit', '')}
- Provided: {deviation.get('provided_value')} {deviation.get('unit', '')}
- Severity: {deviation.get('severity', 'Major')}

Available commissioning tests:
{json.dumps(cx_plan.get('tests', []), indent=2)}

Return JSON:
{{
  "test_id": "<most likely test ID from the list>",
  "test_level": <level number>,
  "reason": "<why this deviation would cause this test to fail>"
}}
"""
    try:
        result = complete_json(prompt, system="You are a commissioning expert.")
        test_id = result.get("test_id")
        test_level = result.get("test_level")
        week_fail = None
        for t in cx_plan.get("tests", []):
            if t["id"] == test_id:
                week_fail = t.get("scheduled_week")
                break
        return {
            "predicted_cx_test": test_id,
            "predicted_cx_level": test_level,
            "predicted_cx_name": _cx_name(test_id) or "LLM-estimated, needs Cx review",
            "week_caught": CURRENT_WEEK,
            "week_fail": week_fail,
            "lead_time_weeks": (week_fail - CURRENT_WEEK) if week_fail else None,
            "severity": deviation.get("severity", "Major"),
            "cx_source": "llm",
        }
    except Exception:
        return {
            "predicted_cx_test": None,
            "predicted_cx_level": None,
            "predicted_cx_name": "Unmapped — requires Cx engineer review",
            "week_caught": CURRENT_WEEK,
            "week_fail": None,
            "lead_time_weeks": None,
            "severity": deviation.get("severity", "Major"),
            "cx_source": "fallback",
        }


def predict_cx_impact(deviation: dict) -> dict:
    key = (deviation.get("component"), deviation.get("parameter"))
    if key in _RULES:
        test_id, level, week_fail, severity = _RULES[key]
        return {
            "predicted_cx_test": test_id,
            "predicted_cx_level": level,
            "predicted_cx_name": _cx_name(test_id),
            "week_caught": CURRENT_WEEK,
            "week_fail": week_fail,
            "lead_time_weeks": week_fail - CURRENT_WEEK,
            "severity": deviation.get("severity", severity),
            "cx_source": "rule",
        }
    return _llm_predict(deviation)


def compute_risk_score(deviation: dict) -> float:
    severity_weights = {"Critical": 1.0, "Major": 0.6, "Minor": 0.3}
    base = severity_weights.get(deviation.get("severity", "Major"), 0.5)
    lead = deviation.get("lead_time_weeks")
    if lead and lead > 20:
        base *= 1.2
    level = deviation.get("predicted_cx_level")
    if level and level >= 4:
        base *= 1.1
    return min(round(base, 2), 1.0)
