# AI Vision, Identification, Counting, and Cataloging — System Specification
**Draft v0.1 — 2026-11-02.** Proposed capability; none of these pipelines are represented as already implemented.

## Product thesis
Put powerful but accountable AI vision into low-cost, community-owned devices. A person can photograph a garden bed, harvest basket, seed tray, compost pile, tool shelf, wildlife station, repair part or plot and ask: **What is this? How many? What's changed? Where does it belong? What action should we take?** The answer becomes a proposed observation, not an unchallengeable fact.

## Supported image tasks
- Detect and count visible objects: seedlings, plant trays, harvested fruit, seed packets, tools, containers, solar parts, insects and candidate bird sightings.
- Identify candidate organisms: crop species, weeds, pollinators, pests, disease symptoms; require human verification of high-consequence identifications.
- Segment: plant canopy, crop bed, erosion boundary, water surface, compost material and damaged leaf region.
- Classify: ripe/unripe, candidate damage type, repair category, seed packet labels, obvious equipment conditions, sorted recyclable components.
- OCR: written plot labels, handwritten harvest sheets, seed envelopes, part numbers and meter readouts, with review of units and ambiguous text.
- Compare across time: repeated photo points, phenology, growth, visual changes, restoration and equipment wear.
- Assist structured cataloging: match image to crop cycle, plot, inventory item, device or reference guide, proposing duplicates.
- Ask grounded follow-ups: 'Place a scale reference', 'Which bed is this?', 'Was the crop harvested or lost?', 'Please weigh this basket'.
- Suggest quests: verify a suspect outbreak, check a sensor, log actual harvest weight, fix a damaged water pipe, review ambiguous wildlife IDs.

## Crucial measurement distinctions
**Visual count** can estimate how many visible items there are; **mass in pounds** requires a scale, calibrated volume-to-mass model, or an explicit uncertain estimate. A photo of kale does not prove harvested pounds or percent of yield lost. A bird in the frame does not establish culpability for crop damage. Visual soil color does not give reliable pH, nitrogen content or soil moisture percentage. Photos are evidence, not substitutes for physical or laboratory measurements.
Store counts with visibility/occlusion assumptions, confidence, capture coverage, and reviewer correction. Distinguish per-frame counts from unique event counts to prevent repeated images counting the same bird or object multiple times.

## End-to-end pipeline
1. Capture: field phone or fixed station; include time, zone, subject and consent status.
2. Local hygiene: hash, redact where necessary, compress, strip unneeded metadata, preserve original securely.
3. Routing: simple model on-device where feasible, otherwise edge Pi/laptop or opt-in remote compute. Default local-only for sensitive imagery.
4. Vision: object detection, segmentation, image-text classification and OCR; use versioned task-specific models.
5. Proposal: create ObservationProposal with labels, locations/bounding shapes, candidate count/quantity, confidence, model provenance and reason.
6. Review: user accepts/edits/rejects; for ecological intervention, hazardous action or contested taxonomy, seek qualified reviewer.
7. Store: immutable source capture, human-reviewed structured events, deduplicated links to ValueFlows or agriculture records.
8. Learn: corrections become an opt-in, permissioned evaluation dataset; no automatic external model training on private images.
9. Surface: map object, seasonal chart, quest, field guide or verified knowledge artifact.
10. Audit: allow reprocessing after model update and compare classifications; never silently rewrite original observations.

## Candidate model families / evaluation
- General detector/segmenter for countable objects, trained on actual site conditions; use transfer learning where legitimate and licensing permits.
- Specialized species recognition with regional taxonomy references.
- OCR + structured field extraction for labels/handwritten records.
- Visual-language model for candidate descriptions and interactive uncertainty clarification.
- Temporal association/tracking for camera events to avoid counting repeat frames as unique visits.
- Lightweight phone-class inference for simple tasks and gateway/desktop/cloud fallback for heavier tasks.
The technology choice is empirical: benchmark representative reused handsets, Pi gateways, server hardware and dataset quality before selecting architecture. Availability, licenses, OS compatibility and performance are not guaranteed.

## Object and evidence schema
VisionJob(id, capture_id, purpose, model_id, model_version, inference_mode, status, latency, compute_cost).
ObjectDetection(id, job_id, category, taxonomy_id, box, mask_ref, count, confidence, occlusion_flag).
ObservationProposal(id, source_job_id, linked_plot_or_asset, quantity, unit, uncertainty, provenance, review_state).
ReviewedObservation(id, proposal_id, reviewer, correction, timestamp, scope, evidence_ref).
DatasetExample(id, capture_id, label, consent, annotation_license, split, context, redaction_status).
ModelEvaluation(id, model_version, site, task, precision, recall, count_error, drift, sample_size, reviewed_by).
Derived stats require source links and stable units. AI cannot directly make irreversible resource transfers or human-safety decisions.

## Accuracy and learning
Create a curated ground-truth benchmark with different light, seasons, foliage density, camera angles, occlusion and phone models. Test precision/recall by species/class; mean absolute error for counts; calibration and false positives for alerts; human correction rate, review time, energy consumption, bandwidth and total maintenance. Revalidate after each major model update and when deployed to a new climate/ecology.

Example: Count sprouts in 10 seed trays, compare human verified counts, document dense/overlapping cases, then publish a model card including error bounds. Do not promote a predictor to automated ecological intervention until prospectively validated.

## UI features
- **Magic Lens:** take photo; AI overlays numbered boxes; edit count and species; turn result into a field journal observation.
- **Pocket Field Guide:** similar local species, uncertain IDs, habitat and observation history.
- **Harvest Witness:** count visible produce and prompt for an actual weight to compute crop yields.
- **Compost Eye:** propose material classification and allow human confirmation; temperature and safety still require real measurements.
- **Repair Familiar:** identify candidate salvage parts, read markings, search community parts inventory.
- **Seasonal Observatory:** chart human-verified measurements and AI-assisted counts with provenance.
- **Wildlife Almanac:** review candidate sightings, track repeat visits, celebrate biodiversity; never assert bird damage without evidence.
- **Quest Camera:** accept evidence of progress or completion; no surveillance or individual productivity scoring.

## Privacy, environmental and safety constraints
Explicit camera authorization, no imaging residential spaces, human faces or license plates for automatic recognition, physical signs for fixed cameras, short configurable retention, permissions per subject. Cloud inference requires opt-in and data transfer review. Limit wildlife disturbance; sensitive species exact locations can be suppressed. AI suggestions must be visible as tentative until accepted.

## Concrete acceptance tests
1. Photo contains 18 visible seedlings; system proposes count and boxes; human can correct to 17 and retain source.
2. Same bird captured in 40 consecutive frames is reported as one candidate visit, not 40 birds.
3. A camera sees bird near kale but assigns no harvest-loss amount without independent evidence.
4. OCR reads '2.5 lb kale' from a handwritten entry; user confirms before a harvest event is created.
5. Crop symptom classified incorrectly can be corrected; model drift and error are logged, no automatic pesticide advice.
6. Privacy deletion propagates to image derivatives, embeddings and shared exports as supported by sync policies.
7. Offline photo remains queued until safe sync; local browsing works.
8. New model version can reinterpret image without overwriting original user-reviewed measurement.
9. Counts are accompanied by coverage/uncertainty and are not silently turned into weight or money.
10. A donated phone with no supported AI accelerator can still capture photos for processing on a local gateway.
