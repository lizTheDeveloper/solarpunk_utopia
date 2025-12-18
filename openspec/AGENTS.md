# OpenSpec Instructions for AI Agents

This document explains how agents in the Abstract Agent Team should interact with the OpenSpec workflow.

---

## What is OpenSpec?

OpenSpec is a spec-driven development framework that replaces our previous ROADMAP.md system. Instead of a monolithic roadmap file, we now use:

- **Proposals** - Structured change requests in `openspec/changes/`
- **Specs** - Living requirements in `openspec/specs/`
- **Archive** - Completed work in `openspec/archive/`

This allows agents to submit, review, approve, and execute work in a structured, traceable way.

---

## Workflow Overview

```
┌─────────────────┐
│ Any Agent       │
│ Submits         │
│ Proposal        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Architect       │
│ Validates       │
│ Proposal        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Autonomous      │
│ Agents Pull     │
│ & Execute       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PM & Testing    │
│ Validate        │
│ Completion      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Architect       │
│ Archives        │
│ Completed Work  │
└─────────────────┘
```

---

## 1. Submitting Proposals (All Agents)

**When to submit a proposal:**
- You identify a feature that needs to be built
- You discover a gap in functionality during implementation
- You find a bug that requires significant work to fix
- You see an opportunity for improvement

**How to submit a proposal:**

### Step 1: Create the proposal directory

```bash
mkdir -p openspec/changes/[feature-name]
```

**Naming convention:** `[category]-[short-description]`

Examples:
- `agent-memory-cleanup-by-size`
- `dashboard-cto-tycoon`
- `nats-error-investigation-flow`

### Step 2: Write the proposal

Create `openspec/changes/[feature-name]/proposal.md`:

```markdown
# Proposal: [Feature Name]

**Submitted By:** [your-agent-name]
**Date:** [YYYY-MM-DD]
**Status:** Draft
**Complexity:** [1-4+ systems]

## Problem Statement

[What problem are we solving? Why does this matter?]

## Proposed Solution

[High-level approach to solving the problem]

## Requirements

### Requirement: [Name]

The system SHALL [specific requirement using SHALL/MUST language].

#### Scenario: [Scenario Name]

- WHEN [condition or trigger]
- THEN [expected outcome]

[Repeat for each requirement]

## Dependencies

- [List any dependencies on other systems or proposals]

## Risks

- [List potential risks or concerns]

## Alternatives Considered

- [Other approaches you considered and why you chose this one]
```

### Step 3: Create task breakdown

Create `openspec/changes/[feature-name]/tasks.md`:

```markdown
# Tasks: [Feature Name]

## Phase 1: [Phase Name]

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Phase 2: [Phase Name]

- [ ] Task 1
- [ ] Task 2

[Continue as needed]

## Validation

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Monte Carlo validation (if applicable)
- [ ] Code review complete
```

### Step 4: (Optional) Add design documentation

If the feature requires significant technical design, create `openspec/changes/[feature-name]/design.md`

### Step 5: Notify the Architect

Post to the `roadmap` channel:

```typescript
mcp__chatroom__chatroom_post({
  channel: "roadmap",
  agent: "your-agent-name",
  status: "QUESTION",
  message: "New proposal submitted: [feature-name]\n\n**Location:** openspec/changes/[feature-name]/\n**Complexity:** [X] systems\n\nReady for architect review."
})
```

---

## 2. Validating Proposals (Architect Agent)

**Role:** The Architect agent is responsible for reviewing and approving proposals.

**When you're notified of a new proposal:**

### Step 1: Read the proposal

```bash
cat openspec/changes/[feature-name]/proposal.md
cat openspec/changes/[feature-name]/tasks.md
```

### Step 2: Evaluate against criteria

- **Alignment:** Does this align with project goals?
- **Complexity:** Is the complexity estimate accurate?
- **Dependencies:** Are dependencies identified and manageable?
- **Quality:** Are requirements specific and testable?
- **Conflicts:** Does this conflict with other active work?

### Step 3: Provide feedback

**If approved:**

Update the proposal status:

```markdown
**Status:** Approved
**Approved By:** architect-1
**Approval Date:** [YYYY-MM-DD]
**Priority:** [TIER 1 / TIER 2 / TIER 3]
```

Post to `roadmap` channel:

```typescript
mcp__chatroom__chatroom_post({
  channel: "roadmap",
  agent: "architect-1",
  status: "COMPLETED",
  message: "✓ APPROVED: [feature-name]\n\n**Priority:** TIER 1\n**Complexity:** [X] systems\n**Ready for:** Implementation\n\nNext steps: Implementation agents can pull this proposal and begin work."
})
```

**If changes needed:**

Update proposal with comments and post:

```typescript
mcp__chatroom__chatroom_post({
  channel: "roadmap",
  agent: "architect-1",
  status: "QUESTION",
  message: "⚠ CHANGES REQUESTED: [feature-name]\n\n**Issues:**\n- [Issue 1]\n- [Issue 2]\n\nPlease update the proposal and resubmit."
})
```

---

## 3. Implementing Approved Proposals (Feature Implementer & Others)

**When looking for work:**

### Step 1: Find approved proposals

```bash
# Look for proposals with Status: Approved
grep -r "Status: Approved" openspec/changes/*/proposal.md
```

### Step 2: Claim the work

Post to `implementation` channel:

```typescript
mcp__chatroom__chatroom_enter({
  channel: "implementation",
  agent: "feature-implementer-1",
  message: "Starting implementation of [feature-name]\n\n**Proposal:** openspec/changes/[feature-name]/\n**Timeline:** Estimated [X] phases"
})
```

Update proposal status:

```markdown
**Status:** In Progress
**Assigned To:** feature-implementer-1
**Started:** [YYYY-MM-DD]
```

### Step 3: Execute tasks

Follow the task breakdown in `tasks.md`:

- Complete each task
- Run tests after each phase
- Post progress updates to `implementation` channel
- Update task checkboxes as you complete them

### Step 4: Post progress updates

```typescript
mcp__chatroom__chatroom_post({
  channel: "implementation",
  agent: "feature-implementer-1",
  status: "IN-PROGRESS",
  message: "Phase 1 complete: [description]\n\n**Completed:**\n- Task 1\n- Task 2\n\n**Next:** Phase 2 - [description]"
})
```

### Step 5: Request validation when complete

```typescript
mcp__chatroom__chatroom_post({
  channel: "implementation",
  agent: "feature-implementer-1",
  status: "HANDOFF",
  message: "Implementation complete: [feature-name]\n\n**Ready for:**\n- PM validation (requirements met)\n- Testing validation (all tests pass)\n\n**Files changed:** [list key files]"
})
```

---

## 4. Validating Completion (PM & Testing Agents)

**When an implementation is ready for validation:**

### PM Agent Validation

**Responsibilities:**
- Verify all requirements from proposal are met
- Check that scenarios pass
- Ensure deliverables match proposal scope

**Process:**

1. Read the original proposal:
   ```bash
   cat openspec/changes/[feature-name]/proposal.md
   ```

2. Verify each requirement has been addressed

3. Post validation results:

```typescript
mcp__chatroom__chatroom_post({
  channel: "testing",
  agent: "pm-agent-1",
  status: "COMPLETED",
  message: "✓ PM VALIDATION PASSED: [feature-name]\n\n**Requirements Met:**\n- Requirement 1: ✓\n- Requirement 2: ✓\n\n**Ready for:** Testing validation"
})
```

### Testing Agent Validation

**Responsibilities:**
- Run all tests
- Verify Monte Carlo validation (if applicable)
- Check code quality
- Ensure no placeholders or TODOs

**Process:**

1. Run test suite:
   ```bash
   npm test
   # or appropriate test command
   ```

2. Check for quality issues:
   ```bash
   grep -r "TODO\|FIXME\|placeholder" src/
   ```

3. Post validation results:

```typescript
mcp__chatroom__chatroom_post({
  channel: "testing",
  agent: "test-agent-1",
  status: "COMPLETED",
  message: "✓ TESTING VALIDATION PASSED: [feature-name]\n\n**Test Results:**\n- Unit tests: ✓ [X] passed\n- Integration tests: ✓ [Y] passed\n- Monte Carlo: ✓ 100 simulations passed\n\n**Ready for:** Archival"
})
```

**If issues found:**

```typescript
mcp__chatroom__chatroom_post({
  channel: "testing",
  agent: "test-agent-1",
  status: "BLOCKED",
  message: "✗ TESTING VALIDATION FAILED: [feature-name]\n\n**Issues:**\n- [Issue 1]\n- [Issue 2]\n\n**Action:** Returning to implementation"
})
```

---

## 5. Archiving Completed Work (Architect Agent)

**When both PM and Testing validation pass:**

### Step 1: Merge spec changes

If the proposal included spec deltas, merge them into the main specs:

```bash
cp openspec/changes/[feature-name]/specs/* openspec/specs/
```

### Step 2: Move to archive

```bash
mv openspec/changes/[feature-name] openspec/archive/[feature-name]_$(date +%Y%m%d)
```

### Step 3: Update CHANGELOG

Add entry to monthly changelog documenting the completion.

### Step 4: Announce completion

```typescript
mcp__chatroom__chatroom_post({
  channel: "roadmap",
  agent: "architect-1",
  status: "COMPLETED",
  message: "✓ ARCHIVED: [feature-name]\n\n**Completed:** [YYYY-MM-DD]\n**Implemented By:** [agent-names]\n**Archive Location:** openspec/archive/[feature-name]_YYYYMMDD/\n\n**Impact:** [brief description of what was achieved]"
})
```

---

## Status Tracking

Proposals move through these statuses:

1. **Draft** - Submitted, awaiting architect review
2. **Approved** - Validated by architect, ready for implementation
3. **In Progress** - Actively being implemented
4. **Validation** - Implementation complete, awaiting PM/testing validation
5. **Completed** - All validations passed, ready for archival
6. **Archived** - Merged to specs and moved to archive

**Status is tracked in the proposal.md frontmatter/header**

---

## Quick Reference

### Agent Responsibilities

| Agent | Role | Key Actions |
|-------|------|-------------|
| **Any Agent** | Submitter | Create proposals when identifying needed work |
| **Architect** | Validator | Review, approve/reject proposals; archive completed work |
| **Feature Implementer** | Executor | Pull approved proposals and implement them |
| **PM Agent** | Requirements Validator | Verify requirements from proposal are met |
| **Testing Agent** | Quality Validator | Run tests, check code quality |
| **Orchestrator** | Coordinator | Coordinate multi-agent workflows across proposals |

### Key Channels

| Channel | Purpose |
|---------|---------|
| `roadmap` | Proposal submissions, approvals, archival announcements |
| `implementation` | Implementation progress updates |
| `testing` | Test results and validation status |
| `coordination` | General workflow coordination |

### Key Locations

| Path | Contents |
|------|----------|
| `openspec/changes/` | Active proposals (Draft, Approved, In Progress) |
| `openspec/specs/` | Living requirements (source of truth) |
| `openspec/archive/` | Completed proposals with timestamps |
| `openspec/project.md` | Project conventions and standards |

---

## Example End-to-End Flow

1. **Feature Implementer** discovers during work that agent memory needs size-based cleanup
   - Creates `openspec/changes/agent-memory-cleanup-by-size/`
   - Writes proposal.md with requirements
   - Writes tasks.md with implementation breakdown
   - Posts to `roadmap` channel

2. **Architect** sees the notification
   - Reviews the proposal
   - Validates complexity estimate (1 system - memory server)
   - Updates status to "Approved"
   - Posts approval to `roadmap` channel

3. **Feature Implementer** (or another agent) sees approved proposal
   - Claims the work
   - Posts to `implementation` channel
   - Executes tasks from tasks.md
   - Posts progress updates

4. **PM Agent** validates requirements
   - Reads proposal.md
   - Verifies each requirement is met
   - Posts validation to `testing` channel

5. **Testing Agent** validates quality
   - Runs all tests
   - Checks for TODOs/placeholders
   - Posts validation to `testing` channel

6. **Architect** archives the work
   - Moves to archive with timestamp
   - Updates CHANGELOG
   - Posts completion to `roadmap` channel

---

## Best Practices

1. **Be specific in proposals** - Use SHALL/MUST language, clear scenarios
2. **Estimate complexity honestly** - Count systems touched, not hours
3. **Update status promptly** - Keep proposal status current
4. **Post to channels regularly** - Keep other agents informed
5. **Validate thoroughly** - Don't rush through validation steps
6. **Archive completely** - Ensure all context is preserved

---

## Questions?

If you're an agent and unsure about the workflow:
- Check `openspec/project.md` for project conventions
- Look at `openspec/archive/` for examples of completed proposals
- Post questions to the `coordination` channel
- Tag the `architect` agent for workflow clarification
