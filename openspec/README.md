# OpenSpec Integration

**Integrated:** 2025-12-06
**Status:** Active

---

## What is This?

This directory contains the OpenSpec-based proposal management system for the solarpunk_utopia. OpenSpec replaces the previous ROADMAP.md system with a structured, spec-driven approach to planning and executing work.

---

## Quick Start

### For New Projects

**Using solarpunk_utopia in a new project?** This OpenSpec structure is automatically set up when you run:
```bash
/path/to/abstract_agent_team/scripts/init_new_project.sh
```

See `../INTEGRATION.md` for complete setup guide.

### For Agents

1. **Need to submit a proposal?** → See `AGENTS.md` section "Submitting Proposals"
2. **Need to validate a proposal?** → See `AGENTS.md` section "Validating Proposals" (Architect)
3. **Need to implement approved work?** → See `AGENTS.md` section "Implementing Approved Proposals"
4. **Need to validate implementation?** → See `AGENTS.md` sections "PM Validation" and "Testing Validation"

### For Humans

1. **Want to understand the workflow?** → See `WORKFLOW_SUMMARY.md`
2. **Want to see what's active?** → Check `changes/` directory
3. **Want to see completed work?** → Check `archive/` directory
4. **Want to understand requirements?** → Check `specs/` directory
5. **Want to know project conventions?** → See `project.md`

### Templates

Need to create new specs or proposals? Use the templates:
- `templates/spec-template.md` - For creating new specs
- `templates/proposal-template.md` - For creating new proposals
- `templates/tasks-template.md` - For task breakdowns

---

## Directory Structure

```
openspec/
├── README.md                    # This file - start here
├── AGENTS.md                    # Detailed workflow for agents
├── WORKFLOW_SUMMARY.md          # High-level workflow overview
├── project.md                   # Project conventions & standards
│
├── specs/                       # Living requirements (source of truth)
│   ├── agent-system/spec.md     # Agent system requirements
│   ├── coordination/spec.md     # Coordination system requirements
│   └── dashboard/spec.md        # Dashboard requirements
│
├── changes/                     # Active proposals
│   ├── dashboard-cto-tycoon/
│   │   ├── proposal.md          # Status: Approved, Priority: TIER 1
│   │   └── tasks.md
│   └── agent-memory-cleanup-by-size/
│       ├── proposal.md          # Status: Approved, Priority: TIER 2
│       └── tasks.md
│
└── archive/                     # Completed proposals (timestamped)
    └── [empty - no completed work yet]
```

---

## The Workflow (Visual)

```
Any Agent
    │
    │ Creates proposal
    ▼
Architect ─────► Validates
    │
    │ Approves
    ▼
Feature Implementer ─────► Executes
    │
    │ Completes
    ▼
PM Validator ─────► Checks requirements
    │
    │ Passes
    ▼
Test Validator ─────► Checks quality
    │
    │ Passes
    ▼
Architect ─────► Archives
    │
    ▼
  Done ✓
```

---

## Current Proposals

### TIER 1 (High Priority)

**CTO Tycoon Dashboard** (`dashboard-cto-tycoon/`)
- Status: Approved
- Complexity: 4 systems
- Portfolio view across all projects
- Agent dispatch system
- Real-time monitoring
- Financial integrations (GCP, Anthropic, Stripe)

### TIER 2 (Medium Priority)

**Agent Memory Size-Based Cleanup** (`agent-memory-cleanup-by-size/`)
- Status: Approved
- Complexity: 1 system
- Size-based cleanup trigger (20 entries default)
- Prevents memory bloat during busy periods
- MCP tool for manual triggering

---

## Key Agents

| Agent | Role | Key Actions |
|-------|------|-------------|
| **architect** | Validator & Archivist | Approve proposals, archive completed work |
| **feature-implementer** | Executor | Pull approved proposals, implement them |
| **pm-validator** | Requirements Validator | Verify requirements met, scenarios pass |
| **test-validator** | Quality Validator | Run tests, check quality, enforce standards |
| **orchestrator** | Coordinator | Coordinate multi-agent workflows, handle blockers |

---

## Key Documents

| File | Purpose | Audience |
|------|---------|----------|
| `AGENTS.md` | Detailed workflow instructions | AI Agents |
| `WORKFLOW_SUMMARY.md` | High-level workflow overview | Humans & Agents |
| `project.md` | Project conventions & standards | All |
| `README.md` | This file - quick orientation | All |
| `specs/*/spec.md` | Living requirements | Implementers |
| `changes/*/proposal.md` | Proposal details | All |

---

## How to Find Work

**For agents looking for work to do:**

```bash
# Find approved proposals ready for implementation
grep -r "Status: Approved" openspec/changes/*/proposal.md

# See what's in progress
grep -r "Status: In Progress" openspec/changes/*/proposal.md

# See what's blocked and needs help
grep -r "Status: Blocked" openspec/changes/*/proposal.md
```

---

## How to Check Status

**For humans checking project status:**

```bash
# List all active proposals
ls -la openspec/changes/

# List all archived (completed) proposals
ls -la openspec/archive/

# Read a specific proposal
cat openspec/changes/dashboard-cto-tycoon/proposal.md

# Check validation status
cat openspec/changes/dashboard-cto-tycoon/pm-validation.md
cat openspec/changes/dashboard-cto-tycoon/test-validation.md
```

---

## Migration from ROADMAP.md

**What changed:**

- **Before:** Single `ROADMAP.md` file with checkboxes
- **After:** Structured proposals in `openspec/changes/`

**What stayed the same:**

- Complexity estimation by systems touched (not hours)
- Quality gates and validation requirements
- Agent coordination via chatroom channels
- Historical preservation (now in `archive/`)

**What improved:**

- Structured requirements with SHALL/MUST and WHEN/THEN
- Clear proposal lifecycle (Draft → Approved → In Progress → Validation → Completed → Archived)
- Formal PM and Testing validation gates
- Better traceability and history

---

## Next Steps

1. **Agents:** Read `AGENTS.md` to understand your role in the workflow
2. **Implementers:** Check `changes/` for approved proposals to work on
3. **Validators:** Monitor chatroom channels for validation requests
4. **Humans:** Read `WORKFLOW_SUMMARY.md` for the big picture

---

## Questions?

**Agent workflow questions:** See `AGENTS.md`
**Project conventions:** See `project.md`
**Workflow overview:** See `WORKFLOW_SUMMARY.md`
**Spec format:** Look at examples in `specs/*/spec.md`
**Proposal format:** Look at examples in `changes/*/proposal.md`

---

**Welcome to the Eighth Iteration. Let's build something great.**
