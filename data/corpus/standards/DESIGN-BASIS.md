# Project Meghdoot — Design Basis Document (owner requirements)

Owner's Project Requirements (OPR) that set capacities, set-points, and topology targets for a 40 MW Uptime Tier IV hyperscale data centre facility located in Navi Mumbai, India.

## DB-4: Electrical — UPS & Battery
- DB-4.1: UPS topology: 2N (dual bus)
- DB-4.2: UPS module rating: 1200 kW per module
- DB-4.3: Battery autonomy: minimum 10 minutes at full rated load
- DB-4.4: Battery technology: VRLA AGM or Li-ion (vendor to propose)
- DB-4.5: UPS efficiency: >= 96% at rated load

## DB-5: Electrical — Generators & Fuel
- DB-5.1: Generator redundancy: N+1
- DB-5.2: Generator rating: 2500 kVA per unit (prime-rated)
- DB-5.3: Start time: <= 10 seconds to rated speed
- DB-5.4: On-site fuel autonomy: minimum 24 hours at full rated load
- DB-5.5: Fuel storage: bulk tank with secondary containment

## DB-6: Mechanical — Cooling
- DB-6.1: Cooling redundancy: N+2 (chiller plant)
- DB-6.2: Chiller capacity: 1500 TR per unit
- DB-6.3: Supply air temperature: 24 C (per ASHRAE TC 9.9 recommended)
- DB-6.4: Delta-T across cooling coils: 10 C
- DB-6.5: Free cooling economiser to be evaluated

## DB-7: Electrical — Switchgear
- DB-7.1: MV switchgear topology: 2N
- DB-7.2: Short-circuit withstand: >= 50 kA for 1 second (per project fault study)
- DB-7.3: Arc-flash protection: Type 2B classification
- DB-7.4: Metering: revenue-grade at utility PCC

## DB-8: Cabling
- DB-8.1: Data cabling: Cat6A minimum for all horizontal runs
- DB-8.2: Fibre backbone: OS2 single-mode inter-building, OM4 multimode intra-building
- DB-8.3: Maximum cable tray fill: 50%
- DB-8.4: Fire rating: CMP (plenum-rated) in all IT and plenum spaces
- DB-8.5: Maximum bundle size: 48 cables per bundle

## DB-9: BMS / EPMS / Monitoring
- DB-9.1: Monitoring redundancy: dual (primary + standby)
- DB-9.2: DCIM integration: Schneider EcoStruxure or equivalent
- DB-9.3: Protocol: BACnet/IP for BMS, Modbus TCP for EPMS
- DB-9.4: Data retention: minimum 2 years trending data
- DB-9.5: Critical alarm set: complete, including power failure, generator status, UPS alarms, temperature exceedance, humidity exceedance, leak detection, fire panel interface, security breach

## DB-10: Fire Protection
- DB-10.1: Suppression zones: 8 (one per data hall)
- DB-10.2: Agent type: clean-agent (FM-200 or Novec 1230)
- DB-10.3: Detection: VESDA in all IT spaces

## DB-11: Busway
- DB-11.1: Busway rating: 4000 A
- DB-11.2: Redundancy: 2N
- DB-11.3: IP rating: IP54

## DB-12: Power Distribution Units
- DB-12.1: Metering: per-outlet
- DB-12.2: Redundancy: A+B feeds
- DB-12.3: Rated current: 63 A per PDU

## DB-13: Structural — Raised Floor
- DB-13.1: Concentrated load rating: 12 kPa minimum
- DB-13.2: Seismic design: Zone IV per IS 1893
- DB-13.3: Finished floor height: 900 mm minimum (for under-floor air distribution, power cabling, and fire suppression piping)
