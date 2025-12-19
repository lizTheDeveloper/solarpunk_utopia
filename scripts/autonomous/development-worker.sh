#!/bin/bash
# Autonomous Development Worker
# Runs every 30 minutes to implement proposals
# Works through ALL proposals: Tier 1 → Tier 2 → Tier 3 → Tier 4
# Uses Sonnet model with dangerously-skip-permissions

set -e

PROJECT_DIR="/Users/annhoward/src/solarpunk_utopia"
LOG_DIR="$PROJECT_DIR/logs/autonomous"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/dev-worker-$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

echo "=== Autonomous Development Worker ===" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "Project: $PROJECT_DIR" | tee -a "$LOG_FILE"

cd "$PROJECT_DIR"

# Pull latest changes
echo "Pulling latest changes..." | tee -a "$LOG_FILE"
git pull origin main 2>&1 | tee -a "$LOG_FILE" || true

# Run Claude Code with Sonnet model
echo "Starting Claude Code (Sonnet)..." | tee -a "$LOG_FILE"

claude --model sonnet --dangerously-skip-permissions --print <<'TASK_EOF' 2>&1 | tee -a "$LOG_FILE"
You are an autonomous development agent working on the Solarpunk Gift Economy Mesh Network.

## Your Mission
Implement ALL proposals from openspec/changes/, working through them systematically from highest to lowest priority until everything is done.

## Priority Order (work through in this order)

### Tier 1: MUST HAVE (Workshop Blockers) - DO THESE FIRST
1. android-deployment - App runs on phones
2. web-of-trust - Vouching system
3. mass-onboarding - Event QR, bulk import
4. offline-first - Works without internet
5. local-cells - Molecules of 5-50
6. mesh-messaging - E2E encrypted DTN

### Tier 2: SHOULD HAVE (First Week Post-Workshop)
7. steward-dashboard - Tools for community leaders
8. leakage-metrics - Track economic impact
9. network-import - Bring existing communities
10. panic-features - Duress, wipe, decoy

### Tier 3: IMPORTANT (First Month)
11. sanctuary-network - Safe houses with auto-purge
12. rapid-response - 30-second alerts
13. economic-withdrawal - Coordinated boycotts
14. resilience-metrics - Network health tracking

### Tier 4: PHILOSOPHICAL (Ongoing)
15. saturnalia-protocol
16. All remaining proposals in openspec/changes/

## Process for Each Proposal

1. Check if proposal is already implemented (look for status in proposal.md)
2. If not implemented:
   a. Read the full proposal
   b. Read ARCHITECTURE_CONSTRAINTS.md to ensure compliance
   c. Implement the feature
   d. Write tests
   e. Run tests to verify
   f. Update proposal status to "Implemented"
   g. Commit: "feat: [proposal-name] - [description]"

3. Move to next proposal in priority order

## Architecture Constraints (NON-NEGOTIABLE)
- Old phones: Android 8+, 2GB RAM
- Fully distributed: No central server
- Works offline: No internet dependency
- No big tech: Zero OAuth, zero external APIs
- Seizure resistant: Any phone can be taken, network continues

## What to Do Now

1. Read openspec/WORKSHOP_SPRINT.md to see current status
2. Find the FIRST unimplemented proposal in priority order
3. Implement it completely
4. Commit your changes
5. If time remains, continue to next proposal

## Do NOT
- Skip any proposal in the priority order
- Leave code in broken state
- Create external dependencies
- Ignore the architecture constraints
- Implement partially - each proposal should be COMPLETE before moving on

Start now. Read WORKSHOP_SPRINT.md, find the first unimplemented proposal, and implement it.
TASK_EOF

echo "Completed: $(date)" | tee -a "$LOG_FILE"
echo "=== End Development Worker ===" | tee -a "$LOG_FILE"
