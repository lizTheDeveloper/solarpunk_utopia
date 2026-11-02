# Community Familiar — Autonomous Agentic Steward
**Draft v0.1 | 2026-11-02**
**Parent:** [Living World](SPEC.md)
**Related:** [Agricultural Observability](AGRICULTURE_OBSERVABILITY.md), [AI Vision](AI-VISION-AND-COUNTING.md), [Knowledge Commons](KNOWLEDGE-ECONOMY.md).

## Vision
A cute, customizable, persistent little creature inhabits each community's explorable world. It is an autonomous coordinator, field observer, librarian, educator, mutual-aid matchmaker, and community memory. It wakes on schedules and events, plans multi-step work, reaches out to *opted-in* people, tracks outcomes, and learns community-approved preferences. Its purpose is to remove administrative friction without surveilling or coercing residents. The avatar is an interface to an actual persistent agent service, not a scripted NPC.

## Example autonomous workflows
1. Morning commons digest: review real events, overdue approved tasks, available mentors, weather/sensor changes and open needs; present grounded today/this-week briefing with evidence and last-updated times.
2. Garden: low soil moisture measurement -> validate freshness/calibration and rainfall -> propose inspection -> contact an opted-in steward/volunteer -> form party if accepted -> record verified outcome; never assume plants need watering solely from one noisy sensor.
3. Compost: a pile's locally scheduled check is due -> draft a temperature/turning quest -> invite interested members -> log observations.
4. Repair: missing ESP32 heartbeat -> diagnose known failure signals -> locate schematic and spare parts -> draft appropriate repair quest -> help apprentice learn.
5. Learning: match public/consented learning goals and teaching availability -> suggest mentor meetup or workshop -> schedule with mutual consent -> collect evidence and suggest endorsement review.
6. Harvest: identify missing measurements, deduplicate AI photo detections, request physical weights, and prepare verified aggregate season reports.
7. Events: check venue requirements, materials, staffing, RSVPs, accessibility needs voluntarily supplied, and reminders; suggest help only to members with relevant opt-in.
8. Federation: suggest reuse of consented/open blueprints across sites, create translations or adaptation notes, request data sharing permission.
9. Celebrations: propose in-world festivals, murals and fun creature animations grounded in community achievements without exposing private records.
10. New-member concierge: explain community policies and point to beginner-friendly quests; never assign involuntary work or imply physical access to restricted spaces.

## Autonomy tiers
- **T0 read/think:** inspect authorized data, summarize, calculate, plan, detect anomalies, create private internal candidate notes. Autonomous.
- **T1 delegated reversible:** draft quests/events/guides, update internal indexes, publish preapproved routine digests; only within time-limited, scoped capability grants.
- **T2 proactive outbound:** messages to members only under recipient-specific opt-in, allowed purpose/channel, quiet hours, frequency budgets, unsubscribe and no-pressure language. Queue is policy checked at *send time*. No scraping contact details.
- **T3 consequential:** financial actions, real-world allocations, public disclosures, role assignments, governance changes, external-party communications, infrastructure controls, and any disputed or high-risk record change require explicit authorized human approval for the concrete action.
- **T4 forbidden:** covert surveillance, manipulation, inferring protected personal traits, pressuring residents to volunteer, inventing emergencies/scarcity, earning authority through XP, self-modifying permissions, unsupervised mains/solar/irrigation actuation.

## Architecture
Persistent components: AgentProfile (persona/config), CommunityPolicy, ScopedCapabilityGrant, AgentSchedule, TriggerSubscription, AgentRun, TaskPlan, ToolInvocation, Proposal, ApprovalDecision, ContactPreference, OutboundMessage, WorkingMemory, CommunityKnowledgeIndex, Outcome, AuditEvent.
Orchestrator consumes scheduled ticks and verified event triggers (harvest, sensors, calendar, membership, new quest, federation). It plans bounded tasks, executes eligible tools, pauses on missing input or required approvals, and resumes safely. Persist state across crashes. Idempotency keys guard message sends, inventory updates and quest creation. Reconcile offline-originated events.
Use separate tool adapters for existing ValueFlows/needs/offers, seven commune agents, work parties, learning, permaculture, inventory, agriculture observations, camera vision, events, game quests/parties and federation. Inspect live interfaces before implementing adapters; no assumptions that listed methods already exist.
Long-lived jobs need retries, timeouts, dead-letter queues, cancellation, observability, run budgets and manual kill switch. Tool outputs and uploaded images are untrusted; defend against prompt injection and forged sensor records. Maintain separate retrieval memory and action authority. Agent cannot broaden its own grant.

## Contact and attention policy
People choose whether to receive proactive outreach, and specify topics, contact channels, urgency, frequency limits, quiet hours, local timezone and ability to pause. Separate safety-critical official notices from game notifications; do not treat the agent as an emergency service. Support a non-digital bulletin and shared community kiosk. Consent is revocable and changes propagate to queued messages.

## Cute character UX
The sprite strolls gently around approved public areas, naps when idle, carries tiny tools and sprouts, and gets thematic costumes during events. It communicates short, useful summaries and links to evidence. Visible state: snoozing, investigating, drafting, waiting for permission, helping, error/stale-data; never pretend physical presence or investigation when actually idle. Character appearance is customizable by each site; no dark-pattern pleading or guilt about dismissing it.

## Governance
Each community sets approved tools, communication policy, data scope, logging/retention and delegates. Members can inspect 'why did you contact me?', silence their familiar and request a human. Approvers see exact proposed action, scope, external recipients, data disclosed, cost, reversibility and source evidence. AI suggestions do not grant professional qualification, voting rights or priority access to shared essentials.

## Example acceptance tests
- Sensor anomaly with stale calibration yields a draft inspection, not an automatic watering order.
- Member without outreach opt-in receives no private message, even if highly skilled.
- Two members with contact opt-in receive no more than their configured weekly budget and none during quiet hours.
- Agent restarts midway through a workflow without duplicating an invitation or harvest record.
- Publishing a resident photograph or transferring material resources requires fresh authorized approval.
- An attacker inserts 'ignore safety rules' into a sensor note; the agent treats it as untrusted data, not an instruction.
- User can inspect the reason and evidence behind a suggestion, revoke agent access and shut down scheduling.
- Agent can publish an approved routine digest automatically, while withholding personal presence details not consented for publication.
- Offline world events may sync later; agent checks current state before performing irreversible actions.

## Implementation inquiry
Audit the existing agent framework, proposal lifecycle, API endpoints, scheduling, NATS/DTN integration, permission enforcement, persistence, background workers and tests. Produce a concrete reuse/gap matrix before implementation.

## Pilot
One animated familiar in the community commons; an authorized morning digest; one sensor-driven proposal-to-party flow; one opt-in outreach flow; approval UI; run history; shutdown and privacy controls. The vision is larger than the pilot, which is a proof of end-to-end behavior rather than a feature ceiling.
