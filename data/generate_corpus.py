"""
Pramaan — Synthetic EPC corpus generator for "Project Meghdoot"
A 40 MW, Uptime Tier IV hyperscale data centre (fictional, India).

Generates a small-but-realistic, LABELLED corpus so the deviation-detection
pipeline can be evaluated with real precision/recall. Deterministic: no LLM
required to produce the corpus, so it is reproducible and auditable.

Outputs (under data/corpus/):
  specs/<SYS>.md                 design-basis "shall" requirements
  submittals/<SYS>.md            procured/vendor values
  standards/<STD>.md             PARAPHRASED public requirement summaries
  commissioning/cx_plan.json     Cx Level 1-5 tests + acceptance criteria
  rfi/rfi_log.json               historical RFIs (some resolved)
  extracted/requirements.json    structured spec triples (perfect-extraction ref)
  extracted/submittals.json      structured submittal triples
  ground_truth.json              the seeded deviation manifest (the LABELS)

NOTE on standards: we never reproduce copyrighted standard text. The
standards/*.md files are short, original paraphrases of publicly-known
requirement *intent* (Uptime Tier IV concurrent maintainability / fault
tolerance, TIA-942, BICSI-002, NFPA 75) written for this synthetic project.
"""

import json
import os
import pathlib

ROOT = pathlib.Path(__file__).parent / "corpus"

PROJECT = {
    "name": "Project Meghdoot",
    "capacity_mw": 40,
    "tier": "Uptime Tier IV",
    "location": "Navi Mumbai, India",
    "current_week": 11,
    "line_items_total": 14000,
    "active_submittals": 87,
}

# ---------------------------------------------------------------------------
# Systems. Each requirement is a triple:
#   (component, parameter, required_value, unit, std_ref, clause)
# Each submittal provides a value. When provided != required in a way that
# violates the standard, it is a seeded deviation (recorded in GROUND_TRUTH).
# ---------------------------------------------------------------------------

SYSTEMS = {
    "UPS": {
        "title": "Uninterruptible Power Supply & Battery",
        "requirements": [
            ("UPS-02", "battery_runtime_min", 10, "min", "UPTIME-TIER4", "DB-4.3"),
            ("UPS-02", "redundancy", "2N", "topology", "UPTIME-TIER4", "DB-4.1"),
            ("UPS-02", "rated_power_kw", 1200, "kW", "DESIGN-BASIS", "DB-4.2"),
        ],
        "submittal": {
            # battery sized for 7 min, not 10 -> DEVIATION (subtle: in a battery datasheet)
            "battery_runtime_min": 7,
            "redundancy": "2N",
            "rated_power_kw": 1200,
        },
    },
    "GEN": {
        "title": "Diesel Generators & Fuel Storage",
        "requirements": [
            ("GEN-FUEL", "onsite_fuel_hours", 24, "h", "UPTIME-TIER4", "DB-5.4"),
            ("GEN-01", "redundancy", "N+1", "topology", "UPTIME-TIER4", "DB-5.1"),
            ("GEN-01", "rated_power_kva", 2500, "kVA", "DESIGN-BASIS", "DB-5.2"),
        ],
        "submittal": {
            # fuel tank sized for 12 h, not 24 -> DEVIATION (in a civil/tank submittal)
            "onsite_fuel_hours": 12,
            "redundancy": "N+1",
            "rated_power_kva": 2500,
        },
    },
    "COOL": {
        "title": "Cooling — Chillers / CRAH / Liquid Loop",
        "requirements": [
            ("COOL-LOOP", "redundancy", "N+2", "topology", "UPTIME-TIER4", "DB-6.1"),
            ("CRAH", "supply_air_temp_c", 24, "C", "DESIGN-BASIS", "DB-6.3"),
            ("CHILLER", "capacity_tr", 1500, "TR", "DESIGN-BASIS", "DB-6.2"),
        ],
        "submittal": {
            # N+1 provided, N+2 required -> DEVIATION (topology buried in a P&ID)
            "redundancy": "N+1",
            "supply_air_temp_c": 24,
            "capacity_tr": 1500,
        },
    },
    "SWGR": {
        "title": "MV/LV Switchgear",
        "requirements": [
            ("SWGR-MV", "short_circuit_rating_ka", 50, "kA", "DESIGN-BASIS", "DB-7.2"),
            ("SWGR-MV", "redundancy", "2N", "topology", "UPTIME-TIER4", "DB-7.1"),
        ],
        "submittal": {
            # 40 kA provided vs 50 kA calculated fault level -> DEVIATION
            "short_circuit_rating_ka": 40,
            "redundancy": "2N",
        },
    },
    "CABLE": {
        "title": "Power & Data Cabling",
        "requirements": [
            ("CABLE-DC", "fire_rating", "CMP", "plenum-class", "NFPA-75", "DB-8.4"),
            ("CABLE-DC", "category", "Cat6A", "type", "TIA-942", "DB-8.1"),
        ],
        "submittal": {
            # CMR provided vs CMP required for plenum/room class -> DEVIATION
            "fire_rating": "CMR",
            "category": "Cat6A",
        },
    },
    "BMS": {
        "title": "Building Management & EPMS",
        "requirements": [
            ("BMS", "critical_alarm_points", "complete", "set", "DESIGN-BASIS", "DB-9.5"),
            ("BMS", "monitoring_redundancy", "dual", "topology", "UPTIME-TIER4", "DB-9.1"),
        ],
        "submittal": {
            # points list missing the leak-detection critical alarm -> DEVIATION (omission)
            "critical_alarm_points": "missing:leak_detection",
            "monitoring_redundancy": "dual",
        },
    },
    "FIRE": {
        "title": "Fire Suppression",
        "requirements": [
            ("FIRE-SUP", "agent", "clean_agent", "type", "NFPA-75", "DB-10.2"),
            ("FIRE-SUP", "zones", 8, "count", "DESIGN-BASIS", "DB-10.1"),
        ],
        "submittal": {  # compliant — included as a true-negative control
            "agent": "clean_agent",
            "zones": 8,
        },
    },
    "BUSWAY": {
        "title": "Busway Distribution",
        "requirements": [
            ("BUSWAY", "rating_a", 4000, "A", "DESIGN-BASIS", "DB-11.1"),
            ("BUSWAY", "redundancy", "2N", "topology", "UPTIME-TIER4", "DB-11.2"),
        ],
        "submittal": {  # compliant — true-negative control
            "rating_a": 4000,
            "redundancy": "2N",
        },
    },
}

# Map each seeded deviation to the commissioning test it jeopardises + week.
# week_caught = project current week (11). week_fail = scheduled Cx test week.
DEVIATION_TO_CX = {
    ("UPS-02", "battery_runtime_min"): {
        "cx_test": "IST-07", "cx_level": 4,
        "cx_name": "Load transfer under maintenance (battery autonomy)",
        "week_fail": 38, "severity": "Critical",
        "reason": "Battery autonomy below Tier IV requirement; UPS cannot sustain "
                  "load during concurrent maintenance of the alternate path.",
    },
    ("GEN-FUEL", "onsite_fuel_hours"): {
        "cx_test": "IST-11", "cx_level": 4,
        "cx_name": "Sustained utility-outage run (fuel autonomy)",
        "week_fail": 41, "severity": "Critical",
        "reason": "On-site fuel autonomy below Tier IV minimum; generators cannot "
                  "sustain a full design-duration outage.",
    },
    ("COOL-LOOP", "redundancy"): {
        "cx_test": "IST-09", "cx_level": 4,
        "cx_name": "Cooling failover under fault + maintenance",
        "week_fail": 39, "severity": "Critical",
        "reason": "N+1 cooling cannot maintain fault tolerance during concurrent "
                  "maintenance as Tier IV fault tolerance demands.",
    },
    ("SWGR-MV", "short_circuit_rating_ka"): {
        "cx_test": "FAT-03", "cx_level": 3,
        "cx_name": "Protection coordination / fault-withstand verification",
        "week_fail": 30, "severity": "Critical",
        "reason": "Switchgear withstand rating below calculated prospective fault "
                  "level; equipment fails protection-coordination verification.",
    },
    ("CABLE-DC", "fire_rating"): {
        "cx_test": "ITP-02", "cx_level": 2,
        "cx_name": "Cable fire-rating / plenum compliance inspection",
        "week_fail": 22, "severity": "Major",
        "reason": "Cable fire-rating below plenum class required for the room "
                  "classification per NFPA 75.",
    },
    ("BMS", "critical_alarm_points"): {
        "cx_test": "IST-14", "cx_level": 4,
        "cx_name": "Monitoring & alarm verification",
        "week_fail": 40, "severity": "Major",
        "reason": "Critical leak-detection alarm point absent; monitoring "
                  "verification cannot confirm full alarm coverage.",
    },
}

# Standards as ORIGINAL paraphrased summaries (no copyrighted text reproduced).
STANDARDS = {
    "UPTIME-TIER4": (
        "# Uptime Tier IV — Fault Tolerance (paraphrased summary)\n\n"
        "Intent for this project: the facility must remain operational after any "
        "single worst-case failure AND must allow any single element to be removed "
        "from service for planned maintenance while still tolerating an unrelated "
        "fault. Practically this drives:\n\n"
        "- Active/active distribution (commonly 2N) for power paths.\n"
        "- Redundancy sufficient that one path can be in maintenance while another "
        "absorbs a fault (drives N+2 where N+1 only covers a single contingency).\n"
        "- Stored energy (battery autonomy, on-site fuel) sized for the full design "
        "ride-through, not a reduced figure.\n"
    ),
    "TIA-942": (
        "# TIA-942 — Telecom Infrastructure (paraphrased summary)\n\n"
        "Cabling, pathways and spaces sized and rated for the data centre rating "
        "class. Structured cabling category and redundancy must match the design "
        "rating class for the facility.\n"
    ),
    "BICSI-002": (
        "# BICSI-002 — Data Centre Design Best Practice (paraphrased summary)\n\n"
        "Coordinated design across power, cooling, cabling and monitoring; "
        "redundancy of one subsystem must not be undermined by a weaker adjacent "
        "subsystem.\n"
    ),
    "NFPA-75": (
        "# NFPA 75 — Fire Protection of IT Equipment (paraphrased summary)\n\n"
        "Materials in IT/plenum spaces must meet the fire performance for the room "
        "classification. Cable fire-rating must satisfy the plenum/room class; "
        "clean-agent suppression is typical for critical IT rooms.\n"
    ),
    "DESIGN-BASIS": (
        "# Project Meghdoot — Design Basis (owner requirements)\n\n"
        "Owner's project requirements (OPR) that set capacities, set-points and "
        "topology targets for a 40 MW Tier IV facility.\n"
    ),
}


def w(path: pathlib.Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fmt_req(r):
    comp, param, val, unit, std, clause = r
    return (f"- **{comp}** — {param.replace('_', ' ')}: "
            f"shall be **{val} {unit}** "
            f"(ref: {std}; clause {clause})")


def build():
    if ROOT.exists():
        import shutil
        shutil.rmtree(ROOT)

    requirements_struct = []
    submittals_struct = []
    ground_truth = []

    # specs + submittals + structured extracts
    for sys_id, sys in SYSTEMS.items():
        # --- spec doc ---
        spec_md = [f"# {PROJECT['name']} — Design Basis: {sys['title']}",
                   f"_System: {sys_id} · {PROJECT['tier']} · {PROJECT['capacity_mw']} MW_\n",
                   "## Requirements\n"]
        for r in sys["requirements"]:
            spec_md.append(fmt_req(r))
            comp, param, val, unit, std, clause = r
            requirements_struct.append({
                "system": sys_id, "component": comp, "parameter": param,
                "required_value": val, "unit": unit,
                "standard_ref": std, "clause": clause,
            })
        w(ROOT / "specs" / f"{sys_id}.md", "\n".join(spec_md) + "\n")

        # --- submittal doc ---
        sub_md = [f"# Vendor Submittal — {sys['title']} ({sys_id})",
                  f"_Project: {PROJECT['name']} · Submittal rev B_\n",
                  "## Provided values\n"]
        for r in sys["requirements"]:
            comp, param, val, unit, std, clause = r
            provided = sys["submittal"][param]
            sub_md.append(f"- **{comp}** — {param.replace('_', ' ')}: "
                          f"**{provided} {unit}** (vendor datasheet)")
            submittals_struct.append({
                "system": sys_id, "component": comp, "parameter": param,
                "provided_value": provided, "unit": unit,
            })

            # detect seeded deviation
            if provided != val:
                key = (comp, param)
                cx = DEVIATION_TO_CX.get(key, {})
                ground_truth.append({
                    "id": f"DEV-{len(ground_truth)+1:03d}",
                    "system": sys_id,
                    "component": comp,
                    "parameter": param,
                    "required_value": val,
                    "provided_value": provided,
                    "unit": unit,
                    "standard_ref": std,
                    "spec_clause": clause,
                    "severity": cx.get("severity", "Major"),
                    "predicted_cx_test": cx.get("cx_test"),
                    "predicted_cx_level": cx.get("cx_level"),
                    "predicted_cx_name": cx.get("cx_name"),
                    "week_caught": PROJECT["current_week"],
                    "week_fail": cx.get("week_fail"),
                    "lead_time_weeks": (cx.get("week_fail") or PROJECT["current_week"])
                                       - PROJECT["current_week"],
                    "rationale": cx.get("reason", ""),
                })
        w(ROOT / "submittals" / f"{sys_id}.md", "\n".join(sub_md) + "\n")

    # standards
    for std_id, text in STANDARDS.items():
        w(ROOT / "standards" / f"{std_id}.md", text)

    # commissioning plan
    cx_plan = {
        "project": PROJECT["name"],
        "levels": {
            "1": "Component verification (factory/ITP)",
            "2": "Installation / inspection (ITP)",
            "3": "Functional / factory acceptance (FAT)",
            "4": "Integrated systems test (IST)",
            "5": "Owner acceptance / sustained operations",
        },
        "tests": [
            {"id": v["cx_test"], "level": v["cx_level"], "name": v["cx_name"],
             "scheduled_week": v["week_fail"],
             "acceptance": v["reason"].split(";")[0]}
            for v in DEVIATION_TO_CX.values()
        ],
    }
    w(ROOT / "commissioning" / "cx_plan.json", json.dumps(cx_plan, indent=2))

    # RFI log (some resolved; one mirrors the UPS issue for the copilot "seen before")
    rfi_log = [
        {"id": "RFI-014", "system": "UPS", "status": "resolved",
         "question": "Confirm UPS battery autonomy target for Tier IV during "
                     "concurrent maintenance.",
         "resolution": "Owner confirmed 10 min minimum autonomy at full load; "
                       "vendor to resize battery string accordingly.",
         "week": 6},
        {"id": "RFI-021", "system": "COOL", "status": "open",
         "question": "Is N+1 acceptable for the chilled-water loop or is N+2 "
                     "required for fault tolerance?",
         "resolution": None, "week": 9},
        {"id": "RFI-009", "system": "SWGR", "status": "resolved",
         "question": "Confirm prospective fault level for MV switchgear sizing.",
         "resolution": "Fault study returned 47.6 kA; specify >=50 kA withstand.",
         "week": 4},
        {"id": "RFI-017", "system": "GEN", "status": "open",
         "question": "Clarify on-site fuel autonomy hours for Tier IV.",
         "resolution": None, "week": 8},
    ]
    w(ROOT / "rfi" / "rfi_log.json", json.dumps(rfi_log, indent=2))

    # structured extracts (perfect-extraction reference) + ground truth
    w(ROOT / "extracted" / "requirements.json",
      json.dumps(requirements_struct, indent=2))
    w(ROOT / "extracted" / "submittals.json",
      json.dumps(submittals_struct, indent=2))
    w(ROOT / "ground_truth.json", json.dumps({
        "project": PROJECT,
        "seeded_deviations": ground_truth,
        "true_negative_systems": ["FIRE", "BUSWAY"],
    }, indent=2))

    # manifest summary
    print(f"Generated corpus for {PROJECT['name']} at {ROOT}")
    print(f"  systems          : {len(SYSTEMS)}")
    print(f"  spec docs        : {len(SYSTEMS)}")
    print(f"  submittal docs   : {len(SYSTEMS)}")
    print(f"  standards docs   : {len(STANDARDS)}")
    print(f"  requirements     : {len(requirements_struct)}")
    print(f"  seeded deviations: {len(ground_truth)}")
    for d in ground_truth:
        print(f"    {d['id']} {d['component']}.{d['parameter']}: "
              f"{d['provided_value']} vs {d['required_value']} {d['unit']} "
              f"-> {d['predicted_cx_test']} (L{d['predicted_cx_level']}), "
              f"lead {d['lead_time_weeks']}w, {d['severity']}")


if __name__ == "__main__":
    build()
