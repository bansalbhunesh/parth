"""Validates the generated schedule.json + supply_chain.json for all 12 projects:
the cross-layer join keys resolve, and every project flows cleanly through the
schedule-risk, supply-chain, and knowledge-graph engines.
"""

import json
import pathlib

import pytest

from backend.agents import project_graph, schedule_risk, supply_chain

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "corpus"
PROJECTS = ROOT / "data" / "projects"


def _project_dirs():
    dirs = [CORPUS]
    if PROJECTS.exists():
        dirs += [p for p in sorted(PROJECTS.iterdir())
                 if p.is_dir() and (p / "ground_truth.json").exists()]
    return dirs


def _load(d, name):
    p = d / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


PROJECT_DIRS = _project_dirs()
PROJECT_IDS = [d.name for d in PROJECT_DIRS]


def test_all_twelve_projects_have_generated_data():
    assert len(PROJECT_DIRS) == 12
    for d in PROJECT_DIRS:
        assert (d / "schedule.json").exists(), f"{d.name} missing schedule.json"
        assert (d / "supply_chain.json").exists(), f"{d.name} missing supply_chain.json"


@pytest.mark.parametrize("d", PROJECT_DIRS, ids=PROJECT_IDS)
class TestGeneratedDataPerProject:
    def test_schedule_cx_tests_resolve(self, d):
        sch = _load(d, "schedule.json")
        cx = _load(d, "commissioning/cx_plan.json") or {"tests": []}
        cx_ids = {t["id"] for t in cx["tests"]}
        for task in sch["tasks"]:
            if task.get("cx_test"):
                assert task["cx_test"] in cx_ids, \
                    f"{d.name}: task {task['id']} cx_test {task['cx_test']} not in cx_plan"
        assert any(t.get("is_milestone") for t in sch["tasks"])
        assert sch.get("deadline_week")

    def test_supply_links_resolve(self, d):
        sup = _load(d, "supply_chain.json")
        cx = _load(d, "commissioning/cx_plan.json") or {"tests": []}
        cx_ids = {t["id"] for t in cx["tests"]}
        for s in sup["shipments"]:
            assert s.get("component")
            if s.get("feeds_cx_test"):
                assert s["feeds_cx_test"] in cx_ids
            # stage means sum to ~ the nominal lead time
            total = sum(st["planned_mean_weeks"] for st in s["stages"])
            assert abs(total - s["lead_time_weeks"]) < 2

    def test_schedule_engine_runs(self, d):
        sch = _load(d, "schedule.json")
        out = schedule_risk.analyze_schedule(sch, n=2000, seed=42)
        assert out["cpm"]["project_duration"] > 0
        assert out["monte_carlo"]["p50"] <= out["monte_carlo"]["p80"]

    def test_supply_engine_runs(self, d):
        sup = _load(d, "supply_chain.json")
        out = supply_chain.analyze_supply_chain(sup)
        assert out["summary"]["total"] == len(sup["shipments"])

    def test_graph_blast_radius_runs(self, d):
        gt = _load(d, "ground_truth.json")
        sch = _load(d, "schedule.json")
        sup = _load(d, "supply_chain.json")
        cx = _load(d, "commissioning/cx_plan.json")
        g = project_graph.assemble(gt["seeded_deviations"], cx_plan=cx,
                                   supply_chain=sup, schedule=sch)
        devs = gt["seeded_deviations"]
        if devs:
            br = project_graph.blast_radius(g, devs[0]["id"])
            assert br is not None
            assert br["weeks_at_risk"] >= 0
