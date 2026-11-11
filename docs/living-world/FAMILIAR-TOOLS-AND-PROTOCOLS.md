# Community Familiar — Tools and Protocols
Status: Draft v0.1 — 2026-11-02. Interface proposal, not existing API.

## Contract
All tool calls: request_id, community_id, actor_id, run_id, capability_grant_id, tool_name/version, inputs, preconditions, privacy_class, idempotency_key. Outputs: typed result, provenance, uncertainty, access scope, action receipt, retryability. Router validates schemas and action policy before execution; LLM does not receive credentials.

## Read tools
site.get_goals; map.list_zones; map.get_landmark; farm.list_plots; farm.crop_history; farm.harvests; farm.losses; soil.tests; sensors.readings; weather.history; compost.piles; wildlife.reviewed_sightings; water.tanks; energy.meters; inventory.search; members.search_opted_in; skills.find_mentors; calendar.list_public_events; quests.list; proposals.get; federation.search_public.

## Research and working tools
knowledge.search_with_citations; knowledge.get_protocol; research.search_public; research.fetch_source; ecology.get_native_range; agronomy.local_extension; seeds.find_suppliers; supplier.check_stock; model.vision_propose_labels; camera.review_authorized_capture; image.compare_timepoints; compute.run_bounded_python; maps.create_proposed_asset; documents.draft_build_card; curriculum.draft_workshop; experiment.design_trial; report.build_chart.
Sources are untrusted; supplier availability must be checked with timestamp and never fabricated. Model output is a proposal until reviewed.

## Write/action tools
observations.propose; corrections.submit_for_review; quests.draft; quests.publish_approved; parties.draft; event.create_approved; outbox.schedule_approved; valueflows.create_approved_economic_event; purchase.submit_request; device.request_diagnostic; federation.share_approved_artifact; code.create_pr_only.
All cross-boundary calls require scoped execution authorization. No unconstrained remote SSH, self-edited production source, arbitrary filesystem access, sending mail based solely on model text, or direct purchase/infra actuation.

## Scheduling / agent tools
goals.create; plan.create; plan.spawn_subtask; plan.await_approval; plan.await_external; plan.checkpoint; plan.cancel; schedule.create_with_policy; triggers.subscribe_with_policy; approvals.request; approvals.inspect; approvals.on_decision; capability.inspect; tool.inspect_schema; runs.get_status; worker.get_budget; feedback.record; incident.report.

## Agentic specialist delegates
Garden advisor, ecological researcher, seed scout, reclaimed electronics librarian, sensor diagnostician, workshop designer, community scheduler, economics modeler, visual cataloger, accessibility reviewer and privacy/policy reviewer. All delegates run within parent scope, quota and purpose. Passing a task to a delegate never broadens access. Results are evidence/plan candidates only.

## Example goal decomposition
'Improve our spring food resilience' creates parallel tasks: baseline harvest completeness; climate/soil facts; candidate crop and native habitat alternatives; available seed sources; water constraints; volunteer interests; salvage-powered monitoring build; workshop materials. Join after evidence; draft alternatives with uncertainty; approval only for trials/communications/purchases; others continue in parallel.

## Integration strategy
Reuse existing Solarpunk Utopia BaseAgent, proposals, ApprovalTracker and proposal executor via adapters. Do not claim integration until real endpoint schemas and permission semantics have been tested. Read-only research adapters first; write gates second. Existing human approval system must be extended to approvals-for-steps and scopes, not replaced.
