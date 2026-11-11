# Comprehensive Feature Map and Dependency Roadmap
**Status:** Draft v0.1 — 2026-11-02
**Purpose:** No artificial MVP ceiling: capture complete ambition while keeping dependency order clear.

## Experiences
- World navigation: tile maps, multiple indoor/outdoor zones, avatar customization, mobile, keyboard, screen reader alternative, localization, accessibility.
- Live campus: opt-in presence, available mentors, skills, events, work needing attention, community stories.
- Character: portable pseudonymous identities, skill tree, evidence-based endorsements, opt-in journals, quest history, accessible text profile.
- Parties: multi-role, cross-community, synchronous/asynchronous events, low-friction invite/RSVP, project coordination.
- Creation: shared decorative building, custom locations, story quests, in-world exhibitions, community-produced games.
- Community OS: requests/offers, schedules, repair and material inventory, governance, consent and proposal reviews.
- Regeneration: agriculture observability, seeds, soil, water, compost, biodiversity, electricity, food waste and restoration.
- Electronics workshops: ESP32, Pi gateways, mesh, calibration, low-voltage solar, rain gauges and privacy-safe wildlife cameras.
- Research: methods, uncertainty, replicable experiments, community data cooperatives, tool libraries and publishable aggregate datasets.
- Federation: portable skills, opt-in intercommunity trade/volunteering, teaching residencies, shared events, independent deployment.
- Resilience: offline-first logs, emergency preparation, spare parts, localized operations and failure-aware UI.
- Celebration: season recaps, festivals, seasonal wildlife stories, art and shared milestones.

## Dependency graph
1. **Trust foundation** — identities, role/consent system, privacy/safety, accessibility and site policy controls.
2. **Place model** — community/zone/landmark data; stable mapping between real projects and stylized spaces.
3. **Core observability** — manual logging, measurement provenance, crop/water/soil/compost entities and units.
4. **Quest/party/event model** — open tasks, roles, verification and real project linkage.
5. **Playable interactions** — navigable world + people/needs/events affordances; in-world data drill-down.
6. **Device integration** — authenticated sensors, gateways, offline sync, calibrated readings and staleness.
7. **Community publishing** — map editor, knowledge templates and site admin flows.
8. **Federation** — identity disclosure and consent, cross-site events/quests, interoperable skill endorsements.
9. **Bioregional and long-horizon systems** — aggregate ecological baselines, research, community governance and cross-site support.

Dependency does not mean postponement of design: each layer should be specified as fully as feasible before development.

## Hard boundaries between reality and play
Production world data is provenance-linked. A decorative indicator is never authoritative telemetry. Simulation is labeled. Real-life safety controls and access rights remain outside the game renderer. XP never writes directly to inventory/ValueFlows. Approval gates apply to real-world state changes. Offline forks and federation conflicts require audit and human reconciliation.

## Success criteria
- A visitor discovers who/what/when without asking an organizer and without exposing hidden residents.
- A gardener answers annual kale harvested, losses by cause and measurement coverage in a few taps.
- A learner builds and repairs a sensor, and its values appear on the correct in-world bed with freshness/quality visible.
- A collective project moves from idea to party to verified real-world result.
- A new community can make an independent themed map, control its own data and optionally federate.
- A meaningful experience is available without a game controller, smartphone, sensor, login or high technical literacy.

## Next specs to derive
Detailed object data contracts, API adapters against repository services, world-map editor and asset pipeline, mobile UX wireflows, permissions matrix, offline synchronization/conflict semantics, quests/parties state machines, attendance versus skill verification, agricultural reporting formulas, ecological methodology review, localization and institutional governance, residency statement of work, operational runbook and observability/telemetry audit.
