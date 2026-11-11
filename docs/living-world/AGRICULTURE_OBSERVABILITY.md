# Living World: Community Agriculture & Environmental Observability
**Status:** Draft v0.1 — November 2, 2026
**Parent:** [Living World Product Spec](SPEC.md)
**Pilot:** Wild Seeds Ranch; generalizable to small-scale farms, gardens, cooperative homesteads and intentional communities.

## 1. Aim and real-site evidence
Make land stewardship measurable and fun without requiring farming expertise or proprietary equipment. People should know what grew, what was lost and why, how soil and water change over time, and what work matters today. Every record can become a map interaction, a learning experience and—when needed—a verified quest.

Wild Seeds publicly lists communal gardens and a small vineyard, permaculture activation, rainwater collection systems, plant propagation and farmers-market coordination among facilities and opportunities:
- https://www.wildseedsranch.com/community-amenities
- https://www.wildseedsranch.com/opportunities
- https://www.wildseedsranch.com/earthlabs
Its current bed inventory, crop yields, sensor hardware and irrigation layout **are not confirmed** by these pages. During residency discovery, do a consent-aware field inventory before modeling real facilities.

## 2. Product constraints
- **Manual-first:** every measurement supports a 15-second phone entry; hardware is optional.
- **Count what is known:** missing is *unknown*, not zero; estimates retain method and uncertainty.
- **Friendly units:** pounds/ounces, grams/kilograms, gallons/liters, count of heads/bunches, bed area; normalize into canonical units with retained original values.
- **Low-friction harvest logging:** tap crop, bed, amount, disposition; support tare, reused containers, batch entry and optional photo.
- **Offline-first:** record locally and synchronize idempotently through existing DTN mechanisms where appropriate; work without connectivity.
- **Provenance:** measurement timestamp, observer/device, location, unit, method, confidence and verification status.
- **No compulsory quantification:** participants may decline individual productivity tracking; aggregate outcomes, not worker surveillance.

## 3. Modules and questions
### A. Land inventory, plots and crop cycles
Named garden beds, orchard trees, vineyard rows, greenhouse benches, compost bins, water catchments, solar rigs and sensors map to spatial features with optional privacy-safe approximation. Crop cycles track species, variety, seed origin, planting/transplant date, expected harvest window, actual harvest, companion plants, rotation and interventions. Each site can build a map progressively via in-world editing.

### B. Harvest + disposition ledger
Harvest event: plot, crop cycle, measured or estimated quantity, unit, container tare, harvest date, measured_by (optional), notes, photos, batch ID, destination: community kitchen, gift exchange, sale, preservation, seed saving, compost or unallocated. Reassigning a batch between destinations must not double count harvested mass.
Views: 'Last season we harvested X lb of kale'; by crop, plot, month, grower-independent community total, destination and year. No harvest entries != no harvest.

### C. Crop loss and pest attribution
Loss event: crop/plot, stage (preharvest/postharvest), reason (bird, mammal, insect, disease, heat, frost, drought, irrigation failure, storage spoilage, other, unknown), quantity, unit, method (weighed/estimated), evidence, confidence and mitigation. Preharvest yield loss is often an estimate, so display uncertainty; do not silently claim loss percentage based on a fictional expected yield. For postharvest loss, reference harvested inventory and avoid subtracting the same quantity twice.
Support damage observations even when loss amount is unknown. Use wildlife-friendly integrated pest management and positive biodiversity observations.

### D. Soil sampling and measurements
Soil sample entity: plot/point, collection depth, date, sampler, conditions, lab or field method, lab report attachment, units, calibration metadata. Measurements: pH, soil temperature, electrical conductivity, organic matter %, texture, nitrate, phosphorus, potassium and other test-specific parameters where available. Field pH strip readings and accredited lab results must be visibly distinguished. Sampling and retesting intervals are locally configurable; do not imply a universal ideal pH.

### E. Soil moisture, rainfall and water
Observation entity for raw sensor values and calibrated moisture estimates; record probe depth, sensor model, soil-specific calibration, placement, battery voltage, last heartbeat and firmware version. Rainfall data from manual rain gauge or station, in mm/inches, including catchment area and reading period. Water tanks track capacity, measured level, collection, leak/overflow events; irrigation log tracks plot, estimated or metered volume and duration. Do not infer water volume from an uncalibrated moisture percent.
Views: rainfall vs soil moisture, cumulative collection vs use, dry-bed alerts tied to actual thresholds and confirmed crop needs.

### F. Compost management
Pile/batch: source materials, green/brown additions, estimated mass/volume, date, location, turning/aeration, water addition, temperature profile, moisture observation, odors, maturity status, destination plot, applied amount. Manual thermometer and squeeze-test entry are first-class options. Distinguish household gardening use from food-safety and regulated compost processes; do not certify manure compost as safe without verified treatment parameters.
Guide: https://www.umass.edu/agriculture-food-environment/resources/food-safety/for-farmers/general-food-safety-information/soil-amendments

### G. Ecology and cameras
Wildlife sightings, pollinator counts, insect traps, visible crop damage and camera observation sessions. Photos or short clips can be annotated with species hypothesis and reviewer confidence. Keep biodiversity sightings separate from crop-loss attribution; bird presence does not prove damage. Cameras default to crop-facing privacy zones, no facial identification, short retention, local processing and explicit physical signage. No covert monitoring of volunteers or residents.

### H. Propagation, seeds and inputs
Seed lots, viability dates, germination observations, cuttings, nursery trays, transplant survival, seed sharing and compost/soil amendments. Track inputs by source and plot/date, enabling season-over-season comparisons.

### I. Maintenance and stewardship
Sensor service history, calibration dates, irrigation checks, solar power for sensor nodes, repairs, spare parts and who can teach the repair. Maintenance task states create optional quests with safety prerequisites.

## 4. Living RPG interface
- Interact with a kale bed -> growth history, harvest total, recent observations, soil data and actionable care quests.
- Interact with compost sprite -> material recipe, thermometer history, 'turn pile' quest if genuinely due.
- Interact with rain barrel -> live/last-known level, rainfall history, maintenance needs.
- Interact with wildlife field guide -> sighting collections and seasonally changing species; not random loot.
- Observatory pavilion -> season recap, plot comparisons, real measurements vs missing-data indicators.
- Farm guild board -> tasks and sensor-build workshops; achievement records reflect verified skills and collaboration.
- Uninstrumented bed is still explorable, decorative and maintainable.

## 5. Counts and accounting rules
Canonical **harvest total** = sum of non-voided harvest events converted to mass, filtered by crop and period; report count-only harvests separately unless crop-specific weighed conversion is recorded and clearly marked estimated.
Canonical **postharvest loss** = sum of non-voided loss events linked to an identified harvested batch; prevent loss amount from exceeding available batch unless reconciled.
**Preharvest damage/loss** is reported separately and should NOT be deducted from measured harvest (it never entered harvested stock).
**Pest share of observed postharvest loss** = pest-attributed loss / total measured postharvest loss, with sample coverage. **Share of potential crop lost** is not computable without a defensible baseline yield estimate; clearly distinguish.
Export all source records and calculations (CSV/JSON), including units and revisions.

## 6. DIY learning and device pipeline
Begin with a manual entry + labeled garden-map workshop, then incremental electronics:
1. Weigh and record one harvest using a kitchen scale; graph its destination.
2. Assemble a moisture-reading ESP32 station from safe salvaged parts and a suitable capacitive sensor; compare dry/wet soil and calibrate for site conditions.
3. Add waterproof enclosure, low-voltage power, battery monitoring, timestamped payload and store-forward buffering.
4. Turn a reclaimed Raspberry Pi into a local gateway (MQTT/HTTP ingestion, Wi-Fi hotspot as appropriate); demonstrate internet-offline logging.
5. Extend with ESP-NOW / Wi-Fi / LoRa as site survey permits. **ESP32 wireless nodes and Raspberry Pi bridges are not automatically a true routed mesh**: document topology, range, failure modes, data delivery and energy budget.
6. Add rain gauge tipping-bucket counts, tank ultrasonic/pressure measurement, temperature probe or compost probe with field calibration and maintenance history.
7. Add crop-facing camera with local classification, opt-in biodiversity tagging, false-positive review and privacy masking.
8. Publish a reproducible build card: BOM with salvaged alternatives, wiring diagram, power safety, firmware, calibration, device ID, last service and troubleshooting quest.
Only appropriate low-voltage learning setups; electrical mains and solar installations require qualified supervision and code-compliant practices.

Device message envelope: event_id, community_id, plot_id, device_id, sensor_id, observed_at, received_at, metric, raw_value, raw_unit, derived_value, derived_unit, calibration_id, quality_flag, battery_state, firmware_version. Device ownership, key rotation, replay deduplication and rate-limiting are requirements. API and storage choices to be finalized after inspecting existing service contracts.

## 7. Data types (proposed, not implemented)
Plot, CropCycle, HarvestEvent, HarvestAllocation, LossEvent, Observation, SoilSample, Measurement, CompostBatch, CompostAction, WaterAsset, WaterEvent, WildlifeObservation, CameraSession, SeedLot, Device, Sensor, Calibration, DeviceReading, MaintenanceEvent, Evidence, Revision, QuestLink.
References should map to existing ValueFlows resource/process/economic-event types **only after** studying the actual schema. Never create duplicate real-world harvest stock from game XP awards.

## 8. Initial acceptance tests
- A contributor logs 3 lb kale in offline mode; on sync, the harvest is counted exactly once, with correct units and timestamp.
- Another records one pound of **postharvest** spoilage; harvest stays 3 lb and available stock becomes 2 lb.
- A 0.5 lb estimated **preharvest** bird-loss note appears with 'estimated'; actual measured harvest remains 3 lb.
- A year with zero records renders 'No harvest records' instead of '0 lb harvested'.
- A soil lab pH result and an inexpensive strip result display separate methods, units and confidence.
- A sensor with stale reading displays 'Last measured 3 days ago', never 'live'.
- Compost logs show temperature and turn history and do not automatically certify food-safety compliance.
- Wildlife camera runs without identifying people; images are withheld from unconsented public display.
- A participant can finish a device-building quest and earn a learning badge without their personal work hours being tracked.
- Two federation sites can exchange consented, aggregate crop statistics while keeping household-level data local.

## 9. Residency prototype
**Day-one viable path:** map 3 plots, label crops, capture manual harvests and damage observations, create a compost ledger, and visualize at least one simple seasonal chart.
**Electronics demonstrator:** one calibrated ESP32 moisture node + local Raspberry Pi gateway + last-known reading displayed at its actual in-world bed. Add more sensors only after reliable data collection and environmental protection.
**Workshop outputs:** each learner gets a portable skill endorsement with evidence and documentation; community keeps working hardware, repair instructions and control of its data.
Success = more reliably logged and understood information, not maximum sensors or maximum individual data extraction.

## 10. Unknowns for site survey
Actual plants/crop inventory; count and boundaries of growing beds; existing yield logs; soil test methods and locations; compost process; water rights and infrastructure; existing rain gauges, Wi-Fi and solar supply; camera privacy zones; data access requirements; device salvage sources; steward capacity; whether any production is sold (affects recordkeeping and food-safety obligations).

## 11. Research basis
- Wild Seeds amenities/opportunities/Earth Labs (links above).
- Mississippi State University Extension small farm records: https://cto.extension.msstate.edu/publications/small-farm-business-basics-planning-records-finances-and-pricing
- Cornell small farm recordkeeping: https://smallfarms.cornell.edu/wp-content/uploads/2016/09/4_Recordkeeping-1qo8q8u.pdf
- UMass soil amendment safety: https://www.umass.edu/agriculture-food-environment/resources/food-safety/for-farmers/general-food-safety-information/soil-amendments
- UF IFAS pest scouting and records: https://ask.ifas.ufl.edu/publication/CV274
