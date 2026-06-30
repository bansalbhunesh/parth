"""Deterministically synthesize schedule.json + supply_chain.json for all 12
projects, bootstrapped from each project's existing cx_plan + ground_truth so the
unified knowledge graph connects (schedule task.cx_test -> cx_plan test id;
supply item.component -> system; supply item.feeds_cx_test -> cx_plan test).

Construction model: DESIGN -> (PROCURE ∥ CIVIL->MEP) -> per-system INSTALL ->
commissioning tasks grouped by Cx level with GATE-L{n} milestones (parallel within
a level, sequential across levels) -> RFS (ready-for-service, the L5 milestone).

Supply model: one long-lead shipment per major system present (UPS/GEN/SWGR/COOL),
with a 10-stage pipeline summing to a real 2024-26 lead time, the same vendors as
the repo's real datasheet pairs, and a couple of deliberately at-risk items.

Run: python data/generate_schedule_supply.py   (writes into each project dir)
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "corpus"
PROJECTS = ROOT / "data" / "projects"

# Major install systems -> (vendor, origin country, lead-time weeks, equipment desc).
# Lead times from 2024-26 data-centre procurement reality; vendors mirror the repo's
# real sourced datasheet pairs.
LONG_LEAD = {
    "UPS": ("Vertiv", "US", 40, "Modular UPS system"),
    "GEN": ("Cummins", "US", 60, "Standby diesel genset"),
    "SWGR": ("ABB", "Germany", 44, "MV/LV switchgear lineup"),
    "COOL": ("STULZ", "Germany", 32, "Precision cooling / CRAH"),
}

# 10-stage pipeline as a fraction of total lead time (manufacturing dominates).
STAGE_FRACTIONS = [
    ("PO_PLACED", 0.0), ("ENGINEERING_SUBMITTAL", 0.08), ("MANUFACTURING", 0.55),
    ("FAT", 0.06), ("EX_WORKS", 0.03), ("OCEAN_FREIGHT", 0.14), ("PORT_CUSTOMS", 0.06),
    ("INLAND_TRANSPORT", 0.05), ("SITE_DELIVERED", 0.0), ("INSTALLED", 0.03),
]

# Per-Cx-level commissioning task 3-point durations (weeks). Later levels are
# longer and riskier (integrated tests).
LEVEL_DUR = {
    1: {"optimistic": 1, "most_likely": 1.5, "pessimistic": 3},
    2: {"optimistic": 1, "most_likely": 2, "pessimistic": 4},
    3: {"optimistic": 2, "most_likely": 3, "pessimistic": 5},
    4: {"optimistic": 2, "most_likely": 3.5, "pessimistic": 7},
    5: {"optimistic": 3, "most_likely": 5, "pessimistic": 9},
}


def _systems(gt: dict) -> list[str]:
    devs = {d["component"].split("-")[0] for d in gt.get("seeded_deviations", [])}
    tn = set(gt.get("true_negative_systems", []))
    return sorted(devs | tn)


def _primary_cx_test(cx_plan: dict, level: int) -> str | None:
    for t in cx_plan.get("tests", []):
        if t.get("level") == level:
            return t["id"]
    return None


def build_schedule(gt: dict, cx_plan: dict) -> dict:
    proj = gt.get("project", {})
    deadline = proj.get("estimated_completion_week", 52)
    systems = _systems(gt)
    install_systems = [s for s in systems if s in LONG_LEAD]

    tasks: list[dict] = [
        {"id": "DESIGN", "name": "Design freeze & IFC release",
         "duration": {"optimistic": 6, "most_likely": 8, "pessimistic": 12}},
        {"id": "PROCURE", "name": "Long-lead procurement release",
         "duration": {"optimistic": 8, "most_likely": 12, "pessimistic": 20},
         "predecessors": ["DESIGN"]},
        {"id": "CIVIL", "name": "Civil & structural",
         "duration": {"optimistic": 8, "most_likely": 10, "pessimistic": 14},
         "predecessors": ["DESIGN"]},
        {"id": "MEP", "name": "MEP rough-in",
         "duration": {"optimistic": 6, "most_likely": 8, "pessimistic": 12},
         "predecessors": ["CIVIL"]},
    ]

    install_ids = []
    for s in install_systems:
        tid = f"INSTALL-{s}"
        install_ids.append(tid)
        tasks.append({
            "id": tid, "name": f"{s} install & terminate", "component": s,
            "cx_test": _primary_cx_test(cx_plan, 3),
            "duration": {"optimistic": 2, "most_likely": 4, "pessimistic": 8},
            "predecessors": ["MEP", "PROCURE"],
        })

    # commissioning tasks grouped by Cx level, with GATE-L{n} milestones
    by_level: dict[int, list[dict]] = {}
    for t in cx_plan.get("tests", []):
        by_level.setdefault(int(t["level"]), []).append(t)

    prev_gate = None
    levels = sorted(by_level)
    for lvl in levels:
        level_task_ids = []
        for t in by_level[lvl]:
            cid = f"CX-{t['id']}"
            level_task_ids.append(cid)
            preds = [prev_gate] if prev_gate else (install_ids or ["MEP"])
            tasks.append({
                "id": cid, "name": t.get("name", t["id"]),
                "cx_test": t["id"], "cx_level": lvl,
                "duration": dict(LEVEL_DUR.get(lvl, LEVEL_DUR[3])),
                "predecessors": list(preds),
            })
        gate = f"GATE-L{lvl}"
        is_final = lvl == levels[-1]
        tasks.append({
            "id": gate, "name": (f"Ready-for-service (L{lvl} integrated systems test)"
                                 if is_final else f"Cx Level {lvl} complete"),
            "cx_level": lvl, "is_milestone": True,
            "duration": {"fixed": 0}, "predecessors": level_task_ids,
        })
        prev_gate = gate

    return {
        "project_id": proj.get("name", "project").lower().replace("project ", "").strip(),
        "time_unit": "weeks",
        "current_week": proj.get("current_week", 11),
        "deadline_week": deadline,
        "tasks": tasks,
    }


def _stages(lead: int, order_week: float, current_week: float) -> tuple[list[dict], str]:
    """Build the 10-stage pipeline; mark done/active/pending against current_week."""
    elapsed = current_week - order_week
    stages = []
    cum = 0.0
    current = "PO_PLACED"
    for name, frac in STAGE_FRACTIONS:
        mean = round(lead * frac, 1)
        std = round(mean * (0.25 if name in ("MANUFACTURING", "PORT_CUSTOMS") else 0.15), 2)
        start, end = cum, cum + mean
        if elapsed >= end and mean > 0:
            status = "done"
        elif start <= elapsed < end or (mean == 0 and abs(elapsed - start) < 0.5):
            status = "active"
            current = name
        else:
            status = "pending"
        stage = {"name": name, "status": status, "planned_mean_weeks": mean, "planned_std_weeks": std}
        if status == "active":
            stage["actual_start_week"] = round(order_week + start, 1)
        stages.append(stage)
        cum = end
    return stages, current


def build_supply_chain(gt: dict, cx_plan: dict) -> dict:
    proj = gt.get("project", {})
    current_week = proj.get("current_week", 11)
    location = proj.get("location", "Site")
    systems = _systems(gt)
    install_systems = [s for s in systems if s in LONG_LEAD]

    shipments = []
    for i, s in enumerate(install_systems):
        vendor, origin, lead, desc = LONG_LEAD[s]
        ros = 28.0  # required on site ~ install window
        # GEN (longest lead) is the deliberately at-risk item: ordered late so it bites.
        late = (s == "GEN")
        order_week = ros - lead + (6 if late else -2)
        stages, current = _stages(lead, order_week, current_week)
        shipments.append({
            "id": f"SHP-{s}", "component": s, "equipment_type": s, "description": desc,
            "supplier": vendor, "vendor": vendor, "origin_country": origin, "country": origin,
            "destination_site": location, "required_on_site_week": ros,
            "lead_time_weeks": lead, "single_source": (s in ("GEN", "SWGR")),
            "feeds_cx_test": _primary_cx_test(cx_plan, 3),
            "linked_task_id": f"INSTALL-{s}", "on_critical_path": (s in ("UPS", "GEN")),
            "current_stage": current,
            "supplier_risk_factors": {
                "single_source": 1.0 if s in ("GEN", "SWGR") else 0.0,
                "subtier_shortage": 1.0 if s in ("UPS", "SWGR") else 0.0,
                "geo": 0.4 if origin != "US" else 0.1,
                "backlog": 0.6 if s in ("GEN", "SWGR") else 0.3,
            },
            "stages": stages,
        })
    return {"project_id": proj.get("name", "project"), "current_week": current_week,
            "shipments": shipments}


def _project_dirs() -> list[pathlib.Path]:
    dirs = [CORPUS]
    if PROJECTS.exists():
        dirs += [p for p in sorted(PROJECTS.iterdir()) if p.is_dir() and (p / "ground_truth.json").exists()]
    return dirs


def main() -> None:
    written = 0
    for d in _project_dirs():
        gt = json.loads((d / "ground_truth.json").read_text(encoding="utf-8"))
        cx_path = d / "commissioning" / "cx_plan.json"
        cx_plan = json.loads(cx_path.read_text(encoding="utf-8")) if cx_path.exists() else {"tests": []}
        (d / "schedule.json").write_text(
            json.dumps(build_schedule(gt, cx_plan), indent=2), encoding="utf-8")
        (d / "supply_chain.json").write_text(
            json.dumps(build_supply_chain(gt, cx_plan), indent=2), encoding="utf-8")
        written += 1
        print(f"  {d.name}: schedule.json + supply_chain.json")
    print(f"Wrote schedule + supply-chain for {written} projects.")


if __name__ == "__main__":
    main()
