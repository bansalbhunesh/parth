"""
Commissioning Risk Predictor — maps deviations to Cx tests and computes lead time.
"""

import json

from backend.llm import complete_json
from backend.paths import CORPUS
from backend.agents import cx_graph


def _current_week():
    gt_path = CORPUS / "ground_truth.json"
    if gt_path.exists():
        gt = json.loads(gt_path.read_text())
        return gt.get("project", {}).get("current_week", 11)
    return 11

_RULES = {
    ("UPS-02", "battery_runtime_min"): ("IST-07", 4, 38, "Critical"),
    ("GEN-FUEL", "onsite_fuel_hours"): ("IST-11", 4, 41, "Critical"),
    ("COOL-LOOP", "redundancy"): ("IST-09", 4, 39, "Critical"),
    ("SWGR-MV", "short_circuit_rating_ka"): ("FAT-03", 3, 30, "Critical"),
    ("CABLE-DC", "fire_rating"): ("ITP-02", 2, 22, "Major"),
    ("BMS", "critical_alarm_points"): ("IST-14", 4, 40, "Major"),
    ("FLOOR", "height_mm"): ("ITP-01", 1, 16, "Major"),
    ("GEN-01", "start_time_sec"): ("IST-01", 4, 34, "Critical"),
    ("COOL-LOOP", "delta_t_c"): ("IST-16", 4, 36, "Major"),
    ("UPS-02", "efficiency_pct"): ("FAT-01", 3, 24, "Major"),
    ("SWGR-MV", "arc_flash_rating"): ("ITP-03", 2, 20, "Major"),
    ("CABLE-DC", "max_bundle_size"): ("ITP-04", 2, 18, "Minor"),
    ("BMS", "monitoring_redundancy"): ("IST-15", 4, 44, "Critical"),
    ("FLOOR", "load_rating_kpa"): ("ITP-05", 1, 19, "Critical"),
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
            "week_caught": _current_week(),
            "week_fail": week_fail,
            "lead_time_weeks": (week_fail - _current_week()) if week_fail else None,
            "severity": deviation.get("severity", "Major"),
            "cx_source": "llm",
        }
    except Exception:
        return {
            "predicted_cx_test": None,
            "predicted_cx_level": None,
            "predicted_cx_name": "Unmapped — requires Cx engineer review",
            "week_caught": _current_week(),
            "week_fail": None,
            "lead_time_weeks": None,
            "severity": deviation.get("severity", "Major"),
            "cx_source": "fallback",
        }


def predict_cx_impact(deviation: dict) -> dict:
    key = (deviation.get("component"), deviation.get("parameter"))
    if key in _RULES:
        test_id, level, week_fail, severity = _RULES[key]
        cw = _current_week()
        return {
            "predicted_cx_test": test_id,
            "predicted_cx_level": level,
            "predicted_cx_name": _cx_name(test_id),
            "week_caught": cw,
            "week_fail": week_fail,
            "lead_time_weeks": week_fail - cw,
            "severity": deviation.get("severity", severity),
            "cx_source": "rule",
        }
    # Standards-grounded knowledge graph: covers equipment classes outside the
    # Meghdoot scheduling table (e.g. the real raised-floor / busway pairs) with
    # a cited deviation -> test -> level path and a level-typical lead time —
    # deterministic, no LLM call on the live path.
    g = cx_graph.explain(key[0], key[1])
    if g:
        cw = _current_week()
        lead = g.get("lead_time_weeks_typical")
        return {
            "predicted_cx_test": g["predicted_cx_test"],
            "predicted_cx_level": g["predicted_cx_level"],
            "predicted_cx_name": g["predicted_cx_name"],
            "week_caught": cw,
            "week_fail": (cw + lead) if lead else None,
            "lead_time_weeks": lead,
            "severity": deviation.get("severity", "Major"),
            "cx_source": "graph",
            "standard_basis": g.get("standard_basis"),
            "failure_mode": g.get("failure_mode"),
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
