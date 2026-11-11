# Community Familiar — Autonomous Runtime and Dedicated Computer
Status: Draft v0.2 — 2026-11-02. Proposed implementation, not deployed.

## Vision
A persistent, cute agent lives on a community-controlled Raspberry Pi, reused laptop, dedicated VM, or small server. It operates between visits: observes approved data, investigates opportunities, delegates research, organizes projects, asks for approvals only when necessary, resumes independently, and keeps an inspectable work journal. Model-agnostic intelligence; community-governed actions.

## Service topology
- **World/UI:** familiar sprite, community floor, chat, notification inbox, approvals workbench, run timeline, accessible text interface.
- **Ingress:** timestamped field observations, calendars, ValueFlows events, approved photo interpretations, task changes, user messages, federation events.
- **Durable event bus:** process events at least once; dedup by event key; preserve audit lineage; handle offline and replay.
- **Opportunity finder:** rules + model investigation of new needs, skills, research and potential improvements.
- **Planner:** outputs typed task DAG (dependencies, evidence, tool grants, risk tier, cost and status).
- **Scheduler / durable workers:** independent jobs on schedules and triggers; leases, checkpoints, heartbeats, resumption, capped retries, dead letters.
- **Approval broker:** creates requests but NEVER waits synchronously for humans; approvals are durable external events.
- **Execution broker:** policy-checked tool calls with scoped credentials, snapshots, receipt and compensation.
- **Research sandbox:** isolated filesystem and computing budget for coding, analyses, maps and reports; no arbitrary host shell access.
- **Model router:** standard interface for hosted and local LLMs, vision, embeddings, extraction; graceful deterministic fallback.
- **Knowledge store:** source-grounded historical community observations, research, failures, decisions and reusable designs.
- **Outbox:** consented channel messages sent at permitted hours; never inferred from a skill profile.
- **Telemetry:** outcomes, costs, privacy, quality, worker status, stale sensors, tool failures and queue age.

## The asynchronous rule
**A task WAITING_APPROVAL must not block its worker or unrelated steps.** An awaiting node checkpoints itself and releases its lease immediately; independent nodes on its task DAG remain runnable. If a human approves, denies, edits or lets the request expire, that event wakes the affected plan and revalidates its preconditions. No polling the model for a human reply.

A goal can spawn multiple plans; each plan can contain independently scheduled research, procurement alternatives, documentation, curriculum, and proposal steps. Approval-required leaf actions may wait while documentation and evidence collection proceed. It may not execute dependent actions early or bypass approval.

## Task model and state transitions
Goal: proposed, active, paused, completed, canceled.
Plan: drafting, active, awaiting_inputs, completed, failed, canceled.
Step: queued, leased, running, waiting_approval, waiting_external, retry_scheduled, succeeded, rejected, canceled, failed.
Approval: drafted, pending, approved, denied, expired, superseded, revoked.
Outbox: drafted, policy_checked, scheduled, sending, delivered, failed, canceled.

Transitions use a transactional store + outbox for atomic event intent. Worker leases expire and retries are safe via idempotency keys. For non-idempotent external APIs, use an action ledger and reconciliation rather than assuming exactly-once delivery.

## Approval queue UX
Views: **Needs my decision**, **Waiting on others**, **Can continue automatically**, **Expired**, **Completed**. Filter by project, place, decision type, risk, cost, requested-by, deadline (genuine), and required approvers. Each request shows the *exact action*, evidence, alternatives, recipients, cost/resources, site permissions, reversibility, expiry and what work continues without approval. Actions: Approve, Reject, Request changes, Delegate (subject to governance), Snooze/remind me (within recipient preferences), Bulk approve only low-risk same-policy actions with per-item receipts, Cancel. Approval cannot be gained from a click in unrelated game UX.

Approval queue never traps the agent. Escalation to a steward is only within defined roles and policies; silence is not consent, and expiry is a normal outcome. Human absence should not require a model to keep running.

## Autonomy boundaries
T0 observe/research/analyze and draft private notes; T1 reversible actions under time-limited explicit grants; T2 opt-in outbound messages with frequency limits and send-time checking; T3 consequential decisions (money, resource allocation, publicly disclosing personal information, governance, external outreach, control of real infrastructure) require authorized exact-action approvals; T4 disallowed covert monitoring, permission self-escalation and unsafe autonomous high-voltage/irrigation actuation. Permissions enforced by tools, not instructions.

## Model-agnostic request interface
ModelRequest{task_id, messages, available_tool_schemas, modality, output_schema, privacy_class, budget, timeout}
ModelResponse{content, structured_data, tool_requests, provider, model_id, usage, latency, error}.
Support local model hosts, OpenAI-compatible gateways, and explicit hosted providers; capability detection for tool calls, vision and context. Strict JSON/schema validation, no silent external upload of restricted data, provider fallback subject to privacy policy. Durable runs must not depend on context staying in one model session.

## State and memory
PostgreSQL (shared multi-site) or SQLite WAL (one-site pilot) for authoritative jobs, events, permissions and receipts. Blob store for photos and artifacts with provenance and retention; searchable local indexes for approved knowledge; vector index optional. Separate immutable observation facts from model hypotheses. State persistence must survive reboot and model changes.

## Dedicated compute
**Pi / lower-powered gateway:** Raspberry Pi 4/5 or equivalent with reliable SSD, adequate power/cooling, LAN, backups. Run queue, rules, MQTT, database, UI and small inference where tested; outsource heavier vision/LLM only with permission. An old laptop often provides better x86 compatibility and more storage/CPU for modest workloads.
**Dedicated mini-PC / VM:** isolated Linux host for workers, indexed knowledge, larger local models with adequate RAM/GPU; use measured benchmarks not promises. Run persistent containers/services under automatic restart.
**Hybrid:** sensor Pi is the edge collector; community server/VM is familiar coordinator; optional hosted model router. Local operations survive loss of internet.
**Isolation:** separate Linux user / rootless containers; read-only app code; scoped working directories; worker cannot mount Docker socket, modify host service definitions, access unrestricted shell or arbitrary local networks; firewall outgoing calls and protect camera/people data. Per-task temporary workspaces and quotas.

## Filesystem sketch
```
/srv/familiar/
  config/              # non-secret policy configuration
  state/               # SQLite or application state; backed up
  events/              # append-only archival records
  communities/<id>/
    knowledge/          # reviewed manuals and local research
    artifacts/          # charts, guides, blueprints, reports
    datasets/           # access-scoped field photos and observations
    runs/<run-id>/      # isolated ephemeral analysis workspace
  cache/
  backups/             # encrypted, off-host copy
```
Secrets are managed outside these user-writable folders. Disk quotas, lifecycle cleanup, migration, encryption, backup verification and operator controls are requirements.

## Loop example
Morning trigger -> read tasks and confirmed observations -> spawn parallel work: inspect compost records, research candidate crops, audit sensor network, draft event digest -> generate approval requests for optional participant invites and spending -> continue independent soil research and blueprint writing -> night quiet hours defer outgoing notices -> human approves seed trial tomorrow -> event wakes queued action -> verify seed availability and authorization again -> publish consented quest -> track experimental outcome.

## Reliability tests
Worker crashes mid-plan without duplicate messages; Pi reboots during approval; decision after expiration rejected; approvals never bypassed by alternative model; independent research continues while spending approval pending; offline device sync does not double count harvest; revoke email consent before scheduled send -> no message; 100 pending approvals do not starve work queue; disk full and provider outage degrade transparently; restore from backup and replay receipts.
