#!/bin/bash
# Gap Analysis Worker
# Runs every 6 hours to find things that look implemented but aren't functional
# Uses Opus model for deep analysis

set -e

PROJECT_DIR="/Users/annhoward/src/solarpunk_utopia"
LOG_DIR="$PROJECT_DIR/logs/autonomous"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/gap-analysis-$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

echo "=== Gap Analysis Worker (Opus) ===" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "Project: $PROJECT_DIR" | tee -a "$LOG_FILE"

cd "$PROJECT_DIR"

# Pull latest changes
echo "Pulling latest changes..." | tee -a "$LOG_FILE"
git pull origin main 2>&1 | tee -a "$LOG_FILE" || true

# Run Claude Code with Opus model
echo "Starting Claude Code (Opus) for gap analysis..." | tee -a "$LOG_FILE"

claude --model opus --dangerously-skip-permissions --print <<'TASK_EOF' 2>&1 | tee -a "$LOG_FILE"
You are an autonomous gap analysis agent for the Solarpunk Gift Economy Mesh Network.

## Your Mission
Find code that APPEARS to be implemented but ISN'T ACTUALLY FUNCTIONAL.

## What to Look For

### 1. Mock Data Still in Place
- Functions that return hardcoded data instead of querying real sources
- "TODO" comments indicating incomplete implementation
- Placeholder values that were never replaced

### 2. Dead Code Paths
- API endpoints that exist but are never called
- UI buttons that don't do anything
- Features advertised but not connected

### 3. Broken Integration Points
- Frontend calling backend endpoints that don't exist
- Backend expecting data formats the frontend doesn't send
- Services that should talk to each other but don't

### 4. Missing Error Handling
- Try/except that silently swallows errors
- Optimistic code that assumes everything works
- No validation on user input

### 5. Incomplete Proposals
- Proposals marked "Implemented" but missing pieces
- Tests that don't actually test the claimed functionality
- Documentation that doesn't match reality

## Process

1. Read openspec/VISION_REALITY_DELTA.md for known gaps
2. Read openspec/WORKSHOP_SPRINT.md for what should be working
3. For each "Implemented" or "Complete" item:
   a. Find the actual code
   b. Trace the code path end-to-end
   c. Check if it actually works
   d. If not, document the gap

4. Search for patterns:
   - `return \[\]` or `return {}` (empty returns)
   - `# TODO` or `# FIXME`
   - `raise NotImplementedError`
   - `pass` in function bodies
   - Mock/hardcoded data patterns

5. Update VISION_REALITY_DELTA.md with new gaps found
6. Create issues or proposals for critical gaps
7. Commit your findings

## Output Format

For each gap found, document:
- GAP-XX: [Title]
- Location: file:line
- Claimed: What it's supposed to do
- Reality: What it actually does
- Severity: CRITICAL/HIGH/MEDIUM/LOW
- Fix: What needs to change

Start by reading the gap document and the proposals marked as complete, then verify each one.
TASK_EOF

echo "Completed: $(date)" | tee -a "$LOG_FILE"
echo "=== End Gap Analysis Worker ===" | tee -a "$LOG_FILE"
