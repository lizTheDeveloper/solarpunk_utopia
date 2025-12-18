# NATS Credentials Quick Reference

**Server:** nats-jetstream VM in GCP
**Zone:** europe-west3-a
**IP:** 34.185.163.86

---

## Credentials

```bash
NATS_URL=nats://34.185.163.86:4222
NATS_USER=orchestrator
NATS_PASSWORD=f3LJamuke3FMecv0JYNBhf8z
NATS_CONTEXT=gcp-orchestrator
```

## Configuration Files

Credentials are stored in:
- **`.env`** - Main environment file (gitignored)
- **`.nats_config`** - Shell-sourceable config (gitignored)
- **`.env.example`** - Template for new setups

## Usage

### Python Scripts

Python scripts like `work_claim_service.py` and `agent_coordinator.py` automatically load from `.env` or `.nats_config`:

```python
import os

# Load from environment
nats_url = os.getenv('NATS_URL', 'nats://localhost:4222')
nats_user = os.getenv('NATS_USER')
nats_password = os.getenv('NATS_PASSWORD')
```

### NATS CLI

If you have the NATS CLI installed (`~/bin/nats`), create a context:

```bash
# Create context
~/bin/nats context save gcp-orchestrator \
  --server=nats://34.185.163.86:4222 \
  --user=orchestrator \
  --password=f3LJamuke3FMecv0JYNBhf8z

# Use context
~/bin/nats stream list --context=gcp-orchestrator
```

### Shell Scripts

Source the config file:

```bash
source .nats_config
echo "Connected to $NATS_URL as $NATS_USER"
```

## Project Namespacing

**CRITICAL: All streams and subjects are namespaced per project.**

### Format
- **Streams:** `{PROJECT}_STREAM_NAME` (uppercase)
- **Subjects:** `{project}.subject.name` (lowercase)

### Your Project
```bash
NATS_NAMESPACE=abstract_agent_team
```

### Example Streams for This Project

| Stream | Subject | Purpose |
|--------|---------|---------|
| **ABSTRACT_AGENT_TEAM_ERROR_REPORTS** | abstract_agent_team.errors | Application errors |
| **ABSTRACT_AGENT_TEAM_STAGING_ERRORS** | abstract_agent_team.errors.staging | Staging errors |
| **ABSTRACT_AGENT_TEAM_PRODUCTION_ERRORS** | abstract_agent_team.errors.production | Production errors |
| **ABSTRACT_AGENT_TEAM_INVESTIGATIONS** | abstract_agent_team.investigation.> | Investigation workflows |
| **ABSTRACT_AGENT_TEAM_TASKS** | abstract_agent_team.tasks.> | Task queue |
| **ABSTRACT_AGENT_TEAM_RESULTS** | abstract_agent_team.results.> | Results |

### Other Active Projects

| Project | Namespace | Example Stream |
|---------|-----------|----------------|
| AI Tutor | `ai_tutor` | AI_TUTOR_ERROR_REPORTS |
| Super Alignment | `superalignment` | SUPERALIGNMENT_TASKS |
| Multiverse School | `multiverse` | MULTIVERSE_INVESTIGATIONS |

## Testing Connection

```bash
# Test with NATS CLI
~/bin/nats server check connection --context=gcp-orchestrator

# Test with netcat
nc -zv 34.185.163.86 4222

# Test with Python
python3 -c "
import asyncio
import nats

async def test():
    nc = await nats.connect(
        servers=['nats://34.185.163.86:4222'],
        user='orchestrator',
        password='f3LJamuke3FMecv0JYNBhf8z'
    )
    print('✅ Connected to NATS!')
    await nc.close()

asyncio.run(test())
"
```

## GCP VM Access

```bash
# SSH into the NATS server
gcloud compute ssh nats-jetstream --zone=europe-west3-a

# Start/Stop instance
gcloud compute instances start nats-jetstream --zone=europe-west3-a
gcloud compute instances stop nats-jetstream --zone=europe-west3-a

# View logs
gcloud compute ssh nats-jetstream --zone=europe-west3-a
journalctl -u nats-server -f
```

## Security Notes

- ✅ Credentials are gitignored (see `.gitignore`)
- ✅ Example file provided (`.env.example`)
- ⚠️ Never commit `.env` or `.nats_config` to git
- ⚠️ Rotate credentials if accidentally exposed

## Related Documentation

- **Full integration guide:** `NATS_INTEGRATION.md`
- **OpenSpec coordination:** `openspec/specs/coordination/spec.md`
- **Project README:** `README.md`
