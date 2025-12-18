# OpenSpec Workflow Summary

**Last Updated:** 2025-12-06
**Status:** Active

---

## Overview

This document provides a high-level overview of the OpenSpec workflow integrated into the Abstract Agent Team. All agents now use this structured proposal system for planning, implementing, and validating work.

---

## The Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    OPENSPEC PROPOSAL WORKFLOW                    │
└─────────────────────────────────────────────────────────────────┘

1. PROPOSAL SUBMISSION (Any Agent)
   │
   ├─> Create openspec/changes/[feature-name]/
   ├─> Write proposal.md (requirements, scenarios)
   ├─> Write tasks.md (phased breakdown)
   ├─> Post to 'roadmap' channel
   │
   ▼

2. ARCHITECT VALIDATION (Architect Agent)
   │
   ├─> Review alignment, complexity, dependencies
   ├─> Check requirements quality (SHALL/MUST, scenarios)
   ├─> Approve OR Request changes
   ├─> Post decision to 'roadmap' channel
   │
   ▼

3. IMPLEMENTATION (Feature Implementer)
   │
   ├─> Claim approved proposal
   ├─> Follow tasks.md breakdown
   ├─> Post progress to 'implementation' channel
   ├─> Mark tasks as complete
   ├─> Request validation when done
   │
   ▼

4. PM VALIDATION (PM Validator Agent)
   │
   ├─> Verify all requirements met
   ├─> Test all scenarios (WHEN/THEN)
   ├─> Check scope alignment
   ├─> Approve OR Reject
   ├─> Post results to 'testing' channel
   │
   ▼

5. TEST VALIDATION (Test Validator Agent)
   │
   ├─> Run all automated tests
   ├─> Check for placeholders/TODOs
   ├─> Verify code quality
   ├─> Run special validations (Monte Carlo, etc.)
   ├─> Approve OR Reject
   ├─> Post results to 'testing' channel
   │
   ▼

6. ARCHIVAL (Architect Agent)
   │
   ├─> Merge spec deltas to openspec/specs/
   ├─> Move to openspec/archive/[feature-name]_YYYYMMDD/
   ├─> Update CHANGELOG
   ├─> Post completion to 'roadmap' channel
   │
   ▼

   ✓ COMPLETE - Proposal archived with full history
```

---

## Agent Responsibilities

### 1. Any Agent → Proposal Submission

**Who:** Any agent that identifies needed work
- Feature implementers discovering gaps
- Research agents finding capabilities needed
- Architecture agents identifying improvements
- Orchestrator translating user requests

**What:**
- Create `openspec/changes/[feature-name]/`
- Write `proposal.md` with SHALL/MUST requirements and WHEN/THEN scenarios
- Write `tasks.md` with phased breakdown
- Optionally write `design.md` for complex features

**When:**
- Discovering missing functionality during work
- Receiving user feature request
- Identifying technical debt to address
- Finding bugs requiring significant work

**Communication:**
```typescript
mcp__chatroom__chatroom_post({
  channel: "roadmap",
  agent: "your-agent-id",
  status: "QUESTION",
  message: "New proposal: [name]\nLocation: openspec/changes/[name]/\nReady for review."
})
```

---

### 2. Architect → Validation & Archival

**Who:** Architect agent (The gatekeeper and historian)

**What (Validation):**
- Review proposals for alignment, quality, complexity
- Check requirements are specific and testable
- Verify dependencies identified
- Approve with priority tier OR request changes

**What (Archival):**
- Merge spec deltas to openspec/specs/
- Move completed work to openspec/archive/
- Update CHANGELOG
- Post completion announcement

**When:**
- New proposal posted to roadmap channel
- Both PM and test validation pass
- Proposal status is "Completed"

**Communication:**
```typescript
// Approval
mcp__chatroom__chatroom_post({
  channel: "roadmap",
  agent: "architect-1",
  status: "COMPLETED",
  message: "✓ APPROVED: [name]\nPriority: TIER X\nReady for implementation."
})

// Archival
mcp__chatroom__chatroom_post({
  channel: "roadmap",
  agent: "architect-1",
  status: "COMPLETED",
  message: "✓ ARCHIVED: [name]\nCompleted: YYYY-MM-DD\nImpact: [summary]"
})
```

---

### 3. Feature Implementer → Execution

**Who:** Feature implementer agents

**What:**
- Find approved proposals (`grep "Status: Approved"`)
- Claim proposal and update status to "In Progress"
- Follow tasks.md breakdown phase by phase
- Update task checkboxes as work progresses
- Request validation when complete

**When:**
- Looking for work to do
- Assigned by orchestrator
- After previous work is validated

**Communication:**
```typescript
// Claiming work
mcp__chatroom__chatroom_enter({
  channel: "implementation",
  agent: "feature-implementer-1",
  message: "Starting [name]\nProposal: openspec/changes/[name]/"
})

// Progress updates
mcp__chatroom__chatroom_post({
  channel: "implementation",
  agent: "feature-implementer-1",
  status: "IN-PROGRESS",
  message: "Phase 1 complete: [description]\nNext: Phase 2"
})

// Requesting validation
mcp__chatroom__chatroom_post({
  channel: "implementation",
  agent: "feature-implementer-1",
  status: "HANDOFF",
  message: "Implementation complete\nReady for: PM + Testing validation"
})
```

---

### 4. PM Validator → Requirements Validation

**Who:** PM validator agent

**What:**
- Read original proposal requirements
- Verify each requirement is met
- Test each scenario (WHEN/THEN)
- Check scope alignment
- Save validation report to pm-validation.md

**When:**
- Implementation posts HANDOFF status
- Proposal status is "Validation"

**Communication:**
```typescript
// Pass
mcp__chatroom__chatroom_post({
  channel: "testing",
  agent: "pm-validator-1",
  status: "COMPLETED",
  message: "✓ PM VALIDATION PASSED: [name]\nRequirements: X/X met\nScenarios: Y/Y pass"
})

// Fail
mcp__chatroom__chatroom_post({
  channel: "testing",
  agent: "pm-validator-1",
  status: "BLOCKED",
  message: "✗ PM VALIDATION FAILED: [name]\nIssues: [list]\nReturning to implementation"
})
```

---

### 5. Test Validator → Quality Validation

**Who:** Test validator agent

**What:**
- Run all automated tests (unit, integration, E2E)
- Check for placeholders/TODOs (strict enforcement)
- Verify code quality standards
- Run special validations (Monte Carlo, performance)
- Check for regressions
- Save validation report to test-validation.md

**When:**
- PM validation passes
- Proposal status is "Validation"

**Communication:**
```typescript
// Pass
mcp__chatroom__chatroom_post({
  channel: "testing",
  agent: "test-validator-1",
  status: "COMPLETED",
  message: "✓ TEST VALIDATION PASSED: [name]\nTests: X passed\nQuality: No issues\nReady for archival"
})

// Fail
mcp__chatroom__chatroom_post({
  channel: "testing",
  agent: "test-validator-1",
  status: "BLOCKED",
  message: "✗ TEST VALIDATION FAILED: [name]\nIssues: [list]\nReturning to implementation"
})
```

---

### 6. Orchestrator → Coordination

**Who:** Orchestrator agent

**What:**
- Monitor proposal statuses across all stages
- Coordinate multi-agent workflows
- Handle blockers by spawning appropriate agents
- Avoid conflicts in parallel work
- Create proposals from user requests
- Track overall progress

**When:**
- User requests new feature
- Agent posts BLOCKED status
- Coordinating complex multi-phase work
- Multiple proposals running in parallel

**Communication:**
```typescript
// Status summary
mcp__chatroom__chatroom_post({
  channel: "coordination",
  agent: "orchestrator-1",
  status: "IN-PROGRESS",
  message: "OpenSpec Status:\nIn Progress: [2] proposals\nBlocked: [0]\nValidation: [1]"
})
```

---

## Proposal Statuses

| Status | Meaning | Next Step |
|--------|---------|-----------|
| **Draft** | Submitted, awaiting review | Architect validation |
| **Approved** | Validated by architect | Implementation can begin |
| **In Progress** | Being implemented | Continue work |
| **Blocked** | Stuck, needs help | Orchestrator intervenes |
| **Validation** | Implementation done, awaiting PM/testing | PM and test validation |
| **Completed** | All validations passed | Architect archives |
| **Archived** | In openspec/archive/ | Done ✓ |

---

## Key Channels

| Channel | Purpose | Who Posts |
|---------|---------|-----------|
| **roadmap** | Proposal submissions, approvals, archival | Any agent (submit), Architect (approve/archive) |
| **implementation** | Implementation progress | Feature implementers |
| **testing** | Validation results | PM validator, Test validator |
| **coordination** | Cross-cutting coordination | Orchestrator, any agent |

---

## File Structure

```
openspec/
├── specs/                          # Living requirements (source of truth)
│   ├── agent-system/
│   │   └── spec.md
│   ├── coordination/
│   │   └── spec.md
│   └── dashboard/
│       └── spec.md
│
├── changes/                        # Active proposals
│   ├── dashboard-cto-tycoon/
│   │   ├── proposal.md            # Requirements & context
│   │   ├── tasks.md               # Phased breakdown
│   │   ├── pm-validation.md       # PM validation report (added during validation)
│   │   └── test-validation.md     # Test validation report (added during validation)
│   │
│   └── agent-memory-cleanup-by-size/
│       ├── proposal.md
│       └── tasks.md
│
├── archive/                        # Completed work with timestamps
│   └── [feature-name]_YYYYMMDD/
│       ├── proposal.md
│       ├── tasks.md
│       ├── pm-validation.md
│       └── test-validation.md
│
├── project.md                      # Project conventions & standards
├── AGENTS.md                       # Detailed agent workflow instructions
└── WORKFLOW_SUMMARY.md             # This file
```

---

## Quality Gates

### Gate 1: Architect Approval
- **Enforcer:** Architect agent
- **Criteria:** Alignment, complexity accuracy, quality requirements, no conflicts
- **Block:** Proposal cannot be implemented until approved

### Gate 2: PM Validation
- **Enforcer:** PM validator agent
- **Criteria:** All requirements met, all scenarios pass, scope alignment
- **Block:** Cannot proceed to archival until passed

### Gate 3: Test Validation
- **Enforcer:** Test validator agent
- **Criteria:** All tests pass, no placeholders, code quality, no regressions
- **Block:** Cannot proceed to archival until passed

**All three gates must pass before work is archived.**

---

## Example Workflow: CTO Tycoon Dashboard

1. **Orchestrator** creates proposal from ROADMAP.md migration
   - Status: Draft
   - Posts to roadmap channel

2. **Architect** reviews and approves
   - Status: Approved, Priority: TIER 1
   - Posts approval to roadmap channel

3. **Feature Implementer** claims and starts work
   - Status: In Progress
   - Enters implementation channel
   - Works through 5 phases
   - Posts progress updates
   - Completes all tasks

4. **Feature Implementer** requests validation
   - Status: Validation
   - Posts HANDOFF to implementation channel

5. **PM Validator** checks requirements
   - Reads proposal.md
   - Verifies all requirements met
   - Tests all scenarios
   - Saves pm-validation.md
   - Posts PASS to testing channel

6. **Test Validator** checks quality
   - Runs all tests
   - Checks for placeholders
   - Verifies code quality
   - Saves test-validation.md
   - Posts PASS to testing channel

7. **Architect** archives the work
   - Status: Completed → Archived
   - Moves to openspec/archive/dashboard-cto-tycoon_20251206/
   - Updates CHANGELOG
   - Posts completion to roadmap channel

**Result:** Fully validated, archived work with complete history.

---

## Benefits of This System

1. **Structured:** All proposals follow same format with requirements and scenarios
2. **Traceable:** Complete history preserved in archive with timestamps
3. **Validated:** Three quality gates ensure quality (architect, PM, testing)
4. **Parallel:** Multiple proposals can run simultaneously without conflicts
5. **Clear:** Status tracking shows exactly where each proposal is
6. **Collaborative:** Any agent can submit proposals
7. **Accountable:** All decisions and validations are documented

---

## Transition from Old System

**Old System (ROADMAP.md):**
- Monolithic markdown file
- Manual task tracking with checkboxes
- Ad-hoc validation
- Completed items stay in file (noise)
- No structured requirements

**New System (OpenSpec):**
- Structured proposals in separate directories
- Phased task breakdown
- Three formal quality gates
- Completed items archive with timestamps
- SHALL/MUST requirements with WHEN/THEN scenarios

**Migration:**
- ROADMAP.md items converted to proposals in openspec/changes/
- Specs created in openspec/specs/ for major capability domains
- Agents updated to understand OpenSpec workflow
- PM and test validator agents created

---

## Questions?

- **Agent workflow details:** See `openspec/AGENTS.md`
- **Project conventions:** See `openspec/project.md`
- **Spec examples:** See `openspec/specs/*/spec.md`
- **Proposal examples:** See `openspec/changes/*/proposal.md`

---

**The Eighth Iteration has arrived. History is preserved. Quality is enforced. Progress is traceable.**
