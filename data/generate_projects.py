"""
Multi-project corpus generator for Pramaan.

Generates 6 realistic EPC data-centre project corpora, each with seeded
deviations, commissioning plans, and standards references. Projects span
different tiers, geographies, climates, and governing standards to prove
the deviation-detection pipeline generalises beyond a single dataset.

Projects:
  1. meghdoot    — 40 MW Tier IV, Navi Mumbai (existing, Indian standards)
  2. vajra       — 20 MW Tier III, Pune (Indian standards, different deviations)
  3. nordic      — 10 MW Tier III, Oslo (EN 50600 European standard)
  4. sahara      — 5 MW Tier II, Dubai (DEWA/ADDC requirements)
  5. cascade     — 30 MW Tier IV, Oregon (US NEC/NFPA/ASHRAE)
  6. yangtze     — 50 MW Tier IV, Shanghai (GB 50174 Chinese standard)

Usage:
    python3 data/generate_projects.py           # generate all 6 projects
    python3 data/generate_projects.py --list     # list project IDs
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent / "projects"


def w(path: pathlib.Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_project(project_id: str, config: dict):
    """Build one project corpus under data/projects/{project_id}/."""
    pdir = ROOT / project_id
    project = config["project"]
    systems = config["systems"]
    deviation_cx = config["deviation_cx"]
    standards = config["standards"]
    cx_tests = config["cx_tests"]
    rfi_log = config.get("rfi_log", [])

    requirements_struct = []
    submittals_struct = []
    ground_truth = []

    for sys_id, sys_def in systems.items():
        spec_lines = [
            f"# {project['name']} — Design Basis: {sys_def['title']}",
            f"_System: {sys_id} · {project['tier']} · {project['capacity_mw']} MW_\n",
        ]
        if sys_def.get("spec_intro"):
            spec_lines.append(f"## Overview\n\n{sys_def['spec_intro']}\n")
        spec_lines.append("## Requirements\n")

        sub_lines = [
            f"# Vendor Submittal — {sys_def['title']} ({sys_id})",
            f"_Project: {project['name']} · Submittal rev B_\n",
        ]
        if sys_def.get("submittal_intro"):
            sub_lines.append(f"## Vendor Notes\n\n{sys_def['submittal_intro']}\n")
        sub_lines.append("## Provided values\n")

        for req in sys_def["requirements"]:
            comp, param, val, unit, std, clause = req
            spec_lines.append(
                f"- **{comp}** — {param.replace('_', ' ')}: "
                f"shall be **{val} {unit}** (ref: {std}; clause {clause})"
            )
            requirements_struct.append({
                "system": sys_id, "component": comp, "parameter": param,
                "required_value": val, "unit": unit,
                "standard_ref": std, "clause": clause,
            })

            provided = sys_def["submittal"][param]
            sub_lines.append(
                f"- **{comp}** — {param.replace('_', ' ')}: "
                f"**{provided} {unit}** (vendor datasheet)"
            )
            submittals_struct.append({
                "system": sys_id, "component": comp, "parameter": param,
                "provided_value": provided, "unit": unit,
            })

            if str(provided) != str(val):
                cx = deviation_cx.get((comp, param), {})
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
                    "week_caught": project["current_week"],
                    "week_fail": cx.get("week_fail"),
                    "lead_time_weeks": (cx.get("week_fail") or project["current_week"])
                                       - project["current_week"],
                    "rationale": cx.get("reason", ""),
                })

        w(pdir / "specs" / f"{sys_id}.md", "\n".join(spec_lines) + "\n")
        w(pdir / "submittals" / f"{sys_id}.md", "\n".join(sub_lines) + "\n")

    for std_id, text in standards.items():
        w(pdir / "standards" / f"{std_id}.md", text)

    tn_systems = config.get("true_negative_systems", [])

    cx_plan = {
        "project": project["name"],
        "cx_authority": project.get("cx_authority", "Independent Cx Authority"),
        "levels": {
            "1": "Factory Acceptance Testing (FAT)",
            "2": "Site Acceptance / Installation Verification",
            "3": "Startup Testing",
            "4": "Performance Testing",
            "5": "End-to-End Systems Testing",
        },
        "tests": cx_tests,
    }

    w(pdir / "commissioning" / "cx_plan.json", json.dumps(cx_plan, indent=2))
    w(pdir / "rfi" / "rfi_log.json", json.dumps(rfi_log, indent=2))
    w(pdir / "extracted" / "requirements.json", json.dumps(requirements_struct, indent=2))
    w(pdir / "extracted" / "submittals.json", json.dumps(submittals_struct, indent=2))
    w(pdir / "ground_truth.json", json.dumps({
        "project": project,
        "seeded_deviations": ground_truth,
        "true_negative_systems": tn_systems,
    }, indent=2))

    return {
        "id": project_id,
        "name": project["name"],
        "systems": len(systems),
        "requirements": len(requirements_struct),
        "deviations": len(ground_truth),
        "tn_systems": len(tn_systems),
    }


# ---------------------------------------------------------------------------
# Project 2: Vajra — 20 MW Tier III, Pune, India
# ---------------------------------------------------------------------------
VAJRA = {
    "project": {
        "name": "Project Vajra",
        "capacity_mw": 20,
        "tier": "Uptime Tier III",
        "location": "Pune, India",
        "current_week": 8,
        "line_items_total": 8500,
        "active_submittals": 52,
        "total_systems": 8,
        "estimated_completion_week": 44,
        "client": "Vajra Cloud Services Pvt. Ltd.",
        "epc_contractor": "Shapoorji Pallonji & Co.",
        "cx_authority": "TUV India Pvt. Ltd.",
    },
    "systems": {
        "UPS": {
            "title": "Uninterruptible Power Supply",
            "requirements": [
                ("UPS-01", "battery_runtime_min", 10, "min", "UPTIME-TIER3", "VJ-4.1"),
                ("UPS-01", "redundancy", "N+1", "topology", "UPTIME-TIER3", "VJ-4.2"),
                ("UPS-01", "rated_power_kw", 800, "kW", "DESIGN-BASIS", "VJ-4.3"),
                ("UPS-01", "efficiency_pct", 96, "%", "DESIGN-BASIS", "VJ-4.4"),
            ],
            "submittal": {
                "battery_runtime_min": 10,
                "redundancy": "N+1",
                "rated_power_kw": 800,
                "efficiency_pct": 93,
            },
            "spec_intro": "UPS system shall provide conditioned power with N+1 redundancy for concurrent maintainability per Tier III design basis.",
            "submittal_intro": "Vendor: Eaton 93PM 800 kW. Efficiency at rated load: 93% (eco mode available for 99% but not in double-conversion).",
        },
        "GEN": {
            "title": "Diesel Generators",
            "requirements": [
                ("GEN-01", "redundancy", "N+1", "topology", "UPTIME-TIER3", "VJ-5.1"),
                ("GEN-01", "rated_power_kva", 2000, "kVA", "DESIGN-BASIS", "VJ-5.2"),
                ("GEN-01", "start_time_sec", 10, "s", "UPTIME-TIER3", "VJ-5.3"),
                ("GEN-FUEL", "onsite_fuel_hours", 24, "h", "UPTIME-TIER3", "VJ-5.4"),
            ],
            "submittal": {
                "redundancy": "N+1",
                "rated_power_kva": 2000,
                "start_time_sec": 15,
                "onsite_fuel_hours": 24,
            },
            "spec_intro": "Standby generators with N+1 redundancy. Start time shall not exceed 10 seconds per Tier III.",
            "submittal_intro": "Vendor: Kirloskar KG2500. Start time: 15s per manufacturer test at site altitude (550m ASL). Vendor states 10s achievable with pre-lube pump upgrade.",
        },
        "COOL": {
            "title": "Cooling Plant",
            "requirements": [
                ("COOL-01", "redundancy", "N+1", "topology", "UPTIME-TIER3", "VJ-6.1"),
                ("COOL-01", "supply_air_temp_c", 24, "C", "ASHRAE-TC9.9", "VJ-6.2"),
                ("COOL-01", "capacity_tr", 800, "TR", "DESIGN-BASIS", "VJ-6.3"),
            ],
            "submittal": {
                "redundancy": "N+1",
                "supply_air_temp_c": 27,
                "capacity_tr": 800,
            },
            "spec_intro": "Chilled water cooling plant with supply air temperature per ASHRAE TC 9.9 Class A1 recommended envelope (18-27 C, target 24 C).",
            "submittal_intro": "Vendor: Daikin EWAD-TZ 800 TR. Supply air set point proposed at 27 C to maximize free cooling hours in Pune climate.",
        },
        "SWGR": {
            "title": "MV Switchgear",
            "requirements": [
                ("SWGR-01", "short_circuit_rating_ka", 40, "kA", "DESIGN-BASIS", "VJ-7.1"),
                ("SWGR-01", "redundancy", "N+1", "topology", "UPTIME-TIER3", "VJ-7.2"),
            ],
            "submittal": {
                "short_circuit_rating_ka": 40,
                "redundancy": "N+1",
            },
        },
        "CABLE": {
            "title": "Cabling Infrastructure",
            "requirements": [
                ("CABLE-01", "fire_rating", "CMP", "plenum-class", "NFPA-75", "VJ-8.1"),
                ("CABLE-01", "category", "Cat6A", "type", "TIA-942", "VJ-8.2"),
            ],
            "submittal": {
                "fire_rating": "CMP",
                "category": "Cat6A",
            },
        },
        "PDU": {
            "title": "Power Distribution Units",
            "requirements": [
                ("PDU-01", "metering", "per_outlet", "type", "DESIGN-BASIS", "VJ-9.1"),
                ("PDU-01", "redundancy", "A+B", "topology", "UPTIME-TIER3", "VJ-9.2"),
                ("PDU-01", "rated_current_a", 32, "A", "DESIGN-BASIS", "VJ-9.3"),
            ],
            "submittal": {
                "metering": "per_breaker",
                "redundancy": "A+B",
                "rated_current_a": 32,
            },
            "spec_intro": "Rack PDUs shall provide per-outlet metering for capacity planning and PUE reporting.",
            "submittal_intro": "Vendor: Raritan PX3-5000. Metering: per-breaker (16 breakers per PDU). Per-outlet metering available as upgrade option.",
        },
        "BMS": {
            "title": "Building Management System",
            "requirements": [
                ("BMS-01", "protocol", "BACnet_IP", "standard", "DESIGN-BASIS", "VJ-10.1"),
                ("BMS-01", "monitoring_redundancy", "dual", "topology", "UPTIME-TIER3", "VJ-10.2"),
            ],
            "submittal": {
                "protocol": "BACnet_IP",
                "monitoring_redundancy": "dual",
            },
        },
        "FIRE": {
            "title": "Fire Suppression",
            "requirements": [
                ("FIRE-01", "agent", "clean_agent", "type", "NFPA-75", "VJ-11.1"),
                ("FIRE-01", "zones", 4, "count", "DESIGN-BASIS", "VJ-11.2"),
            ],
            "submittal": {
                "agent": "clean_agent",
                "zones": 4,
            },
        },
    },
    "deviation_cx": {
        ("UPS-01", "efficiency_pct"): {
            "cx_test": "FAT-V01", "cx_level": 3,
            "cx_name": "UPS efficiency load-bank verification",
            "week_fail": 26, "severity": "Major",
            "reason": "UPS efficiency 93% below 96% design target; increased heat load affects cooling sizing and PUE.",
        },
        ("GEN-01", "start_time_sec"): {
            "cx_test": "IST-V01", "cx_level": 4,
            "cx_name": "Generator start-up sequence test",
            "week_fail": 32, "severity": "Critical",
            "reason": "Generator start time 15s exceeds 10s Tier III requirement; battery ride-through window insufficient.",
        },
        ("COOL-01", "supply_air_temp_c"): {
            "cx_test": "IST-V02", "cx_level": 4,
            "cx_name": "Cooling performance verification",
            "week_fail": 34, "severity": "Major",
            "reason": "Supply air 27 C exceeds ASHRAE TC 9.9 Class A1 recommended target of 24 C; may cause hot spots in high-density zones.",
        },
        ("PDU-01", "metering"): {
            "cx_test": "IST-V03", "cx_level": 4,
            "cx_name": "PDU metering validation",
            "week_fail": 35, "severity": "Major",
            "reason": "Per-breaker metering does not satisfy per-outlet requirement; prevents per-device power tracking for capacity management.",
        },
    },
    "true_negative_systems": ["SWGR", "CABLE", "BMS", "FIRE"],
    "standards": {
        "UPTIME-TIER3": (
            "# Uptime Tier III — Concurrently Maintainable (paraphrased summary)\n\n"
            "Tier III requires that every capacity component and distribution element can be "
            "removed from service for planned maintenance without impacting IT operations.\n\n"
            "## Key requirements\n"
            "- Power distribution: N+1 minimum\n"
            "- Cooling: N+1 minimum\n"
            "- Battery autonomy: minimum 10 minutes\n"
            "- Generator start time: <= 10 seconds\n"
            "- On-site fuel: 24 hours minimum\n"
            "- Availability target: 99.982%\n"
        ),
        "DESIGN-BASIS": (
            "# Project Vajra — Design Basis Document\n\n"
            "20 MW Uptime Tier III data centre, Pune, India.\n\n"
            "## Key parameters\n"
            "- UPS: 800 kW modules, N+1, 96% efficiency target\n"
            "- Generators: 2000 kVA, N+1, 10s start\n"
            "- Cooling: 800 TR, N+1, 24 C supply air\n"
            "- PDU: per-outlet metering, A+B feeds, 32A\n"
        ),
        "ASHRAE-TC9.9": (
            "# ASHRAE TC 9.9 — Thermal Guidelines (paraphrased)\n\n"
            "Class A1 recommended envelope: 18-27 C dry-bulb at server inlet, "
            "target 24 C +/- 2 C for optimal reliability.\n"
        ),
        "NFPA-75": (
            "# NFPA 75 — Fire Protection of IT Equipment (paraphrased)\n\n"
            "CMP (plenum-rated) cable required in all plenum-classified spaces.\n"
            "Clean-agent suppression required for rooms with active IT equipment.\n"
        ),
        "TIA-942": (
            "# TIA-942-C — Data Centre Infrastructure Standard (paraphrased)\n\n"
            "Minimum Cat6A cabling for all new horizontal runs.\n"
        ),
    },
    "cx_tests": [
        {"id": "ITP-V01", "level": 1, "name": "Equipment receipt inspection",
         "scheduled_week": 14, "acceptance": "Visual + documentation check"},
        {"id": "FAT-V01", "level": 3, "name": "UPS efficiency load-bank verification",
         "scheduled_week": 26, "acceptance": "Efficiency >= 96% at rated load"},
        {"id": "IST-V01", "level": 4, "name": "Generator start-up sequence test",
         "scheduled_week": 32, "acceptance": "Start to rated speed <= 10s"},
        {"id": "IST-V02", "level": 4, "name": "Cooling performance verification",
         "scheduled_week": 34, "acceptance": "Supply air 24 C +/- 2 C at server inlet"},
        {"id": "IST-V03", "level": 4, "name": "PDU metering validation",
         "scheduled_week": 35, "acceptance": "Per-outlet power readings verified"},
        {"id": "IST-V04", "level": 4, "name": "Full maintenance simulation",
         "scheduled_week": 38, "acceptance": "IT load unaffected during maintenance"},
        {"id": "SAT-V01", "level": 5, "name": "72-hour sustained operations",
         "scheduled_week": 42, "acceptance": "No critical alarms for 72 hours"},
    ],
    "rfi_log": [
        {"id": "RFI-V01", "system": "GEN", "status": "open",
         "question": "Can generator start time of 15s be accepted with extended battery?",
         "resolution": None, "week": 5},
        {"id": "RFI-V02", "system": "COOL", "status": "open",
         "question": "Is 27 C supply air acceptable given Pune's mild climate?",
         "resolution": None, "week": 6},
    ],
}


# ---------------------------------------------------------------------------
# Project 3: Nordic Edge — 10 MW Tier III, Oslo, Norway (EN 50600)
# ---------------------------------------------------------------------------
NORDIC = {
    "project": {
        "name": "Project Nordic Edge",
        "capacity_mw": 10,
        "tier": "EN 50600 Class 3",
        "location": "Oslo, Norway",
        "current_week": 6,
        "line_items_total": 6200,
        "active_submittals": 38,
        "total_systems": 7,
        "estimated_completion_week": 40,
        "client": "Nordic Edge Digital AS",
        "epc_contractor": "Skanska Data Centers",
        "cx_authority": "DNV GL Energy",
    },
    "systems": {
        "UPS": {
            "title": "Uninterruptible Power Supply",
            "requirements": [
                ("UPS-N1", "battery_runtime_min", 10, "min", "EN-50600", "NE-4.1"),
                ("UPS-N1", "redundancy", "N+1", "topology", "EN-50600", "NE-4.2"),
                ("UPS-N1", "rated_power_kw", 500, "kW", "DESIGN-BASIS", "NE-4.3"),
                ("UPS-N1", "battery_type", "Li-ion", "type", "DESIGN-BASIS", "NE-4.4"),
            ],
            "submittal": {
                "battery_runtime_min": 10,
                "redundancy": "N+1",
                "rated_power_kw": 500,
                "battery_type": "VRLA",
            },
            "spec_intro": "UPS with lithium-ion batteries for reduced footprint and longer cycle life in cold climate.",
            "submittal_intro": "Vendor: ABB Conceptpower DPA 500 kW. Battery: VRLA AGM per vendor standard configuration. Li-ion available as option with 16-week lead time.",
        },
        "GEN": {
            "title": "Backup Generators",
            "requirements": [
                ("GEN-N1", "redundancy", "N+1", "topology", "EN-50600", "NE-5.1"),
                ("GEN-N1", "rated_power_kva", 1500, "kVA", "DESIGN-BASIS", "NE-5.2"),
                ("GEN-N1", "noise_db", 75, "dB(A)", "NS-8175", "NE-5.3"),
                ("GEN-FUEL", "onsite_fuel_hours", 48, "h", "DESIGN-BASIS", "NE-5.4"),
            ],
            "submittal": {
                "redundancy": "N+1",
                "rated_power_kva": 1500,
                "noise_db": 85,
                "onsite_fuel_hours": 48,
            },
            "spec_intro": "Generators shall comply with Norwegian noise standard NS 8175 for urban environments (max 75 dB(A) at property boundary).",
            "submittal_intro": "Vendor: Caterpillar C32 1500 kVA. Noise level: 85 dB(A) at 1m with standard exhaust. Acoustic enclosure reduces to 75 dB(A) but not included in base price.",
        },
        "COOL": {
            "title": "Cooling — Free Cooling Dominant",
            "requirements": [
                ("COOL-N1", "free_cooling_hours", 7000, "h/yr", "DESIGN-BASIS", "NE-6.1"),
                ("COOL-N1", "redundancy", "N+1", "topology", "EN-50600", "NE-6.2"),
                ("COOL-N1", "pue_target", 1.15, "ratio", "EU-COC", "NE-6.3"),
            ],
            "submittal": {
                "free_cooling_hours": 5500,
                "redundancy": "N+1",
                "pue_target": 1.25,
            },
            "spec_intro": "Oslo climate enables >7000 free cooling hours/year. Design PUE target 1.15 per EU Code of Conduct for Data Centres.",
            "submittal_intro": "Vendor: Munters Oasis indirect evaporative. Free cooling hours: 5500 h/yr based on vendor's climate model. PUE estimate: 1.25 at full load.",
        },
        "CABLE": {
            "title": "Cabling Infrastructure",
            "requirements": [
                ("CABLE-N1", "fire_rating", "B2ca-s1-d0", "euroclass", "EN-13501", "NE-8.1"),
                ("CABLE-N1", "category", "Cat6A", "type", "EN-50600", "NE-8.2"),
            ],
            "submittal": {
                "fire_rating": "Cca-s1-d1",
                "category": "Cat6A",
            },
            "spec_intro": "Cable fire class shall be B2ca-s1,d0 (Euroclass) per EN 13501-6 for data centre plenum areas.",
            "submittal_intro": "Vendor: Nexans LANmark Cat6A. Fire class: Cca-s1,d1 per EN 13501-6. B2ca variant available on special order.",
        },
        "FIRE": {
            "title": "Fire Suppression",
            "requirements": [
                ("FIRE-N1", "agent", "inert_gas", "type", "EN-15004", "NE-9.1"),
                ("FIRE-N1", "hold_time_min", 10, "min", "EN-15004", "NE-9.2"),
                ("FIRE-N1", "zones", 4, "count", "DESIGN-BASIS", "NE-9.3"),
            ],
            "submittal": {
                "agent": "inert_gas",
                "hold_time_min": 10,
                "zones": 4,
            },
        },
        "BMS": {
            "title": "Building Management System",
            "requirements": [
                ("BMS-N1", "protocol", "BACnet_IP", "standard", "DESIGN-BASIS", "NE-10.1"),
                ("BMS-N1", "energy_reporting", "EN_ISO_50001", "standard", "EU-COC", "NE-10.2"),
            ],
            "submittal": {
                "protocol": "BACnet_IP",
                "energy_reporting": "EN_ISO_50001",
            },
        },
        "STRUCT": {
            "title": "Structural",
            "requirements": [
                ("FLOOR-N1", "load_rating_kpa", 15, "kPa", "DESIGN-BASIS", "NE-11.1"),
                ("FLOOR-N1", "height_mm", 800, "mm", "DESIGN-BASIS", "NE-11.2"),
            ],
            "submittal": {
                "load_rating_kpa": 15,
                "height_mm": 800,
            },
        },
    },
    "deviation_cx": {
        ("UPS-N1", "battery_type"): {
            "cx_test": "FAT-N01", "cx_level": 3,
            "cx_name": "UPS battery type verification",
            "week_fail": 22, "severity": "Major",
            "reason": "VRLA batteries proposed instead of specified Li-ion; VRLA requires larger footprint and more frequent replacement in cold climate cycling.",
        },
        ("GEN-N1", "noise_db"): {
            "cx_test": "IST-N01", "cx_level": 4,
            "cx_name": "Generator noise compliance test",
            "week_fail": 30, "severity": "Critical",
            "reason": "Generator noise 85 dB(A) exceeds NS 8175 limit of 75 dB(A) at property boundary; will fail municipal noise permit.",
        },
        ("COOL-N1", "free_cooling_hours"): {
            "cx_test": "IST-N02", "cx_level": 4,
            "cx_name": "Annual free cooling performance verification",
            "week_fail": 35, "severity": "Major",
            "reason": "Free cooling 5500 h/yr vs 7000 h/yr target; PUE will exceed EU Code of Conduct target of 1.15.",
        },
        ("COOL-N1", "pue_target"): {
            "cx_test": "SAT-N01", "cx_level": 5,
            "cx_name": "72-hour PUE measurement",
            "week_fail": 38, "severity": "Major",
            "reason": "PUE 1.25 exceeds design target 1.15; fails EU Code of Conduct energy efficiency commitment.",
        },
        ("CABLE-N1", "fire_rating"): {
            "cx_test": "ITP-N01", "cx_level": 2,
            "cx_name": "Cable Euroclass fire inspection",
            "week_fail": 18, "severity": "Critical",
            "reason": "Cable Cca class below required B2ca; does not meet EN 13501-6 for building fire safety classification.",
        },
    },
    "true_negative_systems": ["FIRE", "BMS", "STRUCT"],
    "standards": {
        "EN-50600": (
            "# EN 50600 — Information Technology: Data Centre Facilities (paraphrased)\n\n"
            "European standard for data centre design and operation.\n\n"
            "## Availability Classes\n"
            "- Class 1: Basic site infrastructure\n"
            "- Class 2: Redundant capacity components\n"
            "- Class 3: Concurrently maintainable (N+1 paths)\n"
            "- Class 4: Fault tolerant (2N paths)\n\n"
            "## EN 50600-2-2: Power distribution\n"
            "- UPS autonomy >= 10 min for Class 3+\n"
            "- N+1 redundancy minimum for Class 3\n\n"
            "## EN 50600-2-3: Environmental control\n"
            "- References ASHRAE TC 9.9 for temperature envelopes\n"
            "- Energy efficiency per EU Code of Conduct\n"
        ),
        "NS-8175": (
            "# NS 8175 — Norwegian Noise Standard (paraphrased)\n\n"
            "Sound classification of buildings. For mixed-use urban areas:\n"
            "- Daytime (07-23): max 55 dB(A) at property boundary\n"
            "- Night (23-07): max 45 dB(A) at property boundary\n"
            "- Industrial equipment (generators): max 75 dB(A) at 1m from enclosure\n"
        ),
        "EU-COC": (
            "# EU Code of Conduct for Data Centre Energy Efficiency (paraphrased)\n\n"
            "Voluntary best practice for European data centres.\n"
            "- PUE target: <= 1.30 (best practice), <= 1.15 (expected in Nordic)\n"
            "- Free cooling: maximise economiser hours for climate zone\n"
            "- Energy reporting: ISO 50001 energy management system recommended\n"
        ),
        "EN-13501": (
            "# EN 13501-6 — Fire Classification of Cables (paraphrased)\n\n"
            "Euroclass system for cable fire performance:\n"
            "- Aca: non-combustible\n"
            "- B1ca / B2ca: limited combustibility (required for data centres)\n"
            "- Cca: limited fire spread\n"
            "- Dca / Eca: flammable\n"
            "Suffix s1/s2/s3 = smoke, d0/d1/d2 = flaming droplets.\n"
            "B2ca-s1,d0 minimum for plenum/riser areas in data centres.\n"
        ),
        "DESIGN-BASIS": (
            "# Project Nordic Edge — Design Basis Document\n\n"
            "10 MW EN 50600 Class 3 data centre, Oslo, Norway.\n\n"
            "- UPS: 500 kW Li-ion, N+1\n"
            "- Generators: 1500 kVA, N+1, 75 dB(A) max\n"
            "- Cooling: indirect evaporative, 7000 h/yr free cooling, PUE 1.15\n"
            "- Cable: B2ca-s1,d0 Euroclass\n"
            "- On-site fuel: 48 hours (extended for remote Norwegian grid)\n"
        ),
    },
    "cx_tests": [
        {"id": "ITP-N01", "level": 2, "name": "Cable Euroclass fire inspection",
         "scheduled_week": 18, "acceptance": "Cable marking B2ca-s1,d0 verified"},
        {"id": "FAT-N01", "level": 3, "name": "UPS battery type verification",
         "scheduled_week": 22, "acceptance": "Li-ion battery per spec"},
        {"id": "IST-N01", "level": 4, "name": "Generator noise compliance test",
         "scheduled_week": 30, "acceptance": "Noise <= 75 dB(A) at boundary"},
        {"id": "IST-N02", "level": 4, "name": "Annual free cooling performance verification",
         "scheduled_week": 35, "acceptance": ">= 7000 h/yr free cooling"},
        {"id": "SAT-N01", "level": 5, "name": "72-hour PUE measurement",
         "scheduled_week": 38, "acceptance": "PUE <= 1.15"},
    ],
    "rfi_log": [
        {"id": "RFI-N01", "system": "GEN", "status": "open",
         "question": "Can acoustic enclosure be included to meet NS 8175 noise limit?",
         "resolution": None, "week": 4},
        {"id": "RFI-N02", "system": "COOL", "status": "open",
         "question": "Vendor's free cooling model shows 5500 h/yr — can they re-evaluate with Oslo TMY data?",
         "resolution": None, "week": 5},
    ],
}


# ---------------------------------------------------------------------------
# Project 4: Sahara — 5 MW Tier II, Dubai, UAE (DEWA)
# ---------------------------------------------------------------------------
SAHARA = {
    "project": {
        "name": "Project Sahara",
        "capacity_mw": 5,
        "tier": "Uptime Tier II",
        "location": "Dubai, UAE",
        "current_week": 10,
        "line_items_total": 4800,
        "active_submittals": 29,
        "total_systems": 6,
        "estimated_completion_week": 36,
        "client": "Sahara Digital FZCO",
        "epc_contractor": "Al Jaber Engineering",
        "cx_authority": "Aurecon Middle East",
    },
    "systems": {
        "UPS": {
            "title": "Uninterruptible Power Supply",
            "requirements": [
                ("UPS-S1", "redundancy", "N+1", "topology", "UPTIME-TIER2", "SH-4.1"),
                ("UPS-S1", "rated_power_kw", 400, "kW", "DESIGN-BASIS", "SH-4.2"),
            ],
            "submittal": {
                "redundancy": "N+1",
                "rated_power_kw": 400,
            },
        },
        "GEN": {
            "title": "Diesel Generators",
            "requirements": [
                ("GEN-S1", "redundancy", "N+1", "topology", "UPTIME-TIER2", "SH-5.1"),
                ("GEN-S1", "rated_power_kva", 1000, "kVA", "DESIGN-BASIS", "SH-5.2"),
                ("GEN-S1", "derating_pct", 10, "%", "DEWA-REG", "SH-5.3"),
            ],
            "submittal": {
                "redundancy": "N+1",
                "rated_power_kva": 1000,
                "derating_pct": 0,
            },
            "spec_intro": "Generators shall be derated by 10% for ambient temperatures exceeding 50 C per DEWA regulations.",
            "submittal_intro": "Vendor: Perkins 4012-46TAG3A 1000 kVA. Rated at ISO 8528 standard conditions (25 C). No derating applied in proposal.",
        },
        "COOL": {
            "title": "Cooling — Desert Climate",
            "requirements": [
                ("COOL-S1", "redundancy", "N+1", "topology", "UPTIME-TIER2", "SH-6.1"),
                ("COOL-S1", "design_ambient_c", 50, "C", "DEWA-REG", "SH-6.2"),
                ("COOL-S1", "capacity_tr", 500, "TR", "DESIGN-BASIS", "SH-6.3"),
            ],
            "submittal": {
                "redundancy": "N+1",
                "design_ambient_c": 46,
                "capacity_tr": 500,
            },
            "spec_intro": "Cooling system shall be rated for 50 C outdoor design ambient per DEWA regulation for critical infrastructure.",
            "submittal_intro": "Vendor: Trane RTAF 500 TR air-cooled. Design ambient: 46 C per ASHRAE 0.4% design day. Vendor notes 50 C operation may require capacity derating.",
        },
        "CABLE": {
            "title": "Cabling",
            "requirements": [
                ("CABLE-S1", "temp_rating_c", 90, "C", "DEWA-REG", "SH-8.1"),
                ("CABLE-S1", "category", "Cat6A", "type", "TIA-942", "SH-8.2"),
            ],
            "submittal": {
                "temp_rating_c": 70,
                "category": "Cat6A",
            },
            "spec_intro": "Power cables shall be rated for 90 C conductor temperature per DEWA requirements for UAE climate.",
            "submittal_intro": "Vendor: Ducab PVC/PVC 70 C rated. Standard offering for UAE market. 90 C XLPE variant available.",
        },
        "FIRE": {
            "title": "Fire Suppression",
            "requirements": [
                ("FIRE-S1", "agent", "clean_agent", "type", "UAE-FIRE-CODE", "SH-9.1"),
                ("FIRE-S1", "zones", 2, "count", "DESIGN-BASIS", "SH-9.2"),
            ],
            "submittal": {
                "agent": "clean_agent",
                "zones": 2,
            },
        },
        "STRUCT": {
            "title": "Structural",
            "requirements": [
                ("FLOOR-S1", "load_rating_kpa", 12, "kPa", "DESIGN-BASIS", "SH-10.1"),
            ],
            "submittal": {
                "load_rating_kpa": 12,
            },
        },
    },
    "deviation_cx": {
        ("GEN-S1", "derating_pct"): {
            "cx_test": "FAT-S01", "cx_level": 3,
            "cx_name": "Generator high-ambient load test",
            "week_fail": 24, "severity": "Critical",
            "reason": "Generator not derated for 50 C ambient; will fail to deliver rated power in UAE summer, risking load shedding.",
        },
        ("COOL-S1", "design_ambient_c"): {
            "cx_test": "IST-S01", "cx_level": 4,
            "cx_name": "Cooling peak-ambient stress test",
            "week_fail": 28, "severity": "Critical",
            "reason": "Chiller rated for 46 C but DEWA requires 50 C design ambient; capacity insufficient during peak summer.",
        },
        ("CABLE-S1", "temp_rating_c"): {
            "cx_test": "ITP-S01", "cx_level": 2,
            "cx_name": "Cable temperature rating verification",
            "week_fail": 16, "severity": "Major",
            "reason": "70 C cable rating insufficient for 90 C requirement; accelerated insulation degradation in high-ambient conditions.",
        },
    },
    "true_negative_systems": ["UPS", "FIRE", "STRUCT"],
    "standards": {
        "UPTIME-TIER2": (
            "# Uptime Tier II — Redundant Capacity Components (paraphrased)\n\n"
            "- N+1 component redundancy\n"
            "- Single distribution path\n"
            "- Availability: 99.741%\n"
        ),
        "DEWA-REG": (
            "# DEWA Regulations for Data Centres (paraphrased)\n\n"
            "Dubai Electricity and Water Authority requirements for critical facilities:\n"
            "- Design ambient: 50 C for outdoor equipment sizing\n"
            "- Generator derating: 10% minimum for ambient > 45 C\n"
            "- Cable temperature: 90 C conductor rating for power cables in UAE\n"
            "- Water consumption: reported per kW IT load\n"
        ),
        "DESIGN-BASIS": (
            "# Project Sahara — Design Basis Document\n\n"
            "5 MW Uptime Tier II, Dubai, UAE.\n"
            "- UPS: 400 kW, N+1\n"
            "- Generators: 1000 kVA, N+1, 10% derating for 50 C\n"
            "- Cooling: 500 TR air-cooled, N+1, 50 C design ambient\n"
            "- Cables: 90 C rated\n"
        ),
        "TIA-942": (
            "# TIA-942-C — Data Centre Infrastructure (paraphrased)\n\n"
            "Cat6A minimum for horizontal data cabling.\n"
        ),
    },
    "cx_tests": [
        {"id": "ITP-S01", "level": 2, "name": "Cable temperature rating verification",
         "scheduled_week": 16, "acceptance": "Cable rated >= 90 C"},
        {"id": "FAT-S01", "level": 3, "name": "Generator high-ambient load test",
         "scheduled_week": 24, "acceptance": "Full load at 50 C ambient"},
        {"id": "IST-S01", "level": 4, "name": "Cooling peak-ambient stress test",
         "scheduled_week": 28, "acceptance": "Cooling capacity maintained at 50 C"},
        {"id": "SAT-S01", "level": 5, "name": "Summer sustained operations (72h)",
         "scheduled_week": 34, "acceptance": "No alarms during peak summer operation"},
    ],
    "rfi_log": [
        {"id": "RFI-S01", "system": "GEN", "status": "open",
         "question": "Confirm DEWA derating requirement for generators at 50 C ambient.",
         "resolution": None, "week": 7},
    ],
}


# ---------------------------------------------------------------------------
# Project 5: Cascade — 30 MW Tier IV, Oregon, USA (NEC/NFPA/ASHRAE)
# ---------------------------------------------------------------------------
CASCADE = {
    "project": {
        "name": "Project Cascade",
        "capacity_mw": 30,
        "tier": "Uptime Tier IV",
        "location": "Hillsboro, Oregon, USA",
        "current_week": 14,
        "line_items_total": 12000,
        "active_submittals": 74,
        "total_systems": 8,
        "estimated_completion_week": 52,
        "client": "Cascade Hyperscale Inc.",
        "epc_contractor": "DPR Construction",
        "cx_authority": "Commissioning Agents Inc.",
    },
    "systems": {
        "UPS": {
            "title": "Uninterruptible Power Supply",
            "requirements": [
                ("UPS-C1", "battery_runtime_min", 10, "min", "UPTIME-TIER4", "CS-4.1"),
                ("UPS-C1", "redundancy", "2N", "topology", "UPTIME-TIER4", "CS-4.2"),
                ("UPS-C1", "rated_power_kw", 1000, "kW", "DESIGN-BASIS", "CS-4.3"),
            ],
            "submittal": {
                "battery_runtime_min": 10,
                "redundancy": "2N",
                "rated_power_kw": 1000,
            },
        },
        "GEN": {
            "title": "Standby Generators",
            "requirements": [
                ("GEN-C1", "redundancy", "N+1", "topology", "UPTIME-TIER4", "CS-5.1"),
                ("GEN-C1", "rated_power_kva", 2500, "kVA", "DESIGN-BASIS", "CS-5.2"),
                ("GEN-C1", "epa_tier", "Tier_4", "class", "EPA-40CFR60", "CS-5.3"),
                ("GEN-FUEL", "onsite_fuel_hours", 48, "h", "DESIGN-BASIS", "CS-5.4"),
            ],
            "submittal": {
                "redundancy": "N+1",
                "rated_power_kva": 2500,
                "epa_tier": "Tier_2",
                "onsite_fuel_hours": 48,
            },
            "spec_intro": "Generators shall meet EPA 40 CFR Part 60 Tier 4 emission standards for stationary engines.",
            "submittal_intro": "Vendor: MTU 16V4000 DS2500 2500 kVA. EPA certified Tier 2 (emergency standby). Vendor notes Tier 4 requires SCR/DPF aftertreatment adding $180K/unit and 24-week lead time.",
        },
        "COOL": {
            "title": "Cooling — Evaporative",
            "requirements": [
                ("COOL-C1", "redundancy", "N+2", "topology", "UPTIME-TIER4", "CS-6.1"),
                ("COOL-C1", "wue_target", 0.4, "L/kWh", "DESIGN-BASIS", "CS-6.2"),
                ("COOL-C1", "capacity_tr", 1200, "TR", "DESIGN-BASIS", "CS-6.3"),
            ],
            "submittal": {
                "redundancy": "N+2",
                "wue_target": 0.8,
                "capacity_tr": 1200,
            },
            "spec_intro": "Water Usage Effectiveness (WUE) target 0.4 L/kWh to meet Oregon water conservation requirements.",
            "submittal_intro": "Vendor: Evapco eco-ATWB. WUE: 0.8 L/kWh based on direct evaporative design. Vendor proposes indirect evaporative upgrade to achieve 0.4 L/kWh.",
        },
        "SWGR": {
            "title": "MV Switchgear",
            "requirements": [
                ("SWGR-C1", "short_circuit_rating_ka", 50, "kA", "DESIGN-BASIS", "CS-7.1"),
                ("SWGR-C1", "redundancy", "2N", "topology", "UPTIME-TIER4", "CS-7.2"),
                ("SWGR-C1", "seismic_cert", "ICC_ESR", "standard", "IBC-2021", "CS-7.3"),
            ],
            "submittal": {
                "short_circuit_rating_ka": 50,
                "redundancy": "2N",
                "seismic_cert": "none",
            },
            "spec_intro": "Switchgear shall have ICC-ES evaluation report for seismic certification per IBC 2021 for Seismic Design Category D.",
            "submittal_intro": "Vendor: Eaton VacClad-W 50 kA. Seismic certification: not currently available. Vendor can provide shake-table test report from independent lab.",
        },
        "CABLE": {
            "title": "Cabling",
            "requirements": [
                ("CABLE-C1", "fire_rating", "CMP", "plenum-class", "NFPA-75", "CS-8.1"),
                ("CABLE-C1", "category", "Cat6A", "type", "TIA-942", "CS-8.2"),
            ],
            "submittal": {
                "fire_rating": "CMP",
                "category": "Cat6A",
            },
        },
        "FIRE": {
            "title": "Fire Suppression",
            "requirements": [
                ("FIRE-C1", "agent", "clean_agent", "type", "NFPA-75", "CS-9.1"),
                ("FIRE-C1", "epo_system", "present", "status", "NFPA-75", "CS-9.2"),
                ("FIRE-C1", "zones", 6, "count", "DESIGN-BASIS", "CS-9.3"),
            ],
            "submittal": {
                "agent": "clean_agent",
                "epo_system": "absent",
                "zones": 6,
            },
            "spec_intro": "Emergency Power Off (EPO) system required per NFPA 75 and local AHJ. All data hall zones shall have clean-agent suppression.",
            "submittal_intro": "Vendor: Fike ECARO-25 clean agent. EPO system: not included in fire suppression scope. Vendor assumes EPO by electrical contractor.",
        },
        "BMS": {
            "title": "Building Management System",
            "requirements": [
                ("BMS-C1", "protocol", "BACnet_IP", "standard", "DESIGN-BASIS", "CS-10.1"),
                ("BMS-C1", "monitoring_redundancy", "dual", "topology", "UPTIME-TIER4", "CS-10.2"),
            ],
            "submittal": {
                "protocol": "BACnet_IP",
                "monitoring_redundancy": "dual",
            },
        },
        "STRUCT": {
            "title": "Structural — Seismic Zone",
            "requirements": [
                ("FLOOR-C1", "seismic_design_cat", "SDC_D", "class", "IBC-2021", "CS-11.1"),
                ("FLOOR-C1", "load_rating_kpa", 12, "kPa", "DESIGN-BASIS", "CS-11.2"),
            ],
            "submittal": {
                "seismic_design_cat": "SDC_D",
                "load_rating_kpa": 12,
            },
        },
    },
    "deviation_cx": {
        ("GEN-C1", "epa_tier"): {
            "cx_test": "FAT-C01", "cx_level": 3,
            "cx_name": "Generator emissions certification",
            "week_fail": 28, "severity": "Critical",
            "reason": "EPA Tier 2 does not meet Tier 4 emission requirements; facility will fail air quality permit.",
        },
        ("COOL-C1", "wue_target"): {
            "cx_test": "IST-C01", "cx_level": 4,
            "cx_name": "Water usage efficiency test",
            "week_fail": 40, "severity": "Major",
            "reason": "WUE 0.8 L/kWh double the 0.4 target; exceeds Oregon water use permit allocation.",
        },
        ("SWGR-C1", "seismic_cert"): {
            "cx_test": "FAT-C02", "cx_level": 3,
            "cx_name": "Switchgear seismic qualification",
            "week_fail": 26, "severity": "Critical",
            "reason": "No seismic certification for SDC D; switchgear may fail during Cascadia subduction zone event.",
        },
        ("FIRE-C1", "epo_system"): {
            "cx_test": "IST-C02", "cx_level": 4,
            "cx_name": "EPO system functional test",
            "week_fail": 42, "severity": "Critical",
            "reason": "EPO system absent; required by NFPA 75 and local AHJ for emergency de-energisation of IT spaces.",
        },
    },
    "true_negative_systems": ["UPS", "CABLE", "BMS", "STRUCT"],
    "standards": {
        "UPTIME-TIER4": (
            "# Uptime Tier IV — Fault Tolerance (paraphrased)\n\n"
            "2N power distribution, N+2 cooling, 10 min battery, 24h fuel minimum.\n"
            "Concurrent maintainability AND fault tolerance required.\n"
        ),
        "EPA-40CFR60": (
            "# EPA 40 CFR Part 60 — Stationary Engine Emission Standards (paraphrased)\n\n"
            "Emission tiers for stationary compression-ignition engines:\n"
            "- Tier 1 (pre-2006): basic limits\n"
            "- Tier 2 (2007-2014): reduced PM and NOx\n"
            "- Tier 3 (interim): further reductions\n"
            "- Tier 4 (2015+): near-zero emissions, requires DPF + SCR\n\n"
            "Emergency standby engines may qualify for Tier 2 exemption only if\n"
            "operation limited to <100 hours/year in non-emergency use.\n"
            "Data centres with >500 hours/year runtime require Tier 4.\n"
        ),
        "IBC-2021": (
            "# International Building Code 2021 — Seismic Design (paraphrased)\n\n"
            "Seismic Design Categories (SDC) A through F based on site class and location.\n"
            "- SDC D: moderate-to-high seismic risk (Portland/Hillsboro, Oregon)\n"
            "- Equipment anchorage: ICC-ES evaluation required\n"
            "- Raised floor: special seismic bracing per ASCE 7-22\n"
            "- Essential facilities: Importance Factor Ie = 1.5\n"
        ),
        "NFPA-75": (
            "# NFPA 75 — Fire Protection of IT Equipment (paraphrased)\n\n"
            "- CMP cable in plenum spaces\n"
            "- Clean-agent suppression for IT rooms\n"
            "- Emergency Power Off (EPO) required per Section 8.6\n"
            "- EPO accessible within 5 feet of main exit\n"
        ),
        "TIA-942": (
            "# TIA-942-C — Data Centre Infrastructure (paraphrased)\n\n"
            "Cat6A minimum for horizontal data cabling.\n"
        ),
        "DESIGN-BASIS": (
            "# Project Cascade — Design Basis Document\n\n"
            "30 MW Uptime Tier IV, Hillsboro, Oregon, USA.\n"
            "- UPS: 1000 kW, 2N, 10 min\n"
            "- Generators: 2500 kVA, N+1, EPA Tier 4, 48h fuel\n"
            "- Cooling: 1200 TR evaporative, N+2, WUE 0.4 L/kWh\n"
            "- Seismic: SDC D per IBC 2021\n"
            "- Fire: NFPA 75, EPO required, clean agent\n"
        ),
    },
    "cx_tests": [
        {"id": "ITP-C01", "level": 1, "name": "Equipment receipt inspection",
         "scheduled_week": 18, "acceptance": "Documentation verified"},
        {"id": "FAT-C01", "level": 3, "name": "Generator emissions certification",
         "scheduled_week": 28, "acceptance": "EPA Tier 4 documentation verified"},
        {"id": "FAT-C02", "level": 3, "name": "Switchgear seismic qualification",
         "scheduled_week": 26, "acceptance": "ICC-ES or shake-table cert provided"},
        {"id": "IST-C01", "level": 4, "name": "Water usage efficiency test",
         "scheduled_week": 40, "acceptance": "WUE <= 0.4 L/kWh measured"},
        {"id": "IST-C02", "level": 4, "name": "EPO system functional test",
         "scheduled_week": 42, "acceptance": "EPO de-energises all IT loads"},
        {"id": "SAT-C01", "level": 5, "name": "72-hour sustained operations",
         "scheduled_week": 48, "acceptance": "No critical alarms"},
    ],
    "rfi_log": [
        {"id": "RFI-C01", "system": "GEN", "status": "open",
         "question": "Will facility operate >100 h/yr in non-emergency mode (maintenance testing)?",
         "resolution": None, "week": 10},
        {"id": "RFI-C02", "system": "FIRE", "status": "open",
         "question": "Confirm EPO scope responsibility — fire suppression or electrical contractor?",
         "resolution": None, "week": 11},
    ],
}


# ---------------------------------------------------------------------------
# Project 6: Yangtze — 50 MW Tier IV, Shanghai, China (GB 50174)
# ---------------------------------------------------------------------------
YANGTZE = {
    "project": {
        "name": "Project Yangtze",
        "capacity_mw": 50,
        "tier": "GB 50174 Grade A",
        "location": "Shanghai, China",
        "current_week": 12,
        "line_items_total": 18000,
        "active_submittals": 102,
        "total_systems": 8,
        "estimated_completion_week": 56,
        "client": "Yangtze Digital Technology Co. Ltd.",
        "epc_contractor": "China State Construction Engineering",
        "cx_authority": "Bureau Veritas China",
    },
    "systems": {
        "UPS": {
            "title": "Uninterruptible Power Supply",
            "requirements": [
                ("UPS-Y1", "battery_runtime_min", 15, "min", "GB-50174", "YZ-4.1"),
                ("UPS-Y1", "redundancy", "2N", "topology", "GB-50174", "YZ-4.2"),
                ("UPS-Y1", "rated_power_kw", 1500, "kW", "DESIGN-BASIS", "YZ-4.3"),
            ],
            "submittal": {
                "battery_runtime_min": 10,
                "redundancy": "2N",
                "rated_power_kw": 1500,
            },
            "spec_intro": "GB 50174 Grade A requires minimum 15 minutes battery for facilities >10 MW with dual utility feeds.",
            "submittal_intro": "Vendor: Huawei UPS5000-H 1500 kW. Battery: 10 min at full load per standard configuration. 15 min requires additional battery cabinet.",
        },
        "GEN": {
            "title": "Diesel Generators",
            "requirements": [
                ("GEN-Y1", "redundancy", "N+1", "topology", "GB-50174", "YZ-5.1"),
                ("GEN-Y1", "rated_power_kva", 3000, "kVA", "DESIGN-BASIS", "YZ-5.2"),
                ("GEN-FUEL", "onsite_fuel_hours", 24, "h", "GB-50174", "YZ-5.4"),
            ],
            "submittal": {
                "redundancy": "N+1",
                "rated_power_kva": 3000,
                "onsite_fuel_hours": 24,
            },
        },
        "COOL": {
            "title": "Cooling — Liquid Cooling Hybrid",
            "requirements": [
                ("COOL-Y1", "redundancy", "N+2", "topology", "GB-50174", "YZ-6.1"),
                ("COOL-Y1", "rack_power_kw", 30, "kW", "DESIGN-BASIS", "YZ-6.2"),
                ("COOL-Y1", "liquid_cooling_pct", 60, "%", "DESIGN-BASIS", "YZ-6.3"),
            ],
            "submittal": {
                "redundancy": "N+2",
                "rack_power_kw": 20,
                "liquid_cooling_pct": 60,
            },
            "spec_intro": "High-density design with 30 kW/rack average, 60% direct liquid cooling for GPU clusters.",
            "submittal_intro": "Vendor: Sugon Liquidcool MicroModule. Per-rack cooling capacity: 20 kW per CDU loop. Vendor states 30 kW requires dual-CDU configuration per rack.",
        },
        "CABLE": {
            "title": "Cabling",
            "requirements": [
                ("CABLE-Y1", "fire_rating", "B1_class", "GB-standard", "GB-31247", "YZ-8.1"),
                ("CABLE-Y1", "category", "Cat6A", "type", "GB-50174", "YZ-8.2"),
            ],
            "submittal": {
                "fire_rating": "B1_class",
                "category": "Cat6A",
            },
        },
        "BMS": {
            "title": "Building Management & Government Reporting",
            "requirements": [
                ("BMS-Y1", "protocol", "BACnet_IP", "standard", "DESIGN-BASIS", "YZ-9.1"),
                ("BMS-Y1", "gov_fire_reporting", "connected", "status", "GB-50174", "YZ-9.2"),
                ("BMS-Y1", "pue_reporting", "real_time", "type", "MIIT-REG", "YZ-9.3"),
            ],
            "submittal": {
                "protocol": "BACnet_IP",
                "gov_fire_reporting": "disconnected",
                "pue_reporting": "real_time",
            },
            "spec_intro": "BMS shall connect to municipal fire bureau reporting system per GB 50174 and report PUE to MIIT in real time.",
            "submittal_intro": "Vendor: Delta InfraSuite Manager. Government fire reporting interface: not included (API available, integration requires municipal approval process).",
        },
        "FIRE": {
            "title": "Fire Suppression",
            "requirements": [
                ("FIRE-Y1", "agent", "clean_agent", "type", "GB-50174", "YZ-10.1"),
                ("FIRE-Y1", "zones", 10, "count", "DESIGN-BASIS", "YZ-10.2"),
            ],
            "submittal": {
                "agent": "clean_agent",
                "zones": 10,
            },
        },
        "PDU": {
            "title": "Power Distribution Units",
            "requirements": [
                ("PDU-Y1", "metering", "per_outlet", "type", "DESIGN-BASIS", "YZ-11.1"),
                ("PDU-Y1", "redundancy", "A+B", "topology", "GB-50174", "YZ-11.2"),
            ],
            "submittal": {
                "metering": "per_outlet",
                "redundancy": "A+B",
            },
        },
        "STRUCT": {
            "title": "Structural",
            "requirements": [
                ("FLOOR-Y1", "load_rating_kpa", 16, "kPa", "DESIGN-BASIS", "YZ-12.1"),
                ("FLOOR-Y1", "seismic_intensity", "VII", "class", "GB-50011", "YZ-12.2"),
            ],
            "submittal": {
                "load_rating_kpa": 16,
                "seismic_intensity": "VII",
            },
        },
    },
    "deviation_cx": {
        ("UPS-Y1", "battery_runtime_min"): {
            "cx_test": "IST-Y01", "cx_level": 4,
            "cx_name": "UPS battery autonomy test",
            "week_fail": 42, "severity": "Critical",
            "reason": "Battery runtime 10 min below GB 50174 Grade A requirement of 15 min for >10 MW facilities.",
        },
        ("COOL-Y1", "rack_power_kw"): {
            "cx_test": "IST-Y02", "cx_level": 4,
            "cx_name": "Per-rack cooling capacity test",
            "week_fail": 44, "severity": "Critical",
            "reason": "CDU cooling capacity 20 kW/rack below 30 kW design requirement; GPU clusters will throttle.",
        },
        ("BMS-Y1", "gov_fire_reporting"): {
            "cx_test": "IST-Y03", "cx_level": 4,
            "cx_name": "Government fire reporting integration test",
            "week_fail": 48, "severity": "Major",
            "reason": "Municipal fire bureau connection absent; facility cannot obtain occupancy permit without connected fire reporting.",
        },
    },
    "true_negative_systems": ["GEN", "CABLE", "FIRE", "PDU", "STRUCT"],
    "standards": {
        "GB-50174": (
            "# GB 50174-2017 — Code for Design of Data Centres (paraphrased)\n\n"
            "Chinese national standard for data centre design. Three grades:\n"
            "- Grade A: highest availability, equivalent to Tier III+/IV\n"
            "- Grade B: moderate availability\n"
            "- Grade C: basic\n\n"
            "## Grade A requirements\n"
            "- UPS: 2N topology, >= 15 min battery for >10 MW\n"
            "- Cooling: N+2 redundancy\n"
            "- Generator: N+1, 24h fuel\n"
            "- Fire: connected to municipal fire bureau reporting\n"
            "- PUE: reported to MIIT in real time for facilities >5000 racks\n"
        ),
        "GB-31247": (
            "# GB 31247 — Cable Fire Performance (paraphrased)\n\n"
            "Chinese cable fire rating system:\n"
            "- B1 class: flame retardant, limited smoke\n"
            "- B2 class: basic flame retardant\n"
            "B1 class required for data centre plenum areas.\n"
        ),
        "GB-50011": (
            "# GB 50011-2010 — Seismic Design of Buildings (paraphrased)\n\n"
            "Seismic intensity classification for China:\n"
            "- Intensity VI: minor damage expected\n"
            "- Intensity VII: moderate (Shanghai)\n"
            "- Intensity VIII: significant (some western regions)\n"
            "Essential facilities (data centres >10 MW): importance factor 1.5\n"
        ),
        "MIIT-REG": (
            "# MIIT Data Centre Energy Regulations (paraphrased)\n\n"
            "Ministry of Industry and Information Technology regulations:\n"
            "- PUE reporting mandatory for facilities >5000 racks\n"
            "- PUE target: <= 1.25 for new builds in eastern China\n"
            "- Real-time monitoring and quarterly reporting to MIIT portal\n"
        ),
        "DESIGN-BASIS": (
            "# Project Yangtze — Design Basis Document\n\n"
            "50 MW GB 50174 Grade A, Shanghai, China.\n"
            "- UPS: 1500 kW, 2N, 15 min battery\n"
            "- Cooling: N+2, 30 kW/rack, 60% liquid\n"
            "- BMS: BACnet/IP, gov fire reporting, MIIT PUE reporting\n"
            "- Seismic: Intensity VII per GB 50011\n"
        ),
    },
    "cx_tests": [
        {"id": "ITP-Y01", "level": 1, "name": "Equipment receipt inspection",
         "scheduled_week": 18, "acceptance": "Documentation verified"},
        {"id": "IST-Y01", "level": 4, "name": "UPS battery autonomy test",
         "scheduled_week": 42, "acceptance": "Battery >= 15 min at rated load"},
        {"id": "IST-Y02", "level": 4, "name": "Per-rack cooling capacity test",
         "scheduled_week": 44, "acceptance": "30 kW sustained per rack position"},
        {"id": "IST-Y03", "level": 4, "name": "Government fire reporting integration test",
         "scheduled_week": 48, "acceptance": "Fire events reach municipal bureau within 30s"},
        {"id": "SAT-Y01", "level": 5, "name": "72-hour sustained operations",
         "scheduled_week": 52, "acceptance": "No critical alarms, PUE < 1.25"},
    ],
    "rfi_log": [
        {"id": "RFI-Y01", "system": "UPS", "status": "open",
         "question": "Confirm 15 min battery requirement per GB 50174 Grade A for >10 MW.",
         "resolution": None, "week": 8},
        {"id": "RFI-Y02", "system": "BMS", "status": "open",
         "question": "What is the timeline for municipal fire bureau API access approval?",
         "resolution": None, "week": 9},
    ],
}


ALL_PROJECTS = {
    "vajra": VAJRA,
    "nordic": NORDIC,
    "sahara": SAHARA,
    "cascade": CASCADE,
    "yangtze": YANGTZE,
}


def build_all():
    import shutil
    if ROOT.exists():
        shutil.rmtree(ROOT)

    results = []
    for pid, cfg in ALL_PROJECTS.items():
        r = build_project(pid, cfg)
        results.append(r)
        print(f"  {r['id']:12s}  {r['name']:25s}  "
              f"sys={r['systems']:2d}  reqs={r['requirements']:3d}  "
              f"devs={r['deviations']:2d}  tn={r['tn_systems']}")

    totals = {
        "projects": len(results),
        "total_systems": sum(r["systems"] for r in results),
        "total_requirements": sum(r["requirements"] for r in results),
        "total_deviations": sum(r["deviations"] for r in results),
    }
    print(f"\n  TOTAL: {totals['projects']} projects, "
          f"{totals['total_systems']} systems, "
          f"{totals['total_requirements']} requirements, "
          f"{totals['total_deviations']} deviations")

    manifest = {
        "generated_by": "data/generate_projects.py",
        "projects": {
            r["id"]: {
                "name": r["name"],
                "path": f"data/projects/{r['id']}",
                "systems": r["systems"],
                "requirements": r["requirements"],
                "deviations": r["deviations"],
            }
            for r in results
        },
        "meghdoot": {
            "name": "Project Meghdoot",
            "path": "data/corpus",
            "note": "Original project, maintained separately in data/corpus/",
        },
    }
    w(ROOT / "manifest.json", json.dumps(manifest, indent=2))

    return totals


if __name__ == "__main__":
    if "--list" in sys.argv:
        print("meghdoot  (data/corpus/)")
        for pid in ALL_PROJECTS:
            print(f"{pid:12s}  (data/projects/{pid}/)")
        sys.exit(0)

    print("Pramaan Multi-Project Corpus Generator")
    print("=" * 55)
    build_all()
