# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is the **Abstract Agent Team** meta-framework - a reusable template system for setting up multi-agent AI orchestration, OpenSpec workflows, and autonomous workers across projects. This is NOT an application codebase - it's a collection of patterns, templates, and agents extracted from production projects (AI Tutor, Super Alignment to Utopia, Multiverse School).

**Primary use case:** Instantiating new projects with proven multi-agent patterns via `instantiate.py` or `scripts/init_new_project.sh`.

## Architecture Overview

### Core Components

1. **OpenSpec Workflow System** (`openspec/`, `coordination_templates/`)
   - Structured spec-driven development with proposal → approval → implementation → validation → archive lifecycle
   - Replaces traditional roadmap files with structured requirements (SHALL/MUST, WHEN/THEN scenarios)
   - Three directories: `specs/` (living requirements), `changes/` (active proposals), `archive/` (completed work)

2. **Agent Definitions** (`agents/*.md`)
   - Specialized agents with domain expertise (orchestrator, architect, feature-implementer, validators, researchers, skeptics)
   - Agent memory system (`agents/memories/*.json`) for persistent context across sessions
   - Quality gates: architect approval → PM validation → test validation

3. **MCP Hot-Reload Proxy System** (`mcp_proxy_system/`)
   - 94% context savings (3 proxy tools vs 50+ individual tools)
   - Hot-reload MCP servers without restarting Claude Code
   - Programmatic tool orchestration (loops, conditionals, batch operations)
   - Dynamic installation from git repositories

4. **NATS Event Streaming** (NATS_*.md, `scripts/nats_helpers.sh`)
   - Project-namespaced event streaming for multi-agent coordination
   - Shared server at `nats://34.185.163.86:4222` (GCP Europe-West3)
   - Each project MUST use unique namespace: `{PROJECT_NAME}_{STREAM_NAME}` format

5. **Autonomous Worker Templates** (`autonomous_worker_templates/`)
   - Scheduled autonomous Claude Code execution (hourly/daily)
   - Systemd service/timer templates for VM deployment
   - Pattern: pull code → process work queues → fix bugs → create PRs → log metrics

6. **Solarpunk Node Spec** (`solarpunk_node_full_spec.md`)
   - Full specification for building DTN-based mesh networks on Android phones
   - Multi-AP islands + bridge nodes + ValueFlows economic coordination
   - Not yet implemented - this is the target system specification

## Key Commands

### Project Instantiation

```bash
# Instantiate Abstract Agent Team into a new project
python instantiate.py /path/to/new/project

# Or interactively
python instantiate.py

# What gets installed:
# - OpenSpec workflow structure
# - Agent definitions (orchestrator, architect, implementers, validators)
# - NATS configuration with project namespace
# - MCP proxy system
# - Documentation
```

### NATS Operations

```bash
# Source environment (always do this first)
source .env

# Helper functions from scripts/nats_helpers.sh
source scripts/nats_helpers.sh

# Create project-namespaced stream
nats_create_stream "errors" "errors.>" "workqueue"
# Creates: ${PROJECT_NAME}_ERRORS with subject ${project_name}.errors.>

# List streams for this project
nats_list_project_streams

# Publish to namespaced subject
nats_publish "errors.critical" '{"error": "..."}'

# Subscribe to subjects
nats_subscribe "errors.>"

# Direct NATS CLI usage
nats stream list --context=gcp-orchestrator
nats pub "${NATS_NAMESPACE,,}.errors" '{"error": "..."}' --context=gcp-orchestrator
nats sub "${NATS_NAMESPACE,,}.errors.>" --context=gcp-orchestrator
```

### MCP Proxy Operations (in Claude Code session)

```python
# Load MCP server dynamically (no restart!)
load_mcp_server_dynamically("server-name")

# Call tools programmatically
call_dynamic_server_tool("server-name", "tool_name", {"param": "value"})

# See what's loaded
get_loaded_servers()

# Install from git and load
install_and_load_mcp_server("https://github.com/user/mcp-server")

# Reload after code changes
reload_mcp_server("server-name")
```

### Autonomous Worker Setup

```bash
# Copy template to project
cp autonomous_worker_templates/autonomous-worker.sh /path/to/project/
chmod +x /path/to/project/autonomous-worker.sh

# Customize the TASK_EOF section in autonomous-worker.sh for your project

# Test manually
cd /path/to/project
./autonomous-worker.sh

# Set up systemd timer (on VM)
sudo cp autonomous_worker_templates/autonomous-worker.service.template \
        /etc/systemd/system/autonomous-worker.service
sudo cp autonomous_worker_templates/autonomous-worker.timer.template \
        /etc/systemd/system/autonomous-worker.timer

# Edit templates (replace {{VARIABLES}})
sudo nano /etc/systemd/system/autonomous-worker.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable autonomous-worker.timer
sudo systemctl start autonomous-worker.timer

# Check status
systemctl status autonomous-worker.timer
systemctl list-timers autonomous-worker.timer
journalctl -u autonomous-worker.service -n 50
```

## Agent Workflow (OpenSpec)

### For Agents

```typescript
// Orchestrator - coordinates multi-agent workflows
Task({ subagent_type: "orchestrator", description: "...", prompt: "..." })

// Architect - validates proposals, maintains roadmap, archives completed work
Task({ subagent_type: "architect", description: "...", prompt: "..." })

// Feature Implementer - executes approved proposals
Task({ subagent_type: "feature-implementer", description: "...", prompt: "..." })

// PM Validator - verifies requirements met
Task({ subagent_type: "pm-validator", description: "...", prompt: "..." })

// Test Validator - enforces quality gates (no placeholders, tests pass)
Task({ subagent_type: "test-validator", description: "...", prompt: "..." })

// Research agents
Task({ subagent_type: "super-alignment-researcher", description: "...", prompt: "..." })
Task({ subagent_type: "research-skeptic", description: "...", prompt: "..." })
Task({ subagent_type: "architecture-skeptic", description: "...", prompt: "..." })
```

### Proposal Lifecycle

1. **Create Proposal**: Any agent creates proposal in `openspec/changes/{feature-name}/`
   - Required files: `proposal.md`, `tasks.md`
   - Status: Draft

2. **Architect Review**: Architect validates proposal quality
   - Checks: clear requirements, reasonable scope, proper SHALL/MUST format
   - Status: Draft → Approved or Needs Revision

3. **Implementation**: Feature implementer executes approved proposal
   - Follows tasks.md breakdown
   - Status: Approved → In Progress

4. **Validation**: PM and Test validators check quality gates
   - PM validator: requirements met, scenarios pass
   - Test validator: tests exist and pass, no placeholders
   - Status: In Progress → Validation

5. **Archive**: Architect moves to `openspec/archive/` with timestamp
   - Updates changelog
   - Status: Validation → Completed → Archived

## Critical Patterns

### NATS Namespacing (REQUIRED)

This NATS server is shared across multiple projects. **ALWAYS use project namespacing:**

```python
# Python
import os
namespace = os.getenv('NATS_NAMESPACE', 'default')
stream_name = f"{namespace.upper()}_ERROR_REPORTS"
subject = f"{namespace.lower()}.errors.production"
```

```bash
# Shell
source .env
STREAM_NAME="${NATS_NAMESPACE^^}_ERROR_REPORTS"
SUBJECT="${NATS_NAMESPACE,,}.errors.production"
```

**Never create streams without namespace prefix!**

### Quality Gates (REQUIRED)

All proposals MUST pass:
1. Architect approval (before implementation)
2. PM validation (requirements met)
3. Test validation (tests exist, pass, no placeholders)

### Agent Memory System

Agents use persistent memory stored in `agents/memories/{agent-name}-memory.json`:
- Context preserved across sessions
- Learning from past decisions
- Consistency maintenance
- MCP-based storage and retrieval

## File Locations

| Component | Location | Purpose |
|-----------|----------|---------|
| Agent definitions | `agents/*.md` | Agent personas and workflows |
| Agent memories | `agents/memories/*.json` | Persistent agent context |
| OpenSpec specs | `openspec/specs/` | Living requirements |
| Active proposals | `openspec/changes/` | Work in progress |
| Completed work | `openspec/archive/` | Historical record |
| NATS helpers | `scripts/nats_helpers.sh` | Shell functions for NATS |
| MCP proxy | `mcp_proxy_system/` | Hot-reload proxy system |
| Autonomous worker | `autonomous_worker_templates/` | Scheduled worker templates |
| Documentation | Root `*.md` files | Integration guides |

## Environment Configuration

Required `.env` variables for projects using this framework:

```bash
# Project identification (REQUIRED)
PROJECT_NAME=your_project_name
NATS_NAMESPACE=your_project_name  # Must match PROJECT_NAME

# NATS configuration
NATS_URL=nats://34.185.163.86:4222
NATS_USER=orchestrator
NATS_PASSWORD=f3LJamuke3FMecv0JYNBhf8z
NATS_CONTEXT=gcp-orchestrator

# Matrix (optional - for agent coordination)
MATRIX_HOMESERVER=https://matrix.org
MATRIX_USER=@your-bot:matrix.org
MATRIX_PASSWORD=your-password

# Agent memory
AGENT_MEMORY_PATH=./agents/memories
```

## MCP Configuration

Add proxy to `.mcp.json` in target project:

```json
{
  "mcpServers": {
    "yourproject-proxy": {
      "command": "python",
      "args": ["-m", "mcp_proxy_system.servers.proxy_server"],
      "cwd": "/absolute/path/to/project",
      "env": {
        "PYTHONPATH": "/absolute/path/to/project",
        "DATABASE_URL": "your-database-url"
      }
    }
  }
}
```

## Common Tasks

### Migrating Patterns to New Project

1. Run instantiation script: `python instantiate.py /path/to/new/project`
2. Customize `openspec/project.md` with project conventions
3. Edit `.env` with unique NATS_NAMESPACE
4. Configure `.mcp.json` if using MCP proxy
5. Set up NATS context: `source .env && nats context save ...`
6. Restart Claude Code (one-time, to load MCP proxy)
7. Test agent workflow with simple proposal

### Adding New Agents

1. Create `agents/new-agent.md` following existing agent format
2. Define persona, expertise, responsibilities, constraints
3. Specify decision-making patterns and quality gates
4. Create memory file: `agents/memories/new-agent-memory.json`
5. Invoke via Task tool: `Task({ subagent_type: "new-agent", ... })`

### Creating Proposals

1. `mkdir -p openspec/changes/feature-name`
2. Create `proposal.md` with SHALL/MUST requirements, WHEN/THEN scenarios
3. Create `tasks.md` with implementation breakdown
4. Set Status: Draft
5. Request architect review

### Hot-Reloading MCP Servers

1. Make changes to MCP server code
2. `reload_mcp_server("server-name")` (or `load_mcp_server_dynamically` if first load)
3. Test immediately - no Claude Code restart needed
4. Iterate rapidly

## Important Constraints

### Do NOT

- Create NATS streams without project namespace prefix
- Commit `.env` files (use `.env.example` templates)
- Skip quality gates (architect → PM → test validation)
- Use this repo as application code (it's a template/pattern repository)
- Assume this repo has tests or build commands (it's documentation-heavy)

### DO

- Always use NATS namespacing: `{PROJECT_NAME}_{STREAM_NAME}`
- Follow OpenSpec workflow for all significant changes
- Use agent memory system for context preservation
- Test autonomous workers manually before scheduling
- Review all autonomous PRs before merging
- Set budget limits on autonomous workers

## Cost Considerations

### Autonomous Workers (Monthly Estimates)

- **Daily + haiku**: ~$15/month (recommended starting point)
- **Hourly + haiku**: ~$360/month (scale up after proven stable)
- **Hourly + sonnet**: ~$3,600/month (expensive, use sparingly)

### MCP Proxy

- No ongoing costs - just saves context and speeds up responses

## Source Projects

Patterns migrated from these production projects:

- **AI Tutor**: `/Users/annhoward/src/ai_tutor/` - Education platform with DevOps agent, NATS error processing
- **Super Alignment to Utopia**: `/Users/annhoward/src/super_alignment_to_utopia/` - Research simulation with quality gates
- **Multiverse School**: `/Users/annhoward/src/themultiverse.school/` - Multi-tenant platform with MCP hot-reload

Refer to these for working examples of patterns in action.

## Key Documentation

Read these files for deep dives:

- `INSTANTIATION_GUIDE.md` - Complete setup walkthrough
- `INTEGRATION.md` - Integration into existing projects
- `MIGRATED_PATTERNS.md` - Production patterns and best practices
- `NATS_INTEGRATION.md` - NATS event streaming setup
- `NATS_NAMESPACING.md` - Critical namespacing requirements
- `MCP_PROXY_USAGE.md` - Hot-reload proxy guide
- `openspec/AGENTS.md` - Detailed agent workflow
- `openspec/WORKFLOW_SUMMARY.md` - Workflow overview
- `autonomous_worker_templates/README.md` - Worker setup
- `mcp_proxy_system/README.md` - MCP proxy architecture
- `solarpunk_node_full_spec.md` - DTN mesh network specification

## Development Philosophy

This is a **meta-framework** that evolves through:

1. **Extraction**: Proven patterns from production projects
2. **Generalization**: Remove project-specific details
3. **Documentation**: Comprehensive guides and templates
4. **Reuse**: Instantiate into new projects
5. **Iteration**: Improve based on real-world usage

**Continuous improvement through abstraction.**
