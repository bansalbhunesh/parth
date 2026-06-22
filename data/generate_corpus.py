"""
Pramaan — Synthetic EPC corpus generator for "Project Meghdoot"
A 40 MW, Uptime Tier IV hyperscale data centre (fictional, India).

Generates a realistic, LABELLED corpus so the deviation-detection pipeline can
be evaluated with real precision/recall. Deterministic: no LLM required to
produce the corpus, so it is reproducible and auditable.

v2: Expanded to 10 systems with richer prose, deeper technical detail in specs
and submittals, more realistic RFI log, and a comprehensive Cx plan covering
L1-L5 commissioning levels.
"""

import json
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
    "total_systems": 10,
    "estimated_completion_week": 52,
    "client": "Meghdoot Digital Infrastructure Pvt. Ltd.",
    "epc_contractor": "Patel-Larsen JV",
    "cx_authority": "DCx International (India)",
}

SYSTEMS = {
    "UPS": {
        "title": "Uninterruptible Power Supply & Battery",
        "requirements": [
            ("UPS-02", "battery_runtime_min", 10, "min", "UPTIME-TIER4", "DB-4.3"),
            ("UPS-02", "redundancy", "2N", "topology", "UPTIME-TIER4", "DB-4.1"),
            ("UPS-02", "rated_power_kw", 1200, "kW", "DESIGN-BASIS", "DB-4.2"),
            ("UPS-02", "efficiency_pct", 96, "%", "DESIGN-BASIS", "DB-4.5"),
        ],
        "submittal": {
            "battery_runtime_min": 7,
            "redundancy": "2N",
            "rated_power_kw": 1200,
            "efficiency_pct": 96,
        },
        "prose": {
            "spec_intro": (
                "The UPS system shall provide uninterrupted, conditioned power to "
                "the critical IT load during any single-point utility or generator "
                "failure event, inclusive of concurrent maintenance windows. Battery "
                "strings shall be sized for full-load ride-through per the Tier IV "
                "design basis, accounting for end-of-life capacity degradation at "
                "year 10 and an ambient temperature envelope of 20-35 deg C."
            ),
            "submittal_intro": (
                "Vendor: Vertiv Liebert EXL S1 1200 kW, IGBT online double-conversion.\n"
                "Battery: VRLA AGM, 480 V string configuration, C10 rate.\n"
                "The proposed battery bank has been sized for the specified load profile "
                "at a discharge rate that accounts for standard temperature corrections. "
                "Runtime at full rated load is 7 minutes based on the vendor's sizing "
                "tool at 25 deg C ambient, which the vendor considers adequate for "
                "generator start-up overlap in a 2N topology."
            ),
        },
    },
    "GEN": {
        "title": "Diesel Generators & Fuel Storage",
        "requirements": [
            ("GEN-FUEL", "onsite_fuel_hours", 24, "h", "UPTIME-TIER4", "DB-5.4"),
            ("GEN-01", "redundancy", "N+1", "topology", "UPTIME-TIER4", "DB-5.1"),
            ("GEN-01", "rated_power_kva", 2500, "kVA", "DESIGN-BASIS", "DB-5.2"),
            ("GEN-01", "start_time_sec", 10, "s", "DESIGN-BASIS", "DB-5.3"),
        ],
        "submittal": {
            "onsite_fuel_hours": 12,
            "redundancy": "N+1",
            "rated_power_kva": 2500,
            "start_time_sec": 10,
        },
        "prose": {
            "spec_intro": (
                "Standby diesel generators shall support the entire critical and "
                "mechanical load for a sustained utility outage. On-site bulk fuel "
                "storage shall provide a minimum of 24 hours at full rated load per "
                "the Tier IV design basis, ensuring operational continuity without "
                "dependence on fuel delivery during the initial outage period."
            ),
            "submittal_intro": (
                "Vendor: Cummins QSK60-G23 2500 kVA, 50 Hz, prime-rated.\n"
                "Fuel: Dual belly-tank configuration, total capacity 15,000 litres.\n"
                "The proposed fuel capacity provides approximately 12 hours of "
                "autonomy at rated load based on the manufacturer's specific fuel "
                "consumption data of 214 g/kWh. The vendor notes that fuel delivery "
                "contracts can supplement on-site storage for extended outages."
            ),
        },
    },
    "COOL": {
        "title": "Cooling — Chillers / CRAH / Liquid Loop",
        "requirements": [
            ("COOL-LOOP", "redundancy", "N+2", "topology", "UPTIME-TIER4", "DB-6.1"),
            ("CRAH", "supply_air_temp_c", 24, "C", "DESIGN-BASIS", "DB-6.3"),
            ("CHILLER", "capacity_tr", 1500, "TR", "DESIGN-BASIS", "DB-6.2"),
            ("COOL-LOOP", "delta_t_c", 10, "C", "DESIGN-BASIS", "DB-6.4"),
        ],
        "submittal": {
            "redundancy": "N+1",
            "supply_air_temp_c": 24,
            "capacity_tr": 1500,
            "delta_t_c": 10,
        },
        "prose": {
            "spec_intro": (
                "The chilled-water cooling plant shall maintain ASHRAE-recommended "
                "supply conditions across all white-space zones. Redundancy shall "
                "satisfy Tier IV fault tolerance: the system must tolerate one chiller "
                "failure while another chiller is in planned maintenance, requiring "
                "N+2 minimum."
            ),
            "submittal_intro": (
                "Vendor: York YVWA 1500 TR water-cooled screw chillers.\n"
                "Configuration: 4 x 1500 TR chillers in N+1 arrangement.\n"
                "The chiller plant is proposed as 3 duty + 1 standby (N+1) which "
                "the vendor notes provides 33% excess capacity above the N requirement. "
                "The P&ID shows a common header with isolation valves per chiller."
            ),
        },
    },
    "SWGR": {
        "title": "MV/LV Switchgear",
        "requirements": [
            ("SWGR-MV", "short_circuit_rating_ka", 50, "kA", "DESIGN-BASIS", "DB-7.2"),
            ("SWGR-MV", "redundancy", "2N", "topology", "UPTIME-TIER4", "DB-7.1"),
            ("SWGR-MV", "arc_flash_rating", "Type_2B", "class", "DESIGN-BASIS", "DB-7.3"),
        ],
        "submittal": {
            "short_circuit_rating_ka": 40,
            "redundancy": "2N",
            "arc_flash_rating": "Type_2B",
        },
        "prose": {
            "spec_intro": (
                "MV switchgear shall be rated for the full prospective fault level "
                "as determined by the project fault study. The minimum short-circuit "
                "withstand rating shall be 50 kA for 1 second, coordinated with "
                "upstream utility protection."
            ),
            "submittal_intro": (
                "Vendor: ABB UniGear ZS2, 11 kV air-insulated.\n"
                "The switchgear is offered with a fault withstand rating of 40 kA "
                "for 1 second, which is the standard catalogue rating for this "
                "product range. ABB notes that 50 kA ratings are available as a "
                "special order with extended lead times."
            ),
        },
    },
    "CABLE": {
        "title": "Power & Data Cabling",
        "requirements": [
            ("CABLE-DC", "fire_rating", "CMP", "plenum-class", "NFPA-75", "DB-8.4"),
            ("CABLE-DC", "category", "Cat6A", "type", "TIA-942", "DB-8.1"),
            ("CABLE-DC", "max_bundle_size", 48, "cables", "BICSI-002", "DB-8.5"),
        ],
        "submittal": {
            "fire_rating": "CMR",
            "category": "Cat6A",
            "max_bundle_size": 48,
        },
        "prose": {
            "spec_intro": (
                "Data cabling within IT spaces classified as plenum-rated areas "
                "shall carry a CMP (Communications Multipurpose Plenum) fire rating "
                "per NFPA 75 room classification requirements. CMR (riser-rated) "
                "cable is NOT acceptable in plenum spaces."
            ),
            "submittal_intro": (
                "Vendor: CommScope Systimax GigaSPEED X10D Cat6A U/UTP.\n"
                "Fire rating: CMR (Communications Multipurpose Riser).\n"
                "The vendor has proposed CMR-rated cable which meets the riser "
                "classification. The vendor states this is the standard offering "
                "for data centre deployments in their product line."
            ),
        },
    },
    "BMS": {
        "title": "Building Management & EPMS",
        "requirements": [
            ("BMS", "critical_alarm_points", "complete", "set", "DESIGN-BASIS", "DB-9.5"),
            ("BMS", "monitoring_redundancy", "dual", "topology", "UPTIME-TIER4", "DB-9.1"),
            ("BMS", "protocol", "BACnet_IP", "standard", "DESIGN-BASIS", "DB-9.3"),
        ],
        "submittal": {
            "critical_alarm_points": "missing:leak_detection",
            "monitoring_redundancy": "dual",
            "protocol": "BACnet_IP",
        },
        "prose": {
            "spec_intro": (
                "The BMS/EPMS shall provide complete visibility of all critical "
                "infrastructure systems with a comprehensive alarm point list. "
                "The critical alarm set SHALL include, at minimum: power failure, "
                "generator status, UPS alarms, temperature exceedance, humidity "
                "exceedance, leak detection, fire panel interface, and security "
                "breach. Omission of any critical alarm point is a non-conformance."
            ),
            "submittal_intro": (
                "Vendor: Schneider Electric EcoStruxure Building Operation.\n"
                "Protocol: BACnet/IP with BACnet/MSTP bridging for field devices.\n"
                "The proposed alarm point list covers 847 points across all major "
                "systems. Note: the leak-detection subsystem interface is pending "
                "coordination with the leak-detection vendor and is not included "
                "in this revision of the points list."
            ),
        },
    },
    "FIRE": {
        "title": "Fire Suppression",
        "requirements": [
            ("FIRE-SUP", "agent", "clean_agent", "type", "NFPA-75", "DB-10.2"),
            ("FIRE-SUP", "zones", 8, "count", "DESIGN-BASIS", "DB-10.1"),
            ("FIRE-SUP", "vesda_coverage", "complete", "set", "DESIGN-BASIS", "DB-10.3"),
        ],
        "submittal": {
            "agent": "clean_agent",
            "zones": 8,
            "vesda_coverage": "complete",
        },
    },
    "BUSWAY": {
        "title": "Busway Distribution",
        "requirements": [
            ("BUSWAY", "rating_a", 4000, "A", "DESIGN-BASIS", "DB-11.1"),
            ("BUSWAY", "redundancy", "2N", "topology", "UPTIME-TIER4", "DB-11.2"),
            ("BUSWAY", "ip_rating", "IP54", "class", "DESIGN-BASIS", "DB-11.3"),
        ],
        "submittal": {
            "rating_a": 4000,
            "redundancy": "2N",
            "ip_rating": "IP54",
        },
    },
    "PDU": {
        "title": "Power Distribution Units",
        "requirements": [
            ("PDU-RACK", "metering", "per_outlet", "type", "DESIGN-BASIS", "DB-12.1"),
            ("PDU-RACK", "redundancy", "A+B", "topology", "UPTIME-TIER4", "DB-12.2"),
            ("PDU-RACK", "rated_current_a", 63, "A", "DESIGN-BASIS", "DB-12.3"),
        ],
        "submittal": {
            "metering": "per_outlet",
            "redundancy": "A+B",
            "rated_current_a": 63,
        },
    },
    "STRUCT": {
        "title": "Structural — Raised Floor & Seismic",
        "requirements": [
            ("FLOOR", "load_rating_kpa", 12, "kPa", "DESIGN-BASIS", "DB-13.1"),
            ("FLOOR", "seismic_zone", "Zone_IV", "class", "IS-1893", "DB-13.2"),
            ("FLOOR", "height_mm", 900, "mm", "DESIGN-BASIS", "DB-13.3"),
        ],
        "submittal": {
            "load_rating_kpa": 12,
            "seismic_zone": "Zone_IV",
            "height_mm": 900,
        },
    },
}

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
        "- Continuous cooling maintained under any single failure.\n"
        "- No single point of failure in any critical distribution path.\n\n"
        "## Key numerical thresholds\n"
        "- Battery autonomy: minimum 10 minutes at full rated load (accounts for "
        "generator start + transfer time under worst-case).\n"
        "- On-site fuel: minimum 24 hours at rated load without refuelling.\n"
        "- Cooling: N+2 redundancy (one unit in maintenance, one in fault, N serving).\n"
        "- Power distribution: 2N from utility entrance to rack PDU.\n"
    ),
    "TIA-942": (
        "# TIA-942 — Telecom Infrastructure (paraphrased summary)\n\n"
        "Cabling, pathways and spaces sized and rated for the data centre rating "
        "class. Structured cabling category and redundancy must match the design "
        "rating class for the facility.\n\n"
        "Key requirements:\n"
        "- Minimum Cat6A for all horizontal data cabling.\n"
        "- Redundant pathway routing for rated class 4 facilities.\n"
        "- Cable management to prevent exceeding bend radius limits.\n"
    ),
    "BICSI-002": (
        "# BICSI-002 — Data Centre Design Best Practice (paraphrased summary)\n\n"
        "Coordinated design across power, cooling, cabling and monitoring; "
        "redundancy of one subsystem must not be undermined by a weaker adjacent "
        "subsystem.\n\n"
        "Key requirements:\n"
        "- Maximum 48 cables per bundle to maintain thermal management.\n"
        "- Pathway fill ratios per cable tray sizing.\n"
        "- Coordination between electrical and mechanical routing.\n"
    ),
    "NFPA-75": (
        "# NFPA 75 — Fire Protection of IT Equipment (paraphrased summary)\n\n"
        "Materials in IT/plenum spaces must meet the fire performance for the room "
        "classification. Cable fire-rating must satisfy the plenum/room class; "
        "clean-agent suppression is typical for critical IT rooms.\n\n"
        "Key requirements:\n"
        "- CMP-rated cable mandatory in plenum-classified spaces (CMR is NOT acceptable).\n"
        "- Clean-agent suppression in rooms with active IT equipment.\n"
        "- VESDA very early smoke detection recommended for high-value IT rooms.\n"
    ),
    "DESIGN-BASIS": (
        "# Project Meghdoot — Design Basis (owner requirements)\n\n"
        "Owner's project requirements (OPR) that set capacities, set-points and "
        "topology targets for a 40 MW Tier IV facility.\n\n"
        "Key parameters:\n"
        "- Total IT load: 40 MW across 8 data halls.\n"
        "- UPS: 1200 kW modules, 2N topology, 10 min battery autonomy.\n"
        "- Generators: 2500 kVA units, N+1, 24 h fuel autonomy.\n"
        "- Cooling: 1500 TR chillers, N+2, 24 C supply air.\n"
        "- Switchgear: 50 kA fault rating (per fault study), 2N topology.\n"
        "- Cabling: Cat6A CMP-rated in all IT/plenum spaces.\n"
        "- BMS: complete critical alarm set including leak detection.\n"
    ),
    "IS-1893": (
        "# IS 1893 — Indian Seismic Code (paraphrased summary)\n\n"
        "Navi Mumbai falls in Seismic Zone III/IV. For critical infrastructure "
        "facilities the design shall assume the higher classification. Equipment "
        "anchorage and raised-floor systems shall be designed and tested for the "
        "applicable zone.\n"
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

    for sys_id, sys in SYSTEMS.items():
        prose = sys.get("prose", {})

        spec_md = [f"# {PROJECT['name']} — Design Basis: {sys['title']}",
                   f"_System: {sys_id} · {PROJECT['tier']} · {PROJECT['capacity_mw']} MW_",
                   f"_Client: {PROJECT['client']}_",
                   f"_EPC: {PROJECT['epc_contractor']}_\n"]
        if prose.get("spec_intro"):
            spec_md.append(f"## Overview\n\n{prose['spec_intro']}\n")
        spec_md.append("## Requirements\n")
        for r in sys["requirements"]:
            spec_md.append(fmt_req(r))
            comp, param, val, unit, std, clause = r
            requirements_struct.append({
                "system": sys_id, "component": comp, "parameter": param,
                "required_value": val, "unit": unit,
                "standard_ref": std, "clause": clause,
            })
        w(ROOT / "specs" / f"{sys_id}.md", "\n".join(spec_md) + "\n")

        sub_md = [f"# Vendor Submittal — {sys['title']} ({sys_id})",
                  f"_Project: {PROJECT['name']} · Submittal rev B_\n"]
        if prose.get("submittal_intro"):
            sub_md.append(f"## Vendor Notes\n\n{prose['submittal_intro']}\n")
        sub_md.append("## Provided values\n")
        for r in sys["requirements"]:
            comp, param, val, unit, std, clause = r
            provided = sys["submittal"][param]
            sub_md.append(f"- **{comp}** — {param.replace('_', ' ')}: "
                          f"**{provided} {unit}** (vendor datasheet)")
            submittals_struct.append({
                "system": sys_id, "component": comp, "parameter": param,
                "provided_value": provided, "unit": unit,
            })

            if str(provided) != str(val):
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

    for std_id, text in STANDARDS.items():
        w(ROOT / "standards" / f"{std_id}.md", text)

    cx_plan = {
        "project": PROJECT["name"],
        "cx_authority": PROJECT["cx_authority"],
        "levels": {
            "1": "Factory inspections & witness tests (ITP)",
            "2": "Installation verification & inspection (ITP)",
            "3": "Functional / factory acceptance test (FAT)",
            "4": "Integrated systems test (IST)",
            "5": "Owner acceptance & sustained operations",
        },
        "tests": [
            {"id": "ITP-01", "level": 1, "name": "Equipment receipt inspection",
             "scheduled_week": 16, "acceptance": "Visual + documentation check"},
            {"id": "ITP-02", "level": 2,
             "name": "Cable fire-rating / plenum compliance inspection",
             "scheduled_week": 22,
             "acceptance": "Cable marking matches CMP plenum requirement"},
            {"id": "FAT-01", "level": 3, "name": "UPS module load-bank test",
             "scheduled_week": 24, "acceptance": "Full load sustained 4 hours"},
            {"id": "FAT-02", "level": 3, "name": "Generator load-bank test",
             "scheduled_week": 26, "acceptance": "110% load for 2 hours"},
            {"id": "FAT-03", "level": 3,
             "name": "Protection coordination / fault-withstand verification",
             "scheduled_week": 30,
             "acceptance": "Fault withstand >= calculated prospective fault level"},
            {"id": "IST-01", "level": 4, "name": "Utility failure simulation",
             "scheduled_week": 34, "acceptance": "Zero IT load impact"},
            {"id": "IST-05", "level": 4,
             "name": "Single-path maintenance simulation",
             "scheduled_week": 36, "acceptance": "Full load on single path"},
            {"id": "IST-07", "level": 4,
             "name": "Load transfer under maintenance (battery autonomy)",
             "scheduled_week": 38,
             "acceptance": "Battery sustains load during transfer window"},
            {"id": "IST-09", "level": 4,
             "name": "Cooling failover under fault + maintenance",
             "scheduled_week": 39,
             "acceptance": "Temperature maintained within ASHRAE envelope"},
            {"id": "IST-11", "level": 4,
             "name": "Sustained utility-outage run (fuel autonomy)",
             "scheduled_week": 41,
             "acceptance": "Generators sustain full design-duration outage"},
            {"id": "IST-14", "level": 4,
             "name": "Monitoring & alarm verification",
             "scheduled_week": 40,
             "acceptance": "All critical alarms fire and are received by BMS/NOC"},
            {"id": "IST-15", "level": 4, "name": "Full-facility failover drill",
             "scheduled_week": 44, "acceptance": "Zero downtime during drill"},
            {"id": "SAT-01", "level": 5,
             "name": "72-hour sustained operations test",
             "scheduled_week": 48, "acceptance": "No critical alarms for 72 hours"},
        ],
    }
    w(ROOT / "commissioning" / "cx_plan.json", json.dumps(cx_plan, indent=2))

    rfi_log = [
        {"id": "RFI-003", "system": "STRUCT", "status": "resolved",
         "question": "Confirm raised-floor height requirement for cable routing "
                     "below floor in data halls 1-4.",
         "resolution": "900 mm minimum confirmed per design basis DB-13.3. "
                       "Vendor shall provide 900 mm clear height.",
         "week": 3},
        {"id": "RFI-009", "system": "SWGR", "status": "resolved",
         "question": "Confirm prospective fault level for MV switchgear sizing.",
         "resolution": "Fault study returned 47.6 kA; specify >=50 kA withstand.",
         "week": 4},
        {"id": "RFI-014", "system": "UPS", "status": "resolved",
         "question": "Confirm UPS battery autonomy target for Tier IV during "
                     "concurrent maintenance.",
         "resolution": "Owner confirmed 10 min minimum autonomy at full load; "
                       "vendor to resize battery string accordingly.",
         "week": 6},
        {"id": "RFI-015", "system": "CABLE", "status": "resolved",
         "question": "Are all data cabling areas classified as plenum spaces "
                     "requiring CMP-rated cable?",
         "resolution": "Yes — all IT white-space areas and cable distribution "
                       "areas are plenum-classified per NFPA 75.",
         "week": 7},
        {"id": "RFI-017", "system": "GEN", "status": "open",
         "question": "Clarify on-site fuel autonomy hours for Tier IV — is 12h "
                     "with a fuel delivery contract acceptable?",
         "resolution": None, "week": 8},
        {"id": "RFI-019", "system": "BMS", "status": "open",
         "question": "The BMS points list revision C is missing the leak-detection "
                     "interface. When will it be included?",
         "resolution": None, "week": 9},
        {"id": "RFI-021", "system": "COOL", "status": "open",
         "question": "Is N+1 acceptable for the chilled-water loop or is N+2 "
                     "required for fault tolerance?",
         "resolution": None, "week": 9},
        {"id": "RFI-024", "system": "FIRE", "status": "resolved",
         "question": "Confirm clean-agent suppression is required for all 8 IT "
                     "zones or only the high-density zones.",
         "resolution": "All 8 zones require clean-agent suppression per DB-10.2.",
         "week": 10},
    ]
    w(ROOT / "rfi" / "rfi_log.json", json.dumps(rfi_log, indent=2))

    w(ROOT / "extracted" / "requirements.json",
      json.dumps(requirements_struct, indent=2))
    w(ROOT / "extracted" / "submittals.json",
      json.dumps(submittals_struct, indent=2))
    w(ROOT / "ground_truth.json", json.dumps({
        "project": PROJECT,
        "seeded_deviations": ground_truth,
        "true_negative_systems": ["FIRE", "BUSWAY", "PDU", "STRUCT"],
    }, indent=2))

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
