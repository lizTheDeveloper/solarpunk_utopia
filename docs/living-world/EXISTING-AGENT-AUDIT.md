# Existing Agent System Audit and Familiar Reuse Matrix
**Inspection date:** 2026-11-02
**Method:** Static review of repository files on main using GitHub connector. No runtime, network, UI, or test execution. Claims about production readiness are not independently validated.

## Strong reuse candidates
| Source | Observed implementation | Reuse |
|---|---|---|
| app/agents/framework/base_agent.py | BaseAgent, AgentConfig, run/analyze lifecycle, bundle publishing, LLM helper, run stats; configuration defaults auto_approve false | Specialist engine, not a persistent general-purpose planner |
| app/agents/framework/proposal.py | Typed proposals, statuses, approvers, expiration and explanations | Proposal/approval envelope |
| app/agents/framework/approval.py | ApprovalTracker with repository-backed persistence, pending approvals, expiration and execution records | Extend, not rewrite |
| app/database/proposal_repo.py | SQLite-backed ProposalRepository | Persist approvals; separate durable runs/memory needed |
| app/api/agents.py | Authenticated pending/approval endpoints, settings, stats, manual run; approval can invoke execution | Existing approval UX integration |
| app/services/proposal_executor.py | Type-specific ValueFlows action handlers; placeholders remain for cache/forwarding tools | Consequential action bridge; expand guarded adapters |
| app/agents/mutual_aid_matchmaker.py | Offer/need matching with scoring and proposal creation | Familiar's mutual-aid specialist |
| app/agents/work_party_scheduler.py | Plans, participation and proposed work parties; weather placeholder, fallback/mock plan path | Familiar's work-party specialist |
| app/agents/education_pathfinder.py | Skill-gap and prerequisite logic, but mock commitments and hard-coded skills pending true DB integration | Pedagogy logic; needs real data adapter |
| app/agents/permaculture_planner.py | Seasonal planning specialist | Gardening suggestions |
| app/agents/inventory_agent.py | Privacy-aware shortage planner (as documented) | Replenishment and farm inventory |
| app/agents/perishables_dispatcher.py | Expiry-driven food redistribution (as documented) | Waste prevention |

## Architectural findings
1. This is **not a greenfield agent system**: typed agent proposals, persistence, approval workflows and executor classes are real code.
2. Existing seven-agent summary is likely incomplete: app/api/agents.py also imports ConquestOfBreadAgent, ConscientizationAgent and CounterPowerAgent. Inventory the additional agents before making a canonical count.
3. Existing `auto_approve` option in AgentConfig and API needs explicit risk-tier gating rather than unrestricted authorization to execute real-world actions.
4. At least EducationPathfinder remains substantially demo/mock-data-backed. WorkPartyScheduler contains a fallback to mock plans and a weather placeholder.
5. The approval endpoint can execute approved ValueFlows proposals. Future familiar tool use must distinguish approval to *propose*, approval to *communicate*, and approval to *execute*.
6. Docker Compose lists DTN, ValueFlows, discovery, file-chunking, bridge, frontend and nginx, but no dedicated always-running familiar orchestrator service. Deployment options should be designed after inspecting current background worker/runtime conventions.
7. Repository docs claim production readiness and many tests, but this inspection did not run them. Actual integrated behavior and interface coverage must be tested before estimation.

## Gaps for Community Familiar
**Not verified as implemented:** persistent general task plans with pause/resume, trigger subscriptions, schedule runner, event loop and durable worker queues, long-term community memory, separate per-recipient contact consent and quiet hours, channel connectors, announcement publication flow, proactive outbound notifications, dynamic scoped capability grants, game avatar and map presence, human-facing run timeline, multimodal/photo review tool, farm sensor event adapters, federation policies and multi-site policy isolation.
Absence here means *not established by this targeted inspection*, not necessarily absent everywhere in the repository.

## Recommended construction
- Keep existing agents as specialized tools. Familiar is an **orchestrator above them**, not a replacement.
- Add durable AgentRun + PlanStep + Trigger + Outbox + CapabilityGrant + Preference storage and explicit idempotency.
- Build an authorization broker that checks identity, site, subject, allowed tool, risk tier and consent *at execution time*.
- Drive the sprite from orchestration state (sleeping, investigating, proposing, waiting for approval, working, completed, failed).
- Begin with real ValueFlows, work-party, permaculture and education integration tests; remove silent mock fallbacks from production execution paths.
- Add an event source from environmental observations and image review, then schedule/event-driven triggers.
- Make notification delivery recipient-opt-in with preferences, unsubscription, rate and quiet-hour controls.
- Create audit and kill switch, bounded budgets, replay protection, prompt-injection isolation, and human override.
- Publish structured app-level API contracts and add tests for double sends, stale state, offline sync and abuse.

## Follow-up code examination checklist
- Inspect all current agent subclasses, full tool interfaces, API auth/authorization, service lifespan/startup, tests, persistence schema and deployment processes.
- Determine which additional three political-economy agents are wired and whether proposal executors handle their types.
- Validate how `auto_approve` actually executes across run/publish/API routes and whether permission boundaries hold.
- Run existing tests and create integration tests for one real workflow from observation to approval to completed resource event.
