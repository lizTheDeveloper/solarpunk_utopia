# Reclaimed Phones as Field Instruments
**Draft v0.1 — 2026-11-02.** Companion to Agriculture Observability, Sensors & Workshops and Knowledge Commons.

## Core idea
Old phones become community-owned field notebooks, image stations, maker-lab terminals, audio logs, kiosks and optional gateways. Cameras turn visual changes into trackable evidence. Every capability is detected per device: no assumption that all phones support camera APIs, raw sensors, background capture or sustained operation.

## Modes
1. **Field notebook** — take photos, short video or voice notes; scan plot QR; select crop/plot; log harvest weight, pest observations, compost temperatures and soil results even when offline.
2. **Repeat-photo station** — guide framing and camera angle to show a bed, erosion site, tank, nursery or compost pile across seasons. Retain camera placement, scale reference and timestamps.
3. **Wildlife observation camera** — crop-facing station for candidate birds, pollinators, mammal visits and suspected damage. Identifications remain hypotheses until reviewed.
4. **Inventory lens** — photograph seed packets, tools, trays, baskets, salvaged electronics, pantry shelves, compost materials and repairs. AI proposes objects/counts for confirmation.
5. **Workshop station** — shared phone displays instructions, wiring illustrations, safe operating instructions and live readings for nearby ESP32/Pi instruments.
6. **Community kiosk** — event, quest and garden info in a low-cost, accessible, nontracking interface.
7. **Sensor gateway (device-dependent)** — collect nearby instruments via supported network protocols; buffer and forward readings to local Raspberry Pi gateway or community server.

## Capture workflow
QR/landmark → photo → local storage + unique capture ID → user chooses purpose → optional on-device AI → proposed tags/counts and confidence → human review/correction → verified observation → linked quest/plot/resource records → aggregate reporting. Permit manual-only capture throughout.

## Photo data contract
Capture(id, owner, community, location_ref, subject_ref, timestamp, device_id, content_hash, image_orientation, capture_method, scale_reference, privacy_scope, retention, license, offline_status).
Annotation(id, capture_id, model_version, candidate_taxon_or_object, bbox_or_mask, count, probability, reviewer, review_state, evidence_notes).
Observation(id, capture_id, metric, value, unit, method, uncertainty, timestamp).
Consent and deletion policies apply to derivative crops, thumbnails, embeddings and federation caches as well as originals.

## Deployment and power
Check battery health, OS security update availability, weatherproofing, safe charging, heat, moisture, enclosure, storage, local power and Wi-Fi range. Prefer intermittent captures over unmaintained 24/7 phone recording. Keep phones in a maintainable inventory with repair/retirement plan. Never attach damaged/swollen lithium-ion batteries to unattended power. Support wiped, account-removed donated phones and avoid exposure of prior owners' photos/accounts.

## Privacy and ethical ecology
No covert human monitoring, face recognition, personal tracking or housing-area cameras. Clear signage, camera-facing areas, opt-in participation, access controls and short retention. Bird presence cannot by itself establish crop loss. Sensitive species locations may require redaction. Do not use imagery to score volunteer productivity.

## Workshops
Refurbish a phone; photograph and tag one garden bed; establish repeat-photography station; capture and annotate pest observations; link image to crop loss (without claiming unsupported yield); configure on-device vision where supported; connect ESP32 readings via Pi gateway; learn calibration, false positives and privacy; publish an accessible community field guide.

## Validation
Works with no network; preserves photo and edits through sync; avoids duplicate records; shows stale capture/reading labels; consent withdrawal removes authorized access to images and derived public information, while disclosing unavoidable offline cache limitations.
