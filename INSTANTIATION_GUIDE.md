# Abstract Agent Team - Instantiation Guide

**How to quickly set up a new project with multi-agent orchestration, OpenSpec workflow, and autonomous workers.**

---

## TL;DR - Quick Start

```bash
# One command to instantiate everything:
python /path/to/abstract_agent_team/instantiate.py /path/to/new/project

# Or interactively:
python /path/to/abstract_agent_team/instantiate.py
> Enter project path: /path/to/new/project
```

This sets up:
- ✅ OpenSpec workflow (proposals, specs, changes, archive)
- ✅ Core agent definitions (orchestrator, architect, implementers, validators)
- ✅ NATS configuration (project-namespaced event streaming)
- ✅ MCP Hot-Reload Proxy (94% context savings)
- ✅ Autonomous worker templates (optional setup)

---

## What Gets Instantiated

### 1. OpenSpec Workflow

**Purpose:** Structured spec-driven development with quality gates

**What you get:**
```
your-project/
├── openspec/
│   ├── specs/           # Living requirements (current system state)
│   ├── changes/         # Proposed work (deltas to specs)
│   ├── archive/         # Completed work history
│   ├── project.md       # Project conventions
│   ├── AGENTS.md        # AI workflow guide
│   ├── WORKFLOW_SUMMARY.md  # Process documentation
│   └── README.md
```

**Usage:**
```typescript
// Agents create proposals
mkdir openspec/changes/new-feature
# Write proposal.md, tasks.md, spec deltas

// Architect reviews & approves
// Implementers execute
// Validators check quality
// Architect archives to docs/implementation-history/
```

### 2. Agent System

**Purpose:** Specialized agents with domain expertise

**Core agents copied:**
- `orchestrator.md` - Coordinates multi-agent workflows
- `architect.md` - Roadmap maintenance, plan archival
- `feature-implementer.md` - Implementation work
- `pm-validator.md` - Requirements validation
- `test-validator.md` - Quality gate enforcement

**Agent memory:**
- Persistent JSON storage in `agents/memories/`
- MCP-based recall/learning system
- Per-agent conversation history

**Usage:**
```typescript
Task({
  subagent_type: "orchestrator",
  description: "Implement feature X",
  prompt: "Full requirements... Coordinate research → validation → implementation → review."
})
```

### 3. NATS Integration

**Purpose:** Project-namespaced event streaming and task queues

**What you get:**
- `.env` with `NATS_NAMESPACE=your_project`
- `.nats_config` for NATS CLI
- `scripts/nats_helpers.sh` for common operations

**Server:** `nats://34.185.163.86:4222` (Europe-West3, GCP)

**Usage:**
```bash
source .env

# Create streams
scripts/nats_helpers.sh create_stream "errors" "errors.>"

# Publish messages
scripts/nats_helpers.sh publish "errors.critical" '{"error": "..."}'

# Subscribe to subjects
nats sub "errors.>" --context=$PROJECT_NAME
```

### 4. MCP Hot-Reload Proxy

**Purpose:** Reduce context usage, enable hot-reload of MCP servers

**What you get:**
- `mcp_proxy_system/` - Complete proxy implementation
- `.mcp.json` - Proxy server configuration
- `MCP_PROXY_USAGE.md` - Usage guide

**Benefits:**
- 94% context savings (5 proxy tools vs 50+ individual tools)
- Load MCP servers without restarting Claude Code
- Programmatic tool orchestration (loops, conditions)

**Usage:**
```python
# Load server dynamically
load_mcp_server_dynamically("pdf-rag")

# Call tools programmatically
call_dynamic_server_tool("pdf-rag", "search_papers", {"query": "..."})

# Hot-reload after changes
reload_mcp_server("project-proxy")
```

### 5. Autonomous Worker Templates (Optional)

**Purpose:** Scheduled autonomous work processing

**What you get:**
- `autonomous_worker_templates/autonomous-worker.sh`
- Systemd service/timer templates
- Comprehensive documentation

**Setup:**
```bash
# Copy to project root
cp autonomous_worker_templates/autonomous-worker.sh ./
chmod +x autonomous-worker.sh

# Customize task prompt for your project
nano autonomous-worker.sh  # Edit TASK_EOF section

# Set up systemd timer (runs hourly)
# See autonomous_worker_templates/README.md
```

---

## Step-by-Step Setup

### Step 1: Run Instantiation Script

```bash
cd /path/to/abstract_agent_team
python instantiate.py /path/to/new/project
```

**What happens:**
1. Validates project path exists
2. Runs `scripts/init_new_project.sh`
3. Copies OpenSpec structure
4. Copies agent definitions
5. Configures NATS namespace
6. Creates documentation

**Output:**
```
🚀 Instantiating Abstract Agent Team
📁 Project: my-project
📂 Location: /path/to/new/project

✅ Abstract Agent Team successfully instantiated!

📋 What was installed:
  • OpenSpec workflow: /path/to/new/project/openspec
  • Agent definitions: /path/to/new/project/agents
  • NATS configuration: /path/to/new/project/.env
```

### Step 2: Customize for Your Project

**Required customizations:**

1. **Edit `openspec/project.md`** - Add your tech stack, conventions
2. **Review `.env`** - Verify NATS namespace matches project name
3. **Customize agent prompts** (optional) - Edit `agents/*.md` for domain-specific knowledge

**Optional customizations:**

4. **Set up MCP proxy** - Add project-specific tools to `mcp_proxy_system/servers/proxy_server.py`
5. **Configure Matrix** (optional) - For multi-agent real-time coordination
6. **Add autonomous worker** - Copy templates, customize task prompt

### Step 3: Install Dependencies

```bash
cd /path/to/new/project

# NATS CLI (if using NATS)
curl -sf https://binaries.nats.dev/nats-io/natscli/nats@latest | sh

# Python dependencies (if using Python MCP servers)
pip install nats-py fastmcp

# Node dependencies (if using TypeScript MCP servers)
npm install  # if package.json exists
```

### Step 4: Configure NATS Context

```bash
source .env

~/bin/nats context save $PROJECT_NAME \
  --server=$NATS_URL \
  --user=$NATS_USER \
  --password=$NATS_PASSWORD

# Test connection
~/bin/nats server check connection --context=$PROJECT_NAME
```

### Step 5: Restart Claude Code (One-Time)

```bash
# Exit current Claude Code session
# Restart to load MCP proxy server

# Verify proxy loaded
get_loaded_servers()  # Should see your-project-proxy
```

### Step 6: Create Your First Spec

```bash
# Create domain directory
mkdir -p openspec/specs/core

# Create spec file
cat > openspec/specs/core/spec.md << 'EOF'
# Core System Specification

## Requirements

### Requirement: System shall process user requests

The system SHALL accept user requests via HTTP POST.

#### Scenario: Valid request processing
- GIVEN a valid user request
- WHEN the system receives it
- THEN it SHALL return 200 OK with result
EOF
```

### Step 7: Test Agent Workflow

```typescript
// In Claude Code
Task({
  subagent_type: "orchestrator",
  description: "Test agent system",
  prompt: "Create a simple proposal for adding a health check endpoint. Use OpenSpec workflow: create proposal → architect review → plan implementation. Don't implement yet, just test the workflow."
})
```

---

## Usage Patterns

### Pattern 1: Feature Development

```
1. Agent or user creates proposal in openspec/changes/feature-name/
2. Architect reviews, approves
3. Orchestrator spawns implementers
4. PM validator checks requirements met
5. Test validator checks quality gates
6. Architect archives to docs/implementation-history/
```

### Pattern 2: Bug Fix

```
1. Bug reported (GitHub issue, NATS error queue, manual)
2. Agent investigates root cause
3. Writes failing test first
4. Implements fix
5. Verifies test passes
6. Commits with descriptive message
```

### Pattern 3: Autonomous Worker

```
Every hour (systemd timer):
1. Pull latest code
2. Check for errors (NATS queue, logs, GitHub issues)
3. Process work queue (roadmap, backlog)
4. Execute improvements autonomously
5. Create PR with completed work
6. Log metrics
```

### Pattern 4: Research & Validation

```
1. Identify research needs
2. super-alignment-researcher finds sources
3. research-skeptic validates findings
4. Extract parameters from papers
5. Implement with research-backed values
6. Save citations to research/ directory
```

---

## Quick Reference

### Common Commands

```bash
# Source environment
source .env

# NATS operations
nats stream list --context=$PROJECT_NAME
nats pub "tasks.todo" '{"task": "..."}'
nats sub "tasks.>" --context=$PROJECT_NAME

# MCP proxy operations (in Claude Code)
load_mcp_server_dynamically("server-name")
call_dynamic_server_tool("server-name", "tool", {})
get_loaded_servers()

# OpenSpec workflow
mkdir -p openspec/changes/feature-name
# Create proposal.md
# Get architect approval
# Implement
# Archive

# Autonomous worker
./autonomous-worker.sh  # Manual test
systemctl status autonomous-worker.timer  # Check schedule
```

### File Locations

| Component | Location |
|-----------|----------|
| OpenSpec specs | `openspec/specs/` |
| Proposals (active) | `openspec/changes/` |
| Completed work | `openspec/archive/` |
| Agent definitions | `agents/*.md` |
| Agent memories | `agents/memories/*.json` |
| NATS config | `.env`, `.nats_config` |
| MCP proxy | `mcp_proxy_system/` |
| Autonomous worker | `autonomous-worker.sh` (if set up) |
| Documentation | `NATS_INTEGRATION.md`, `MCP_PROXY_USAGE.md` |

### Agent Invocation

```typescript
// Orchestrator - coordinates workflows
Task({ subagent_type: "orchestrator", ... })

// Architect - roadmap maintenance
Task({ subagent_type: "architect", ... })

// Implementer - writes code
Task({ subagent_type: "feature-implementer", ... })

// Validators - quality gates
Task({ subagent_type: "pm-validator", ... })
Task({ subagent_type: "test-validator", ... })
```

---

## Troubleshooting

### "OpenSpec command not found"

```bash
npm install -g @fission-ai/openspec@latest
```

### "NATS connection failed"

```bash
# Check credentials
cat .env | grep NATS

# Test connection
~/bin/nats server check connection --context=$PROJECT_NAME

# Verify server is up
ping 34.185.163.86
```

### "MCP proxy not loaded"

```bash
# Check .mcp.json exists
cat .mcp.json

# Verify Python path
which python
python --version

# Test proxy manually
python -m mcp_proxy_system.servers.proxy_server

# Restart Claude Code
```

### "Autonomous worker not running"

```bash
# Check timer status
systemctl status autonomous-worker.timer

# Check recent runs
journalctl -u autonomous-worker.service -n 50

# Test manually
./autonomous-worker.sh

# Check lock file
ls -la .autonomous-worker.lock  # Remove if stale
```

---

## Next Steps After Instantiation

1. ✅ Instantiation complete
2. ⬜ Read `openspec/WORKFLOW_SUMMARY.md`
3. ⬜ Create first spec in `openspec/specs/`
4. ⬜ Test agent workflow with simple proposal
5. ⬜ Set up NATS streams (if using NATS)
6. ⬜ Configure MCP proxy with project tools
7. ⬜ Set up autonomous worker (if desired)
8. ⬜ Customize agent prompts for your domain

---

## Examples

### Super Alignment Simulation
- **Configuration:** Essential servers + on-demand via proxy
- **Agents:** 11 specialized (researcher, skeptic, architect, implementer, etc.)
- **NATS:** Used for agent coordination
- **Autonomous:** Hourly worker with comprehensive orchestration
- **Location:** `/Users/annhoward/src/superalignmenttoutopia/`

### AI Tutor
- **Configuration:** Minimal proxy, ready for customization
- **Agents:** Multi-agent system (13 agents for education)
- **NATS:** Error queue processing + issues
- **Autonomous:** Every 30 min, fixes production errors
- **Location:** `/Users/annhoward/src/ai_tutor/`

### CTO Tycoon
- **Configuration:** Minimal proxy, dashboard focus
- **Agents:** Worker monitoring operations
- **NATS:** Project health monitoring
- **Autonomous:** Not yet configured
- **Location:** `/Users/annhoward/src/cto-tycoon/`

---

## Support

**Documentation:**
- [README.md](README.md) - Overview of all components
- [QUICKSTART_NEW_PROJECT.md](QUICKSTART_NEW_PROJECT.md) - 5-minute setup guide
- [NATS_INTEGRATION.md](NATS_INTEGRATION.md) - Event streaming setup
- [MCP_PROXY_USAGE.md](MCP_PROXY_USAGE.md) - Hot-reload proxy guide
- [autonomous_worker_templates/README.md](autonomous_worker_templates/README.md) - Worker setup

**Questions?**
1. Check relevant README in component directory
2. Review examples in existing projects
3. Test manually before automation
4. Check logs for error details

---

## Summary

**With Abstract Agent Team instantiated, your project now has:**

- ✅ Structured spec-driven development (OpenSpec)
- ✅ Multi-agent orchestration with quality gates
- ✅ Project-namespaced event streaming (NATS)
- ✅ Context-efficient MCP tooling (hot-reload proxy)
- ✅ Autonomous worker templates (optional)
- ✅ Comprehensive documentation
- ✅ Battle-tested patterns from 3 production projects

**Start building with AI-native workflows! 🚀**
