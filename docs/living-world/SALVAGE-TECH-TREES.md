# Salvage Technology Trees: Farm, Repair, Sensors, Education and Infrastructure
**Draft v0.1 — 2026-11-02**
An expansive catalog of realistic, serviceable inventions from reclaimed hardware, with clear buy-versus-salvage distinctions. Availability is site-specific; all prices below are rough planning allowances rather than current quotes.

## Salvage grading
**A: Strong candidate** reusable phone camera, enclosure, battery-*free* mains-powered gateway phone where safe, laptop, Raspberry Pi, USB cables in sound condition, chargers with verified certification, plastic bins, food-safe containers with known history, computer fans, heat sinks, wire, machine screws, connectors and display panels with documented interfaces.
**B: Test/repair first** power banks, used solar panels, solar charge controllers, pressure transducers, float switches, Hall sensors, optical interrupters, old reed switches, rain gauge buckets, temperature sensors, industrial probes, speakers, vibration motors, servos, switches and relays with ratings understood.
**C: Buy new / professionally validate** buried moisture probes, pH calibration buffers, known-standard reference thermometers, certified power supplies where mains are involved, lithium battery protection, waterproof cable glands, surge protection, fuses, electrical enclosures, safety-critical parts and lab soil tests.
**D: Avoid uncontrolled salvage** swollen lithium cells, damaged mains chargers, damaged capacitors/high-voltage components, unknown chemical containers for food/water, medical or industrial calibration equipment of unknown history, unsafe laser/UV sources, and unverified mains/battery systems.

## Potential sensor scavenging sources
| Donor device | Plausible harvest | Best use | Reality check |
|---|---|---|---|
| Old smartphone | camera, accelerometer, light sensor, mic, GPS, CPU, Wi-Fi, display | Field notebook, crop photos, fixed observation | Sensor APIs vary; phone barometer is not soil pressure |
| Computer case | 5/12V fan, switch, thermistors sometimes, cables, LEDs | Ventilation, demo circuits, repair stock | Fan is an actuator; RPM hall output depends on model |
| Printer/scanner | endstop switches, IR interrupters, motors, encoders, rails | Movement counters, plant imaging rigs | Mechanical complexity high; dangerous power parts |
| Washing machine/dishwasher | float/pressure/temperature sensors, flow-related sensors on some units | Water experiment after validation | Not food-safe by assumption; line-powered parts require safety screening |
| Refrigerator/freezer | thermistors, door reed switches, fans | Ambient/compost temperature demonstrations | Avoid refrigerant handling and mains compressor disassembly |
| Bike computer/cycling sensor | magnet + reed/Hall switches | Wind/rain bucket pulse counting | Calibration required |
| Home weather station | anemometer, rain gauge, humidity/temperature | Rainfall station | Useful only with identified pinout/calibration |
| Smart thermostat | temperature/humidity sensors | Indoor environmental observations | Proprietary firmware; harvesting sensor can be harder than replacement |
| Security camera/webcam | camera module, USB camera, night-vision parts | Wildlife station with consent | Do not reuse insecure proprietary cloud endpoints |
| Kitchen scale | load cell + analog frontend sometimes | Harvest weight station | Validate electronics and calibration weights |
| Old solar garden light | small PV cells, LED, light detector, enclosure | Demonstrations and low-power lessons | Cell output often inadequate for continuous cameras |
| Industrial/lab scrap | pH/EC probes, pressure sensors, load cells | Advanced sensing | Often costly calibration and interface issues |

## Farm technology ladders
### I. Harvest/data ladder
Handwritten tally -> QR-coded bed -> offline phone harvest log -> Bluetooth/USB kitchen-scale entry -> image assisted counts -> deduplicated harvest batches -> seasonal dashboard -> cross-community comparable crop experiments. **Always weigh mass; image counts don't imply pounds.**

### II. Soil ladder
Hand touch/visual observations -> sampled soil jar/texture exercise -> test-strip pH vs lab pH -> calibrated capacitive moisture probe -> several depths/plots -> rainfall-linked temporal history -> manual irrigation decisions -> water efficiency experiments -> qualified agronomic research. Don't infer nutrient content/pH from photos.

### III. Water ladder
Manual rain gauge -> recycled roof gutter demonstration (nonpotable, tested materials) -> tipping bucket sensor -> tank float/ultrasonic sensing -> irrigation flow logging -> leak diagnosis -> rainfall collection forecast with explicit uncertainty -> watershed cooperation. Distinguish water collection legality and potable safety.

### IV. Compost ladder
Manual recipe and thermometry -> photo log -> turning journal -> temperature probe -> moisture measurement -> multi-pile comparison -> maturity assessments and safety-qualified handling -> garden amendment outcome study.

### V. Wildlife ladder
Citizen sighting notes -> phone repeat-photo observations -> local camera trap -> candidate bird classifier -> temporal de-duplication -> crop-damage attribution research -> habitat and wildlife-friendly mitigation -> federated biodiversity map with sensitive coordinates protected.

### VI. Repair and energy ladder
Reclaimed cable testing -> low-voltage bench -> replaceable sensor node -> safe solar charger kit -> power budgeting and weatherproofing -> local ESP32 gateway -> network diagnostics -> microgrid modeling -> professionally supervised solar installation. Distinguish electrical skills from certification.

### VII. Community infrastructure ladder
Seed library labels -> inventory scanner -> accessible signage -> skill/mentor registry -> shared equipment checkouts -> collective project ledger -> autonomous familiar proposals -> cross-site replication guild -> independent federated commons.

## Build cards (example BOM planning only)
**Build A: Offline Harvest Witness**: reused Android phone ($0 donated), kitchen scale ($12-30 if unavailable), reusable plot tags ($5), QR labels ($3), optional basic tripod ($10-20). Camera captures evidence; mass manually entered. ~ $20-60 incremental materials.
**Build B: Single Bed Moisture Familiar**: donated ESP32 if available or controller ($5-15), capacitive moisture probe ($2-10), cable/glands/connector ($5-12), protected low-voltage USB supply ($8-18), enclosure ($5-15), optional temp probe ($3-8). ~ $25-75 incremental new parts. Salvage enclosure/cable after inspection.
**Build C: Local Pi Garden Gateway**: donated Pi/old laptop ($0), known-safe power supply ($8-20), durable storage ($10-20), enclosure ($0-15), Wi-Fi networking infrastructure depending on site. ~ $18-55 assuming donated computer.
**Build D: Compost Monitor**: manual probe thermometer ($10-25) and reused phone ($0); optional waterproof temperature probe ($3-15), controller ($5-15), enclosure/power ($10-35). ~ $10-65.
**Build E: Wildlife Station**: old phone with usable camera ($0), mounting hardware/shroud ($10-25), safe power ($8-20), optional weather cover ($8-25), local gateway storage ($0-30). ~ $18-100, plus substantial maintenance and consent work.
**Build F: Rain Gauge**: manual gauge ($5-15), or salvaged tipping mechanism with reed switch ($0-15) + ESP32 ($5-15) + enclosure/power ($10-35). ~ $5-65.
These are engineering estimates, not purchase orders, and exclude labor/travel/maintenance, spare parts and field failures.

## Value benchmark
Buy a tested precision reference where bad measurements invalidate the experiment. Salvage for control, housing, UI, learning and repairability. A $7.50 commercial capacitive sensor exists (Adafruit STEMMA product 4026), while studies show low-cost moisture sensors need field calibration and can have accuracy/lifetime tradeoffs: https://www.adafruit.com/product/4026 and https://pmc.ncbi.nlm.nih.gov/articles/PMC10007478/. A Pico W was listed at $4.95 by SparkFun during research, though a Pico is not an ESP32 and availability changes: https://www.sparkfun.com/development-boards/raspberry-pi/raspberry-pi-boards.html

## Research tasks
Document donor availability, battery inspection, permissions for collection, disposal rights, solderability, connector pinouts, calibration, protocol availability, total ongoing maintenance, safe e-waste handling. Keep repair cards and component lineage; label reclaimed origin and unknown specifications.
