# NATS Namespacing Guide

**Why:** The NATS server at `nats://34.185.163.86:4222` is shared across multiple projects. Namespacing prevents conflicts and keeps data isolated.

---

## Quick Reference

### Your Project
```bash
PROJECT: abstract_agent_team
NAMESPACE: abstract_agent_team
```

### Naming Convention

| Type | Format | Example |
|------|--------|---------|
| **Stream** | `{PROJECT}_STREAM_NAME` | `ABSTRACT_AGENT_TEAM_ERROR_REPORTS` |
| **Subject** | `{project}.subject.name` | `abstract_agent_team.errors.staging` |

---

## Configuration

Add to your `.env`:
```bash
NATS_NAMESPACE=abstract_agent_team
PROJECT_NAME=abstract_agent_team
```

For other projects, use their project name:
```bash
# For ai_tutor project
NATS_NAMESPACE=ai_tutor

# For superalignment project
NATS_NAMESPACE=superalignment
```

---

## Using Namespaces

### Method 1: Helper Script (Recommended)

```bash
# Source the helper functions
source scripts/nats_helpers.sh

# Create a namespaced stream
nats_create_stream "error_reports" "errors.>" "workqueue"
# Creates: ABSTRACT_AGENT_TEAM_ERROR_REPORTS with subject abstract_agent_team.errors.>

# List all streams for your project
nats_list_project_streams

# Subscribe to namespaced subject
nats_subscribe "errors.staging"
# Subscribes to: abstract_agent_team.errors.staging

# Publish to namespaced subject
nats_publish "tasks.test" '{"task": "test"}'
# Publishes to: abstract_agent_team.tasks.test

# Get stream info
nats_stream_info "error_reports"
# Gets info for: ABSTRACT_AGENT_TEAM_ERROR_REPORTS
```

### Method 2: Manual (Shell)

```bash
# Load environment
source .env

# Create namespaced stream name
STREAM="${NATS_NAMESPACE^^}_ERROR_REPORTS"

# Create namespaced subject
SUBJECT="${NATS_NAMESPACE}.errors.>"

# Use in NATS commands
~/bin/nats stream add "$STREAM" \
  --subjects="$SUBJECT" \
  --context=gcp-orchestrator
```

### Method 3: Python

```python
import os

# Load from environment
namespace = os.getenv('NATS_NAMESPACE', 'default')

# Create stream name
stream_name = f"{namespace.upper()}_ERROR_REPORTS"

# Create subject
subject = f"{namespace.lower()}.errors.staging"

# Use with nats.py
import nats

async def publish_error(error_data):
    nc = await nats.connect(
        servers=[os.getenv('NATS_URL')],
        user=os.getenv('NATS_USER'),
        password=os.getenv('NATS_PASSWORD')
    )

    subject = f"{namespace.lower()}.errors.production"
    await nc.publish(subject, json.dumps(error_data).encode())
    await nc.close()
```

---

## Stream Templates

### Standard Streams for Each Project

| Template | Subject Pattern | Purpose |
|----------|----------------|---------|
| `{PROJECT}_ERROR_REPORTS` | `{project}.errors` | Application errors |
| `{PROJECT}_STAGING_ERRORS` | `{project}.errors.staging` | Staging environment |
| `{PROJECT}_PRODUCTION_ERRORS` | `{project}.errors.production` | Production environment |
| `{PROJECT}_TASKS` | `{project}.tasks.>` | Task queue |
| `{PROJECT}_INVESTIGATIONS` | `{project}.investigation.>` | Investigation workflows |
| `{PROJECT}_RESULTS` | `{project}.results.>` | Results and fixes |

### Create All Standard Streams

```bash
source scripts/nats_helpers.sh

# Error reporting
nats_create_stream "error_reports" "errors" "workqueue"
nats_create_stream "staging_errors" "errors.staging" "workqueue"
nats_create_stream "production_errors" "errors.production" "workqueue"

# Task management
nats_create_stream "tasks" "tasks.>" "workqueue"
nats_create_stream "investigations" "investigation.>" "limits"
nats_create_stream "results" "results.>" "limits"
```

---

## Current Projects on Server

| Project | Namespace | Owner | Active Streams |
|---------|-----------|-------|----------------|
| AI Tutor | `ai_tutor` | Ann | AI_TUTOR_ERROR_REPORTS |
| Abstract Agent Team | `abstract_agent_team` | Ann | TBD |
| Super Alignment | `superalignment` | Ann | TBD |
| Multiverse School | `multiverse` | Ann | TBD |

---

## Verification

### Check Your Streams

```bash
# List all streams (all projects)
~/bin/nats stream list --context=gcp-orchestrator

# List only your project's streams
source scripts/nats_helpers.sh
nats_list_project_streams
```

### Verify Subject Isolation

```bash
# Subscribe to your project's errors
nats_subscribe "errors.>"

# This will ONLY receive messages for your project
# Other projects' errors won't appear
```

---

## Migration from Non-Namespaced

If you have existing streams without namespacing:

### 1. Check Existing Streams
```bash
~/bin/nats stream list --context=gcp-orchestrator
```

### 2. Create Namespaced Versions
```bash
source scripts/nats_helpers.sh
nats_create_stream "error_reports" "errors.>" "workqueue"
```

### 3. Update Publishers
Change from:
```bash
nats pub errors.staging "..."
```

To:
```bash
source .env
nats pub "${NATS_NAMESPACE}.errors.staging" "..."
```

Or use helper:
```bash
nats_publish "errors.staging" "..."
```

### 4. Update Consumers
Change from:
```bash
nats consumer add ERROR_REPORTS consumer1 --filter errors.staging
```

To:
```bash
STREAM="${NATS_NAMESPACE^^}_ERROR_REPORTS"
SUBJECT="${NATS_NAMESPACE}.errors.staging"
nats consumer add "$STREAM" consumer1 --filter "$SUBJECT"
```

### 5. Verify Migration
```bash
# Check new stream has messages
nats_stream_info "error_reports"

# Delete old stream (after verification)
~/bin/nats stream rm OLD_STREAM_NAME --force --context=gcp-orchestrator
```

---

## Best Practices

1. **Always use helpers:** `source scripts/nats_helpers.sh`
2. **Set namespace in .env:** Don't hardcode project names
3. **Document your streams:** Update this file with your active streams
4. **Test isolation:** Verify other projects can't see your messages
5. **Clean up:** Delete old non-namespaced streams after migration

---

## Troubleshooting

### "Stream not found"
- Check you're using the correct namespace
- Verify stream exists: `nats_list_project_streams`
- Create stream if needed: `nats_create_stream "stream_name" "subject.>"`

### "No messages arriving"
- Verify publisher is using correct namespaced subject
- Check stream subject pattern includes your subject
- Test with: `nats_subscribe "errors.>"`

### "Wrong project receiving messages"
- Check namespace is set correctly in .env
- Verify subject matches namespace: `abstract_agent_team.errors.staging`
- Each project should have different namespace

---

## Questions?

- **Full NATS guide:** `NATS_INTEGRATION.md`
- **Credentials:** `NATS_CREDENTIALS.md`
- **Helper functions:** `scripts/nats_helpers.sh`
