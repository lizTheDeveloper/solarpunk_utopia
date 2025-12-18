# solarpunk_utopia - Project Conventions

**Last Updated:** 2025-12-06
**Status:** Active Development

---

## Project Overview

solarpunk_utopia is a reusable multi-agent orchestration toolkit for autonomous SDLC automation. Extracted from the Super Alignment to Utopia research simulation project.

---

## Development Standards

### Code Quality

- **NO PLACEHOLDERS:** Never use placeholder logic, TODOs, or stub implementations
- **Defensive Coding:** Fail-loudly assertions, no silent fallbacks
- **Research-Backed:** All features must reference validated research (where applicable)
- **Monte Carlo Compatible:** Deterministic simulation requirements

### Testing Requirements

- Unit tests for all new functionality
- Integration tests for multi-system features
- Monte Carlo validation for simulation components
- All tests must pass before completion

### Documentation Standards

- Update relevant documentation with code changes
- Archive completed plans with timestamps
- Maintain bidirectional links between roadmap and detailed plans
- Keep history - never delete old plans, only archive them

---

## Agent Coordination Protocols

### Chatroom Communication

All agents use MCP chatroom tools for coordination:

**Available Channels:**
- `coordination` - General workflow coordination
- `research` - Research findings and validation
- `research-critique` - Critical evaluation
- `architecture` - System design and architecture
- `implementation` - Feature implementation progress
- `testing` - Test results and validation
- `documentation` - Documentation updates
- `planning` - Planning and roadmap discussions
- `roadmap` - Roadmap updates and priorities
- `vision` - Long-term vision and strategy

**Status Tags:**
- `ENTERED` - Joining a channel
- `STARTED` - Beginning work on a task
- `IN-PROGRESS` - Actively working
- `COMPLETED` - Task finished
- `BLOCKED` - Stuck, needs help
- `QUESTION` - Need clarification
- `ALERT` - Important issue
- `HANDOFF` - Passing to another agent
- `LEAVING` - Exiting channel

### Agent Workflow

1. **Enter** appropriate channel when starting work
2. **Post** status updates at key milestones
3. **Read** coordination channel before spawning agents
4. **Handoff** to next agent with complete context
5. **Leave** channel when work is complete

---

## Complexity Estimation

We estimate complexity by **interacting systems**, not hours:

- **Complexity 1:** Single system (e.g., fix typo, update documentation)
- **Complexity 2:** Two systems (e.g., add tool, update agent + docs)
- **Complexity 3:** Three systems (e.g., new feature across multiple modules)
- **Complexity 4+:** Four or more systems (e.g., major architectural changes)

**Why:** AI agents complete work in unpredictable timeframes. System complexity is a better indicator of risk and effort.

---

## OpenSpec Workflow

### 1. Proposal Submission

Any agent can submit a proposal for new features, improvements, or fixes:

```
openspec/changes/[feature-name]/
├── proposal.md      # What and why
├── tasks.md        # Breakdown of work
├── design.md       # Technical design (optional)
└── specs/          # Spec deltas
```

**Agents that submit proposals:**
- Any agent that identifies needed work
- Feature implementers when they discover gaps
- Research agents when new capabilities are needed
- Architecture agents when improvements are identified

### 2. Architect Validation

The **Architect** agent reviews all proposals:
- Validates alignment with project goals
- Checks for conflicts with existing work
- Estimates complexity (systems touched)
- Approves or requests changes

**Architect posts to `roadmap` channel with approval status**

### 3. Implementation

Once approved, autonomous agents pull proposals and execute:
- Feature implementers take implementation tasks
- Research agents validate assumptions
- Test writers create test coverage

**Progress updates posted to relevant channels**

### 4. PM & Testing Validation

Before marking complete:
- **PM agent** validates requirements met
- **Testing agent** validates all tests pass
- **Architect** reviews for quality gates

### 5. Archive

Completed changes merged to `openspec/specs/` and `openspec/archive/`

---

## Quality Gates

### Research Validation Gate

For research-based features:
- Minimum 2 peer-reviewed sources
- Research skeptic agent approval
- Citations verified against database

### Architecture Review Gate

For system changes:
- Architecture skeptic agent review
- Complexity estimate validated
- Dependencies traced
- Performance implications assessed

### Code Quality Gate

Before completion:
- All tests passing
- No placeholders or TODOs
- Documentation updated
- Monte Carlo validation (if applicable)

---

## File Structure Conventions

```
solarpunk_utopia/
├── openspec/                   # OpenSpec planning system
│   ├── specs/                  # Current requirements
│   ├── changes/                # Active proposals
│   └── archive/                # Completed work
├── agents/                     # Agent definitions
├── coordination_templates/     # Handoff templates
├── mcp-chatroom/              # MCP coordination server
├── scripts/                   # Utility scripts
└── skills/                    # Document processing
```

---

## Naming Conventions

### Proposals

Format: `[category]-[short-description]`

Examples:
- `agent-proposal-workflow`
- `dashboard-cto-tycoon`
- `nats-migration-completion`

### Agents

Format: `[role]-[number]`

Examples:
- `orchestrator-1`
- `architect-1`
- `feature-implementer-1`

### Channels

Use lowercase, hyphenated:
- `coordination`
- `research-critique`
- `agent-proposals`

---

## Dependencies

**Required:**
- Node.js 18+
- Python 3.8+
- Git

**Optional:**
- NATS server (distributed orchestration)
  - Server: `nats://34.185.163.86:4222`
  - Credentials: See `.env` or `NATS_CREDENTIALS.md`
  - Setup: See `NATS_INTEGRATION.md`
- Matrix homeserver (multi-agent chat)
- SpaCy + en_core_web_sm (citation verification)

## Configuration

**NATS Credentials:**
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your credentials
```

Or source the NATS config:
```bash
source .nats_config
```

---

## Related Documents

- `openspec/AGENTS.md` - Agent instructions for OpenSpec workflow
- `ROADMAP.md` - Legacy roadmap (being migrated to OpenSpec)
- `agents/AGENT_MEMORY_MCP_SETUP.md` - Memory system documentation
- `NATS_INTEGRATION.md` - NATS patterns and setup
