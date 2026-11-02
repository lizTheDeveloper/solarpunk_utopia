# Familiar Async Execution, Approval Queues and Delegation
**Status:** Draft v0.1 — 2026-11-02

## Goal
The familiar never stalls just because a person has not responded. It safely progresses independent work while exact-action approvals remain pending, and transparently shows what is awaiting humans versus what is underway.

## State machine and concurrency
Every plan is a DAG, each node specifying input evidence, prerequisites, risk, grant, expected side effects, budget, checkpoint and timeout. Workers claim runnable nodes via durable leases and heartbeat. Nodes awaiting approvals or external responses release worker capacity. A resumer consumes approval, message response, sensor event or clock events, checks freshness and only requeues now-unblocked nodes. Global and per-community concurrency limits prevent monopolization.

## Approval objects
ApprovalRequest(id, plan_id, step_id, requester_agent, site, action_type, exact_payload_hash, clear_summary, source_evidence, cost, risk, reversible, required_approvers, quorum_policy, created_at, expires_at, status, comments, escalation_policy). Approvers authenticate and authorize for concrete site and action at decision time. Payload changes invalidate prior approval; reject and edits create a revised request, never quietly execute an altered action. Approvals expire and revoked authorities are respected.

## Inbox and workflow
- One inbox for site stewards and individual members, with sorting by urgency, risk, actual deadline, project and age.
- Clear summary, exact action details and preview of consequences.
- Approve / Deny / Request Changes / Ask Agent / Delegate according to authority / Snooze.
- Batch only compatible low-risk actions, never hidden high-impact grants.
- Separate 'FYI' digest from actual approval requirement; accessibility/mobile and offline paths.
- Reminder policy respects quiet hours; no spam, guilt, artificially urgent tasks, or approval inferred from silence.
- Delegation has expiry, scope, recipient acceptance and audit.
- Agent always has a 'continue safe work' path when approvals await.

## Async patterns
**Scatter/gather:** independent specialist tasks run concurrently, results are reconciled with provenance and conflicts noted.
**Long research:** save checkpoints (references, files, hypotheses, completion criteria), free model context and resume later with a fresh model call.
**Await human:** persist approval request, release lease; launch independent documentation, alternative seed lookup and lessons.
**Await external:** record reply endpoint/conditions and timeout; never assume a supplier or community partner replied.
**Event trigger:** incoming sensor or new publication triggers a fresh scoped subtask with deduplication.
**Workflow saga:** each effect gets an idempotency key, receipt and defined compensation/reconciliation path.
**Scheduled review:** at actual seasonal windows, revisit hypotheses with current evidence, not endless polling.
**Backpressure:** cap number of open messages, approvals, concurrent calls and compute costs; low-value ideas queued, not forced onto members.

## Example 72-hour timeline
08:00 Day 1: familiar detects low spinach yield data coverage, opens read-only research, soil analysis and seed-source subtasks.
09:00: proposes trial bed and seed order, posts two approvals, then continues preparing optional workshop and documentation.
Day 2: steward denies purchase but approves trial; familiar finds donated seeds, drafts party invitation, waits on outreach consent while continuing soil monitoring.
Day 3: consented party accepts; workshop happens, observations logged, future follow-up scheduled. No worker was blocked by human response latency.

## Autonomy and safety
LLM's apparent intention is never enough to authorize anything; policy broker is the final authority. Do not authorize spending, public publication, property access, pesticide application or irrigation actuation through generalized 'do what is best' approval. Human decisions are not an excuse to circumvent laws or qualifications.

## Acceptance tests
- 50 long-running plans, 20 approvals pending: independent steps still execute within fair scheduling.
- Approval approved after payload edit: blocked until a new approval.
- Worker dies after external write but before response: ledger reconciles; no duplicate write.
- Guest receives an invitation only if opted in at actual send time.
- Old photo or stale moisture reading cannot trigger irreversible physical action.
- Late external callback after cancellation is retained in audit but triggers no new action.
- Running plan can be paused by site operator and disabled without losing audit.
