"""
Pramaan — Synthetic EPC corpus generator for "Project Meghdoot"
A 40 MW, Uptime Tier IV hyperscale data centre (fictional, India).

Generates a realistic, LABELLED corpus so the deviation-detection pipeline can
be evaluated with real precision/recall. Deterministic: no LLM required to
produce the corpus, so it is reproducible and auditable.

v3: Standards upgraded with real data from ASHRAE TC 9.9, Uptime Institute,
TIA-942-C, BICSI-002-2024, NFPA 75/262, and IS 1893:2016. Added ASHRAE TC 9.9
as seventh standard. Academic references: ASCE JCEM 2024 GenAI compliance
checking, Graph-RAG compliance (arXiv 2412.08593), I-SNACC NLP framework.
Added adversarial deviation (STRUCT raised floor height) to prove system
generalises beyond pre-programmed rules.
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
            "height_mm": 600,
        },
        "prose": {
            "spec_intro": (
                "The raised-floor system in all data halls shall be designed for "
                "the concentrated and distributed loads of fully populated server "
                "racks, including future high-density deployments up to 30 kW/rack. "
                "Floor height shall provide adequate clearance for under-floor "
                "chilled-air distribution, power cabling, and fire suppression "
                "piping, with seismic bracing per IS 1893 for Zone IV."
            ),
            "submittal_intro": (
                "Vendor: Kingspan Alpha III HPL system, steel pedestal + stringer.\n"
                "Panels: 600 × 600 mm, calcium sulphate core, HPL surface.\n"
                "The vendor has proposed a 600 mm finished floor height based on "
                "their standard pedestal range. The vendor notes that 600 mm is the "
                "minimum recommended height per BICSI-002 and is adequate for "
                "conventional under-floor air distribution. The project specification "
                "of 900 mm has been noted but the vendor recommends the lower height "
                "to reduce cost and pedestal count."
            ),
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
    ("FLOOR", "height_mm"): {
        "cx_test": "ITP-01", "cx_level": 1,
        "cx_name": "Equipment receipt inspection",
        "week_fail": 16, "severity": "Major",
        "reason": "Raised floor height 600 mm vs required 900 mm; insufficient "
                  "clearance for under-floor chilled-air distribution, power "
                  "cabling, and fire suppression piping per design basis DB-13.3.",
    },
}

STANDARDS = {
    "UPTIME-TIER4": (
        "# Uptime Tier IV — Fault Tolerance (paraphrased summary)\n\n"
        "The Uptime Institute Tier Standard defines four levels of data centre "
        "infrastructure topology. Tier IV is the highest classification, requiring "
        "both concurrent maintainability (any component can be removed for planned "
        "maintenance without impacting IT load) and fault tolerance (the facility "
        "must withstand any single worst-case infrastructure failure without "
        "impacting IT load).\n\n"
        "## Availability target\n"
        "- Site-level availability: 99.995%\n"
        "- Maximum annual downtime: 26.3 minutes per year\n"
        "- Compared to Tier III (99.982%, 1.6 h/yr) and Tier II (99.749%, 22 h/yr)\n\n"
        "## Topology requirements\n\n"
        "### Power distribution\n"
        "- Minimum 2N distribution from utility entrance to the rack PDU\n"
        "- Two independent utility feeds or on-site generation sufficient "
        "to meet 2N requirement\n"
        "- Each path must be capable of carrying the full critical load independently\n"
        "- Automatic transfer between paths with zero IT load impact\n\n"
        "### Stored energy\n"
        "- Battery autonomy: minimum 10 minutes at full rated load\n"
        "- Must account for generator start sequence, transfer time, and "
        "load acceptance under worst-case conditions\n"
        "- End-of-life battery capacity degradation must be included in sizing\n"
        "- On-site fuel: minimum 24 hours at rated load without refuelling\n"
        "- Fuel storage must account for seasonal density variations\n\n"
        "### Cooling\n"
        "- N+2 redundancy: N units serving load, one available for planned "
        "maintenance, one available to absorb an unrelated fault\n"
        "- N+1 is insufficient for Tier IV because it only covers a single "
        "contingency (maintenance OR fault, not both simultaneously)\n"
        "- Continuous cooling must be maintained under any single failure\n"
        "- Chilled water piping in dual-path configuration\n\n"
        "### Generators\n"
        "- N+1 minimum redundancy\n"
        "- Start-up time: maximum 10 seconds to rated speed\n"
        "- Load acceptance within 10 seconds of start command\n"
        "- On-site fuel for 24 hours at full rated load\n\n"
        "## Key numerical thresholds\n\n"
        "| Parameter                  | Tier III   | Tier IV          |\n"
        "|----------------------------|------------|------------------|\n"
        "| Availability               | 99.982%    | 99.995%          |\n"
        "| Power distribution         | N+1 or 2N  | 2N               |\n"
        "| Cooling redundancy         | N+1        | N+2              |\n"
        "| Battery autonomy (min)     | 10 min     | 10 min           |\n"
        "| On-site fuel (min)         | 24 h       | 24 h             |\n"
        "| Concurrent maintainability | Yes        | Yes              |\n"
        "| Fault tolerance            | No         | Yes              |\n"
        "| Single point of failure    | Possible   | None permitted   |\n\n"
        "## Certification process\n"
        "- Tier Certification of Design Documents (TCDD) — paper review\n"
        "- Tier Certification of Constructed Facility (TCCF) — field verification\n"
        "- Both required; TCDD alone does not certify Tier IV\n"
    ),
    "TIA-942": (
        "# TIA-942-C — Telecommunications Infrastructure Standard "
        "for Data Centres (paraphrased summary)\n\n"
        "ANSI/TIA-942-C (revised 2024) defines telecommunications infrastructure "
        "requirements for data centres using a four-tier Rated system (Rated 1 "
        "through Rated 4). The standard covers cabling, pathways, spaces, and "
        "environmental requirements.\n\n"
        "## Rating levels\n\n"
        "| Feature                    | Rated 1    | Rated 2    | Rated 3    | Rated 4    |\n"
        "|----------------------------|------------|------------|------------|------------|\n"
        "| Redundancy                 | None       | N+1 comp.  | N+1 path   | 2N path    |\n"
        "| Concurrent maintainable    | No         | No         | Yes        | Yes        |\n"
        "| Fault tolerant             | No         | No         | No         | Yes        |\n"
        "| Dual utility feeds         | No         | No         | Optional   | Required   |\n\n"
        "## Cabling requirements\n"
        "- Horizontal data cabling: minimum Category 6A (Cat6A) for all new "
        "installations\n"
        "- Fibre backbone: OS2 single-mode for inter-building; OM3/OM4 "
        "multimode for intra-building\n"
        "- Structured cabling topology: MDA (Main Distribution Area), "
        "HDA (Horizontal Distribution Area), EDA (Equipment Distribution "
        "Area), ZDA (Zone Distribution Area)\n"
        "- Maximum 90 m horizontal copper channel length\n"
        "- Minimum 25 mm bend radius for 4-pair UTP cable\n\n"
        "## Pathway and spaces\n"
        "- Cable tray fill ratio: maximum 50% for future growth\n"
        "- Redundant pathway routing required for Rated 3 and Rated 4\n"
        "- Separation of power and data pathways per applicable electrical code\n"
        "- Fire-rated pathway penetrations where crossing fire barriers\n\n"
        "## Environmental\n"
        "- References ASHRAE TC 9.9 for environmental conditions\n"
        "- Hot-aisle/cold-aisle containment recommended for Rated 3 and above\n"
    ),
    "BICSI-002": (
        "# BICSI-002-2024 — Data Centre Design and Implementation "
        "Best Practices (paraphrased summary)\n\n"
        "BICSI-002 (8th edition, 2024, 575 pages) provides comprehensive "
        "design guidance for data centres. It coordinates requirements across "
        "power, cooling, cabling, monitoring, and physical security. A core "
        "principle: redundancy of one subsystem must not be undermined by a "
        "weaker adjacent subsystem.\n\n"
        "## Electrical design\n"
        "- UPS efficiency target: >= 96% at rated load\n"
        "- Generator sizing: minimum 110% of connected critical load\n"
        "- Power Usage Effectiveness (PUE) target: <= 1.4 for new builds\n"
        "- Harmonic distortion: THD-V <= 5% at PCC\n"
        "- Arc-flash hazard analysis required for all switchgear\n\n"
        "## Cabling infrastructure\n"
        "- Maximum 48 cables per bundle to maintain thermal management "
        "and serviceability\n"
        "- Cable tray pathway fill: maximum 50% of usable area\n"
        "- Coordination between electrical and mechanical routing to "
        "prevent electromagnetic interference\n"
        "- Minimum cable bend radius: 4x cable OD for UTP, 10x for fibre\n"
        "- Labelling: every cable at both ends, every patch panel port\n\n"
        "## Raised floor\n"
        "- Minimum 600 mm (24 in) finished floor height for under-floor "
        "air distribution\n"
        "- Higher heights (900 mm+) recommended for high-density "
        "deployments with extensive under-floor cabling\n"
        "- Concentrated load rating per CISCA/ISDSI standards\n"
        "- Seismic bracing where required by local code\n\n"
        "## Cooling\n"
        "- CRAH/CRAC units sized with N+1 or N+2 per availability class\n"
        "- Supply air temperature per ASHRAE TC 9.9 recommended envelope\n"
        "- Delta-T across cooling coils: 10-14 C typical\n"
        "- Free cooling economiser hours evaluated for climate zone\n\n"
        "## Commissioning\n"
        "- Five commissioning levels: L1 (ITP/receipt inspection), "
        "L2 (installation verification), L3 (functional/FAT), "
        "L4 (integrated systems test/IST), L5 (owner acceptance)\n"
        "- 72-hour sustained operations test required before handover\n"
        "- Commissioning authority independent of design and construction teams\n"
    ),
    "NFPA-75": (
        "# NFPA 75 — Standard for the Fire Protection of Information "
        "Technology Equipment (paraphrased summary)\n\n"
        "NFPA 75 (2025 edition) establishes fire protection requirements "
        "for IT equipment areas. Materials in IT and plenum spaces must meet "
        "fire performance requirements for the room classification.\n\n"
        "## Cable fire ratings\n"
        "Cable fire-rating must satisfy the plenum or room classification. "
        "NFPA 75 references the cable hierarchy defined by the NEC and "
        "tested per UL/NFPA standards:\n\n"
        "| Rating | Full Name                        | Test Standard     | Use               |\n"
        "|--------|----------------------------------|-------------------|-------------------|\n"
        "| CMP    | Communications Multipurpose Plenum | UL 910 / NFPA 262 | Plenum spaces    |\n"
        "| CMR    | Communications Multipurpose Riser  | UL 1666           | Riser / vertical |\n"
        "| CM     | Communications Multipurpose        | UL 1581           | General purpose  |\n"
        "| CMX    | Communications Multipurpose Ltd    | UL 1581           | Residential      |\n\n"
        "### Key rule: CMP is mandatory in plenum-classified spaces.\n"
        "CMR cable is NOT acceptable as a substitute for CMP in plenums. "
        "The hierarchy is strictly CMP > CMR > CM > CMX — a higher-rated "
        "cable may substitute for a lower rating, but never the reverse.\n\n"
        "### UL 910 / NFPA 262 plenum test criteria\n"
        "- Peak optical smoke density: <= 0.50\n"
        "- Average optical smoke density: <= 0.15\n"
        "- Maximum flame spread distance: <= 1.52 m (5 ft)\n\n"
        "## Fire detection\n"
        "- VESDA (Very Early Smoke Detection Apparatus) recommended "
        "for high-value IT rooms\n"
        "- Aspirating smoke detection provides earliest warning tier "
        "(Alert → Action → Fire levels)\n"
        "- Spot-type smoke detectors as secondary detection layer\n\n"
        "## Fire suppression\n"
        "- Clean-agent suppression (e.g., FM-200, Novec 1230, or "
        "inert gas) required for rooms with active IT equipment\n"
        "- Design concentration per agent manufacturer's listing\n"
        "- 10-minute minimum hold time for agent concentration\n"
        "- Water-based systems (pre-action) acceptable in support spaces\n\n"
        "## Room construction\n"
        "- IT equipment rooms: 1-hour fire-rated construction minimum\n"
        "- Raised-floor plenum classified as plenum space per mechanical code\n"
        "- All cable penetrations fire-stopped to match wall rating\n"
    ),
    "DESIGN-BASIS": (
        "# Project Meghdoot — Design Basis Document (owner requirements)\n\n"
        "Owner's Project Requirements (OPR) that set capacities, set-points, "
        "and topology targets for a 40 MW Uptime Tier IV hyperscale data "
        "centre facility located in Navi Mumbai, India.\n\n"
        "## DB-4: Electrical — UPS & Battery\n"
        "- DB-4.1: UPS topology: 2N (dual bus)\n"
        "- DB-4.2: UPS module rating: 1200 kW per module\n"
        "- DB-4.3: Battery autonomy: minimum 10 minutes at full rated load\n"
        "- DB-4.4: Battery technology: VRLA AGM or Li-ion (vendor to propose)\n"
        "- DB-4.5: UPS efficiency: >= 96% at rated load\n\n"
        "## DB-5: Electrical — Generators & Fuel\n"
        "- DB-5.1: Generator redundancy: N+1\n"
        "- DB-5.2: Generator rating: 2500 kVA per unit (prime-rated)\n"
        "- DB-5.3: Start time: <= 10 seconds to rated speed\n"
        "- DB-5.4: On-site fuel autonomy: minimum 24 hours at full rated load\n"
        "- DB-5.5: Fuel storage: bulk tank with secondary containment\n\n"
        "## DB-6: Mechanical — Cooling\n"
        "- DB-6.1: Cooling redundancy: N+2 (chiller plant)\n"
        "- DB-6.2: Chiller capacity: 1500 TR per unit\n"
        "- DB-6.3: Supply air temperature: 24 C (per ASHRAE TC 9.9 recommended)\n"
        "- DB-6.4: Delta-T across cooling coils: 10 C\n"
        "- DB-6.5: Free cooling economiser to be evaluated\n\n"
        "## DB-7: Electrical — Switchgear\n"
        "- DB-7.1: MV switchgear topology: 2N\n"
        "- DB-7.2: Short-circuit withstand: >= 50 kA for 1 second "
        "(per project fault study)\n"
        "- DB-7.3: Arc-flash protection: Type 2B classification\n"
        "- DB-7.4: Metering: revenue-grade at utility PCC\n\n"
        "## DB-8: Cabling\n"
        "- DB-8.1: Data cabling: Cat6A minimum for all horizontal runs\n"
        "- DB-8.2: Fibre backbone: OS2 single-mode inter-building, "
        "OM4 multimode intra-building\n"
        "- DB-8.3: Maximum cable tray fill: 50%\n"
        "- DB-8.4: Fire rating: CMP (plenum-rated) in all IT and plenum spaces\n"
        "- DB-8.5: Maximum bundle size: 48 cables per bundle\n\n"
        "## DB-9: BMS / EPMS / Monitoring\n"
        "- DB-9.1: Monitoring redundancy: dual (primary + standby)\n"
        "- DB-9.2: DCIM integration: Schneider EcoStruxure or equivalent\n"
        "- DB-9.3: Protocol: BACnet/IP for BMS, Modbus TCP for EPMS\n"
        "- DB-9.4: Data retention: minimum 2 years trending data\n"
        "- DB-9.5: Critical alarm set: complete, including power failure, "
        "generator status, UPS alarms, temperature exceedance, humidity "
        "exceedance, leak detection, fire panel interface, security breach\n\n"
        "## DB-10: Fire Protection\n"
        "- DB-10.1: Suppression zones: 8 (one per data hall)\n"
        "- DB-10.2: Agent type: clean-agent (FM-200 or Novec 1230)\n"
        "- DB-10.3: Detection: VESDA in all IT spaces\n\n"
        "## DB-11: Busway\n"
        "- DB-11.1: Busway rating: 4000 A\n"
        "- DB-11.2: Redundancy: 2N\n"
        "- DB-11.3: IP rating: IP54\n\n"
        "## DB-12: Power Distribution Units\n"
        "- DB-12.1: Metering: per-outlet\n"
        "- DB-12.2: Redundancy: A+B feeds\n"
        "- DB-12.3: Rated current: 63 A per PDU\n\n"
        "## DB-13: Structural — Raised Floor\n"
        "- DB-13.1: Concentrated load rating: 12 kPa minimum\n"
        "- DB-13.2: Seismic design: Zone IV per IS 1893\n"
        "- DB-13.3: Finished floor height: 900 mm minimum (for under-floor "
        "air distribution, power cabling, and fire suppression piping)\n"
    ),
    "IS-1893": (
        "# IS 1893 (Part 1): 2016 — Criteria for Earthquake Resistant Design "
        "of Structures (paraphrased summary)\n\n"
        "IS 1893 is the Bureau of Indian Standards code for seismic design. "
        "It classifies India into seismic zones II through V (with Zone VI "
        "proposed in the 2025 draft amendment for the Himalayan belt).\n\n"
        "## Seismic zone classification\n\n"
        "| Zone   | Zone Factor (Z) | Seismic Intensity     | Examples                |\n"
        "|--------|----------------|-----------------------|-------------------------|\n"
        "| II     | 0.10           | Low                   | Most of peninsular India|\n"
        "| III    | 0.16           | Moderate               | Mumbai, Kolkata         |\n"
        "| IV     | 0.24           | Severe                 | Delhi, Navi Mumbai*     |\n"
        "| V      | 0.36           | Very severe            | NE India, Kashmir       |\n\n"
        "*Navi Mumbai spans Zone III/IV boundary; critical infrastructure "
        "facilities shall assume Zone IV per IS 1893 clause 6.4.2.\n\n"
        "## Design parameters for data centres\n"
        "- Importance factor (I): 1.5 for critical infrastructure "
        "(post-disaster function, per Table 8)\n"
        "- Response reduction factor (R): per structural system type\n"
        "- Soil classification: Type I (rock/hard), Type II (medium), "
        "Type III (soft)\n"
        "- Design horizontal seismic coefficient: A_h = (Z/2) × (I/R) × (Sa/g)\n"
        "- Seismic base shear: V_B = A_h × W (total seismic weight)\n\n"
        "## Equipment and non-structural elements\n"
        "- Raised-floor pedestals: anchorage designed for applicable zone "
        "with importance factor I=1.5\n"
        "- Equipment anchorage: server racks, UPS modules, switchgear, "
        "battery racks must be bolted/braced\n"
        "- Suspended ceiling and cable tray bracing per IS 1893 Part 4\n"
        "- Seismic isolation/damping for sensitive IT equipment if "
        "floor acceleration exceeds equipment rating\n\n"
        "## Testing and qualification\n"
        "- Shake-table testing or equivalent analysis for raised-floor "
        "systems in Zone IV and above\n"
        "- Vendor to provide seismic qualification certificate for the "
        "applicable zone and importance factor\n"
    ),
    "ASHRAE-TC9.9": (
        "# ASHRAE TC 9.9 — Thermal Guidelines for Data Processing "
        "Environments (paraphrased summary)\n\n"
        "ASHRAE Technical Committee 9.9 publishes thermal guidelines "
        "that define allowable and recommended environmental conditions "
        "at the server inlet, classified by equipment class.\n\n"
        "## Equipment classes and envelopes\n\n"
        "### Class A1 (enterprise servers, storage)\n"
        "- Allowable dry-bulb: 15 C to 32 C\n"
        "- Allowable dew point: -12 C to 17 C\n"
        "- Allowable relative humidity: 8% to 80%\n"
        "- Recommended dry-bulb: 18 C to 27 C\n"
        "- Recommended dew point: -9 C to 15 C\n"
        "- Recommended relative humidity: <= 60%\n\n"
        "### Class A2 (volume servers, rack-mount)\n"
        "- Allowable dry-bulb: 10 C to 35 C\n"
        "- Allowable dew point: -12 C to 21 C\n"
        "- Allowable relative humidity: 8% to 80%\n\n"
        "### Class A3 (ruggedised equipment)\n"
        "- Allowable dry-bulb: 5 C to 40 C\n"
        "- Allowable dew point: -12 C to 24 C\n"
        "- Allowable relative humidity: 8% to 85%\n\n"
        "### Class A4 (hardened equipment)\n"
        "- Allowable dry-bulb: 5 C to 45 C\n"
        "- Allowable dew point: -12 C to 24 C\n"
        "- Allowable relative humidity: 8% to 90%\n\n"
        "## Recommended envelope (design target)\n"
        "For most data centre designs, the Class A1 recommended "
        "envelope is the design target:\n"
        "- Supply air temperature: 18-27 C (target 24 C +/- 2 C)\n"
        "- Dew point: -9 C to 15 C\n"
        "- Relative humidity: <= 60%\n\n"
        "## Rate of change\n"
        "- Maximum allowable rate of temperature change: 5 C per hour "
        "during planned or unplanned transitions (e.g., cooling failover)\n"
        "- Rapid temperature changes increase risk of condensation "
        "and thermal shock to components\n\n"
        "## Measurement guidance\n"
        "- Temperature and humidity shall be measured at the server "
        "inlet (front of rack), not at room average or return air\n"
        "- Sensor placement: top, middle, and bottom of each rack "
        "or per hot-aisle/cold-aisle containment monitoring plan\n"
        "- Altitude derating: maximum allowable temperature decreases "
        "by 1 C per 300 m above 900 m elevation\n"
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
        "true_negative_systems": ["FIRE", "BUSWAY", "PDU"],
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
