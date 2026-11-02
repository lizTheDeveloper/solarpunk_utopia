# Civic Sensor Network and Reclaimed-Hardware Learning Spec
**Status:** Draft v0.1 — 2026-11-02
**Related:** [Agricultural Observability](AGRICULTURE_OBSERVABILITY.md)

## Objective
Make environmental observability a community skill, not an expensive proprietary service. Teach participants to build, calibrate, maintain and interpret small instruments made from repaired or salvaged parts; connect devices through an offline-first infrastructure compatible with Solarpunk Utopia. The network should be useful even if every sensor is removed.

## Reference architecture
**Instruments**: ESP32 nodes, appropriate calibrated soil moisture probes, DS18B20-class temperature probes, tipping bucket rain gauges, flow meters with calibration, water level sensors, solar/battery monitors and cameras focused on plants or wildlife.
**Edge**: Raspberry Pi or reused laptop gateways ingest readings, run local validation/queue, offer local UI and export data. A Pi is a gateway/node, not necessarily a battery-efficient field device.
**Network**: choose wired, Wi-Fi, ESP-NOW, or LoRa based on measured topology, climate, power and maintenance capacity. 'Mesh' requires explicit routing/relay design and reliability tests; star networks with forwarding gateways may be more reliable. Local-first MQTT or HTTP transport, with authenticated interfaces and store-and-forward.
**Application**: time-series measurements, calibration/provenance, alerts based on authentic thresholds, link sensor IDs to plots and in-world objects.
**Federation**: share aggregates by consent, not unrestricted raw camera feeds, exact sensitive locations, identities or infrastructure maps.

## Sensor type contracts
Each record includes event_id, community_id, device_id, sensor_id, observed_at, received_at, plot_id, metric, raw_value, raw_unit, interpreted_value, interpreted_unit, calibration_id, quality_flags, firmware_version, battery_state and provenance. A stale clock, invalid calibration or physically implausible reading produces a data-quality warning rather than a false numeric fact. Store raw readings for future recalibration.

## Calibration, research and provenance
- Soil moisture probes may yield relative signals; volumetric water content requires soil-specific calibration.
- Soil pH readings require documented extraction and instrument method; field strips, meters and laboratory tests are different quality classes.
- Rainfall reading requires gauge dimensions, siting, period and cleaning notes; distinguish forecast from observed rainfall.
- Camera classification is a hypothesis; record confidence, verify sightings and maintain false-positive statistics.
- Compare water use, rainfall and growth with care; do not present observational correlation as causal improvement.
- Include accessible uncertainty badges: measured, estimated, self-reported, sensor-derived, simulation and unknown.

## Hardware safety and privacy
Power workshops default to safe low-voltage circuits with battery protection, waterproofing, strain relief and safe lithium storage. Hazardous mains electrical, permanent solar installations or battery banks require qualified professionals and appropriate permits. No camera may aim at living quarters or identifying human traffic without properly informed consent; no face recognition or covert monitoring. Wildlife conservation rules and local law govern placement. A sensor system must not make automated decisions about critical water or electrical infrastructure without safeguards.

## Workshop learning tree
1. **Measurement Matters**: manual harvest logs, spreadsheet fundamentals, units, errors, confidence and uncertainty.
2. **Map the Commons**: label actual beds/compost bins, QR codes, plot IDs and community data governance.
3. **From Scrap to Sensor**: test/repair components, safe soldering, firmware flashing, serial plots, moisture probes and calibration.
4. **ESP32 Field Station**: deep sleep, radio telemetry, enclosures, field diagnostics and secure identity.
5. **Build a Raspberry Pi Gateway**: local ingestion and offline dashboard; test connectivity loss and sync.
6. **Rain and Water Lab**: gauges, tank levels, weatherproofing, flow estimates and maintenance.
7. **Compost Observatory**: temperature probes, manual entry and data literacy.
8. **Wildlife Camera Guild**: responsible camera placement, privacy masking, candidate detections and human review.
9. **Mesh Mythbusting**: evaluate Wi-Fi, ESP-NOW, LoRa and routed multihop; range maps, duty cycle, relay failures and costs.
10. **Citizen Science**: protocols, controls, replication, metadata, visualization and open reports.
11. **Repair & Stewardship**: battery replacements, calibration checks, e-waste disposal and device lending.
12. **Teach the Teachers**: publish build cards, mentor peers and federate proven lessons.

## Quest mechanics
Each lab can create a party with roles: maker, tester, documentarian, gardener and mentor. 'Built device' badge records learning evidence; 'calibrated probe' badge requires real comparison; 'environmental engineer' or regulated professional titles are never awarded automatically. System projects can earn collective celebrations with no XP tied to labor hours.

## Phased validation
A) 1 bed + manual harvest log; B) 1 moisture sensor + calibration + local Pi gateway + visible staleness; C) multi-plot readings + data quality; D) solar powered field nodes + reliable connectivity survey; E) optional biodiversity camera; F) cross-community environmental commons. Measure packet delivery, uptime, maintenance burden, field accuracy, onboarding effort and participant understanding, not only number of devices.

## Threat model
Compromised sensor, forged readings, clock drift, duplicate events, battery failure, malicious firmware, leaked coordinates, camera privacy breach, router abuse, wireless interference, vandalism, physical safety. Mitigations: authenticated devices, least privilege, signed update releases where feasible, replay IDs, edit/revoke controls, backup, retention and local override.
