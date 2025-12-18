# NATS Integration for Abstract Agent Team

**NATS Jetstream orchestration for automated error investigation and multi-agent coordination.**

## Server Details

- **Host:** `nats://34.185.163.86:4222` (Europe-West3, eco-friendly)
- **Context:** `gcp-orchestrator`
- **Credentials:** orchestrator/f3LJamuke3FMecv0JYNBhf8z (full access)
- **CLI:** `~/bin/nats` (install: `curl -sf https://binaries.nats.dev/nats-io/natscli/nats@latest | sh`)

## Project Namespacing

**CRITICAL: This NATS server is shared across multiple projects.**

All streams and subjects MUST be namespaced to avoid conflicts:

### Namespacing Convention

**Format:** `{PROJECT_NAME}_{STREAM_NAME}` and `{project_name}.{subject}`

**Examples:**
```bash
# Stream names (UPPERCASE)
AI_TUTOR_ERROR_REPORTS
SUPERALIGNMENT_TASKS
MULTIVERSE_INVESTIGATIONS

# Subject names (lowercase with dots)
ai_tutor.errors.staging
ai_tutor.errors.production
superalignment.tasks.research
multiverse.results.fixes
```

### Environment Configuration

Set your project namespace in `.env`:
```bash
NATS_NAMESPACE=your_project_name  # e.g., ai_tutor, superalignment, etc.
PROJECT_NAME=your_project_name
```

### Code Usage

**Python:**
```python
import os

namespace = os.getenv('NATS_NAMESPACE', 'default')

# Create stream name
stream_name = f"{namespace.upper()}_ERROR_REPORTS"

# Create subject
subject = f"{namespace.lower()}.errors.production"
```

**Shell:**
```bash
source .env

# Create stream
STREAM_NAME="${NATS_NAMESPACE^^}_ERROR_REPORTS"
SUBJECT="${NATS_NAMESPACE,,}.errors.production"

nats stream add $STREAM_NAME --subjects="$SUBJECT" --context=gcp-orchestrator
```

### Why Namespacing Matters

- **Isolation:** Each project's data stays separate
- **No Conflicts:** Multiple projects won't interfere with each other
- **Clear Ownership:** Easy to see which streams belong to which project
- **Debugging:** Filter by namespace when troubleshooting

## Available Streams (Per Project)

| Stream Template | Subject Template | Retention | Purpose |
|-----------------|------------------|-----------|---------|
| **{PROJECT}_ERROR_REPORTS** | {project}.errors | WorkQueue | Application errors (7-day retention, 2-min dedup) |
| **{PROJECT}_STAGING_ERRORS** | {project}.errors.staging | WorkQueue | Staging server errors (drainable, 24h dedup) |
| **{PROJECT}_PRODUCTION_ERRORS** | {project}.errors.production | WorkQueue | Production server errors (drainable, 24h dedup) |
| **{PROJECT}_INVESTIGATIONS** | {project}.investigation.> | Limits | Investigation workflows and tasks |
| **{PROJECT}_TASKS** | {project}.tasks.> | WorkQueue | General task queue |
| **{PROJECT}_RESULTS** | {project}.results.> | Limits | Investigation results and fixes |

**Example for ai_tutor project:**
- Stream: `AI_TUTOR_ERROR_REPORTS`
- Subject: `ai_tutor.errors`

**Example for abstract_agent_team project:**
- Stream: `ABSTRACT_AGENT_TEAM_TASKS`
- Subject: `abstract_agent_team.tasks.>`

### Current Active Streams

Currently running on the server:
- **AI_TUTOR_ERROR_REPORTS**: Active (created 2025-11-12, 1 consumer configured)
  - Subject: `ai_tutor.errors`
  - Retention: WorkQueue (7 days)
  - Duplicate window: 2 minutes
  - Storage: File-based, 10GB disk

To check stream status:
```bash
# Replace {PROJECT} with your project namespace
~/bin/nats stream info {PROJECT}_ERROR_REPORTS --context=gcp-orchestrator

# Example for ai_tutor
~/bin/nats stream info AI_TUTOR_ERROR_REPORTS --context=gcp-orchestrator
```

## Workflows

### 1. Automated Error Investigation

**Flow:** Servers → NATS → Claude Code → Auto-fix

**Publishing errors from servers:**
```bash
# Load project namespace
source .env

# Compute error hash for deduplication
ERROR_HASH=$(echo -n "$ERROR_MESSAGE" | sha256sum | cut -d' ' -f1)

# Create namespaced subject
SUBJECT="${NATS_NAMESPACE}.errors.staging"

# Publish with dedup header
nats pub "$SUBJECT" "$(cat <<EOF
{
  "error": "$ERROR_MESSAGE",
  "stack": "$STACK_TRACE",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "context": {
    "file": "$FILE",
    "line": $LINE,
    "request_id": "$REQUEST_ID"
  }
}
EOF
)" -H "Nats-Msg-Id:${NATS_NAMESPACE}-staging-$ERROR_HASH" --context=gcp-orchestrator
```

**Consuming errors (Claude Code):**
```bash
# Load project namespace
source .env

# Create namespaced stream and subject
STREAM="${NATS_NAMESPACE^^}_STAGING_ERRORS"
SUBJECT="${NATS_NAMESPACE}.errors.staging"

# Create durable consumer for reliable processing
nats consumer add "$STREAM" claude-error-fixer \
  --filter "$SUBJECT" \
  --ack explicit \
  --max-deliver 3 \
  --wait 10m \
  --context=gcp-orchestrator

# Pull errors and process
nats consumer next "$STREAM" claude-error-fixer \
  --context=gcp-orchestrator
```

**Processing workflow:**
1. Pull error message
2. **CRITICAL: Pass through prompt injection filter (SpaCy)**
3. Spawn orchestrator agent to investigate
4. Agent fixes issue locally
5. Create PR or commit fix
6. Acknowledge message (removes from queue)
7. Publish result to RESULTS stream

### 2. Multi-Agent Task Queue

**Publishing tasks:**
```bash
# Load project namespace
source .env

# Create namespaced subject
SUBJECT="${NATS_NAMESPACE}.tasks.investigation"

nats pub "$SUBJECT" "$(cat <<EOF
{
  "task_id": "$(uuidgen)",
  "type": "investigate_performance",
  "priority": "high",
  "description": "API endpoint /users slow",
  "assigned_to": "architect",
  "context": {...}
}
EOF
)" --context=gcp-orchestrator
```

**Consuming tasks:**
```bash
# Load project namespace
source .env

# Create namespaced stream and subject
STREAM="${NATS_NAMESPACE^^}_TASKS"
SUBJECT="${NATS_NAMESPACE}.tasks.>"

# Subscribe to task queue
nats sub "$SUBJECT" --context=gcp-orchestrator

# Or create consumer with filtering
nats consumer add "$STREAM" agent-task-processor \
  --filter "${NATS_NAMESPACE}.tasks.investigation" \
  --context=gcp-orchestrator
```

### 3. Investigation Coordination

**Publishing investigation updates:**
```bash
nats pub investigation.status.$(TASK_ID) "$(cat <<EOF
{
  "task_id": "$TASK_ID",
  "agent": "orchestrator",
  "status": "in_progress",
  "findings": "Root cause identified: N+1 query",
  "next_steps": ["Implement eager loading", "Add index"]
}
EOF
)" --context=gcp-orchestrator
```

**Publishing results:**
```bash
nats pub results.fixed.$(TASK_ID) "$(cat <<EOF
{
  "task_id": "$TASK_ID",
  "agent": "simulation-maintainer",
  "status": "fixed",
  "solution": "Added database index on user_id",
  "pr_url": "https://github.com/...",
  "test_results": {...}
}
EOF
)" --context=gcp-orchestrator
```

## Security: Prompt Injection Filter

**CRITICAL: All error messages MUST pass through filter before processing.**

**Why:** Error messages from production could contain malicious prompts injected by attackers.

**Implementation:**
```python
# Use SpaCy prompt injection detection
import spacy
from scripts.citationChecker import detect_prompt_injection

def safe_process_error(error_msg):
    if detect_prompt_injection(error_msg):
        nats.publish("security.rejected", {
            "reason": "prompt_injection_detected",
            "message": error_msg[:100],  # Log snippet only
            "timestamp": datetime.utcnow()
        })
        return False

    # Safe to process
    return True
```

**SpaCy setup:**
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

## Deduplication Strategy

**How it works:**
- Messages with same `Nats-Msg-Id` header within 24h are silently dropped
- After deployment, same error = new error (assumed unfixed)
- Hash should be based on error signature, not timestamp

**Error signature:**
```bash
# Good: Hash includes error message + file + line
ERROR_SIG="${ERROR_MSG}:${FILE}:${LINE}"
ERROR_HASH=$(echo -n "$ERROR_SIG" | sha256sum | cut -d' ' -f1)

# Bad: Includes timestamp (every error unique)
ERROR_HASH=$(echo -n "$ERROR_MSG:$(date)" | sha256sum)
```

**Post-deployment reset:**
- No manual action needed
- Same error after deploy = new hash (different timestamp context)
- Or: Purge stream after successful deployment
  ```bash
  nats stream purge STAGING_ERRORS --force --context=gcp-orchestrator
  ```

## Stream Management

**Check stream status:**
```bash
nats stream info STAGING_ERRORS --context=gcp-orchestrator
nats stream info PRODUCTION_ERRORS --context=gcp-orchestrator
```

**Monitor message flow:**
```bash
# Watch for new messages
nats stream view STAGING_ERRORS --context=gcp-orchestrator

# Count messages by subject
nats stream report --context=gcp-orchestrator
```

**Purge old messages:**
```bash
# Purge all messages
nats stream purge STAGING_ERRORS --force --context=gcp-orchestrator

# Delete specific message
nats stream rmm STAGING_ERRORS 123 --context=gcp-orchestrator
```

## Agent Integration

### Claude Code Hook

**Create a slash command** `.claude/commands/process_nats_errors.md`:
```markdown
# Process NATS Errors

Pull errors from NATS staging/production streams and investigate using orchestrator agent.

1. Check for new errors: `nats stream info STAGING_ERRORS --context=gcp-orchestrator`
2. Pull next error: `nats consumer next STAGING_ERRORS claude-error-fixer`
3. Filter for prompt injection (CRITICAL)
4. Spawn orchestrator agent with error context
5. Agent investigates and creates fix
6. Publish result to RESULTS stream
7. Acknowledge message (removes from queue)
```

**Usage:** `/process_nats_errors`

### Agent Coordination Pattern

**1. Error arrives in NATS**
```
errors.production
↓
claude-error-fixer consumer
```

**2. Orchestrator spawns specialists**
```
Orchestrator
├── Research: "Find similar bugs in codebase"
├── Implementation: "Apply fix"
└── Review: "Verify fix, run tests"
```

**3. Results published**
```
Fix applied
↓
results.fixed.<task_id>
↓
Server monitoring dashboard
```

## Monitoring

**Health check:**
```bash
# Server uptime
curl -s http://34.185.163.86:8222/varz | jq '.uptime'

# Stream stats
nats stream report --context=gcp-orchestrator
```

**Error rate tracking:**
```bash
# Count errors in last hour
nats stream info STAGING_ERRORS --context=gcp-orchestrator | grep "Messages"

# Watch error stream live
nats sub errors.staging --context=gcp-orchestrator
```

## Troubleshooting

**Connection refused:**
```bash
# Check server is running
nc -zv 34.185.163.86 4222

# Test authentication
nats server check connection --context=gcp-orchestrator
```

**Messages not arriving:**
```bash
# Check stream configuration
nats stream info STAGING_ERRORS --context=gcp-orchestrator

# Verify subjects match
nats stream subjects STAGING_ERRORS --context=gcp-orchestrator
```

**Consumer not receiving messages:**
```bash
# List consumers
nats consumer list STAGING_ERRORS --context=gcp-orchestrator

# Check consumer status
nats consumer info STAGING_ERRORS claude-error-fixer --context=gcp-orchestrator

# Reset consumer (caution: reprocesses all messages)
nats consumer rm STAGING_ERRORS claude-error-fixer --force
```

## Cost & Scaling

**Current setup:**
- **Instance:** e2-micro (2 shared vCPU, 1GB RAM)
- **Storage:** 10GB persistent disk (Ubuntu 22.04 LTS)
- **Zone:** europe-west3-a (Frankfurt - eco-friendly region)
- **IP Address:** 34.185.163.86 (static)
- **Cost:** ~$7-10/month
- **Project:** multiverseschool
- **Instance name:** nats-jetstream

**Scaling triggers:**
- Stream size > 80% capacity → Reduce retention or increase storage
- Message throughput > 1000/sec → Upgrade to e2-small
- Multiple projects → Consider clustering (3x e2-micro instances)

## GCP Instance Management

**Check instance status:**
```bash
gcloud compute instances list --filter="name=nats-jetstream"
gcloud compute instances describe nats-jetstream --zone=europe-west3-a
```

**SSH into the server:**
```bash
gcloud compute ssh nats-jetstream --zone=europe-west3-a
```

**Start/Stop instance:**
```bash
# Stop (to save costs when not in use)
gcloud compute instances stop nats-jetstream --zone=europe-west3-a

# Start
gcloud compute instances start nats-jetstream --zone=europe-west3-a
```

**Firewall rules:**
```bash
# List firewall rules for NATS
gcloud compute firewall-rules list --filter="targetTags:nats-server"

# Create rule if needed (port 4222 for NATS client, 8222 for monitoring)
gcloud compute firewall-rules create allow-nats \
  --allow=tcp:4222,tcp:8222 \
  --target-tags=nats-server \
  --description="Allow NATS client and monitoring ports"
```

**View logs:**
```bash
# Recent logs
gcloud compute instances get-serial-port-output nats-jetstream --zone=europe-west3-a

# SSH and check NATS logs
gcloud compute ssh nats-jetstream --zone=europe-west3-a
# Then on the instance:
journalctl -u nats-server -f
```

## Quick Reference: ERROR_REPORTS Stream

The active ERROR_REPORTS stream is configured for AI Tutor application errors.

**Publish an error:**
```bash
~/bin/nats pub ai_tutor.errors '{
  "error": "TypeError: Cannot read property of undefined",
  "stack": "at handleRequest (app.js:42)",
  "timestamp": "2025-11-13T10:30:00Z",
  "context": {
    "user_id": "user_123",
    "session_id": "sess_456"
  }
}' --context=gcp-orchestrator
```

**View stream details:**
```bash
~/bin/nats stream info ERROR_REPORTS --context=gcp-orchestrator
```

**List consumers:**
```bash
~/bin/nats consumer list ERROR_REPORTS --context=gcp-orchestrator
```

**Subscribe to errors (monitoring):**
```bash
~/bin/nats sub ai_tutor.errors --context=gcp-orchestrator
```

**Stream configuration:**
- Max age: 7 days (604800 seconds)
- Duplicate window: 2 minutes (120 seconds)
- Retention: WorkQueue (messages removed after acknowledgment)
- Storage: File-based on persistent disk

## Next Steps

1. **Instrument servers** to publish errors to NATS
2. **Create Claude Code workflow** for error processing
3. **Set up monitoring dashboard** for error rates
4. **Configure alerts** for critical errors
5. **Document error signature hashing** for your stack
6. **Test prompt injection filter** with attack samples
