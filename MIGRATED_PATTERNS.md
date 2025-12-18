# Migrated Patterns from Other Projects

This document tracks patterns, agents, and systems that have been migrated from other projects into the Abstract Agent Team.

## Overview

The Abstract Agent Team serves as a **meta-framework** for multi-agent systems. We extract proven patterns from production projects and generalize them for reuse.

**Source projects:**
- **AI Tutor** - Production education platform
- **Super Alignment to Utopia** - Research simulation project
- **Multiverse School** - Multi-tenant education platform

## Migrated Components

### 1. DevOps Agent (from AI Tutor)

**Source:** `/Users/annhoward/src/ai_tutor/agents/devops.md`
**Destination:** `agents/devops.md`

**What it does:**
- VM management and configuration (GCP)
- Deployment pipelines and automation
- Systemd service management
- NATS queue monitoring
- Incident response and recovery
- Log analysis and alerting

**When to use:**
- Projects with cloud infrastructure (GCP, AWS, Azure)
- Autonomous workers on VMs
- Production deployments requiring monitoring
- NATS-based error reporting systems

**Key responsibilities:**
- Check staging/production health
- Restart failed services
- Monitor NATS queues
- Send Matrix/email alerts
- Automated recovery workflows

### 2. Autonomous Worker Pattern (from AI Tutor)

**Source:** `/Users/annhoward/src/ai_tutor/sre/scripts/run_devops_agent.sh`
**Destination:** `autonomous_worker_templates/`

**Components:**
- `autonomous-worker.sh.template` - Generalized bash script template
- `autonomous-worker.service.template` - Systemd service file
- `autonomous-worker.timer.template` - Systemd timer configuration
- `README.md` - Comprehensive setup guide

**What it does:**
- Runs Claude Code autonomously on a schedule (hourly, daily, etc.)
- Pulls latest code from git
- Executes agent tasks (monitoring, testing, fixing bugs)
- Creates PRs with completed work
- Logs all activity with metrics

**When to use:**
- Continuous monitoring and recovery
- Scheduled maintenance tasks
- Autonomous bug fixing
- Queue draining (NATS, GitHub issues)
- Daily/weekly reporting

**Real-world usage:**
- **AI Tutor:** DevOps agent runs hourly, checks staging health, fixes frontend/backend issues, sends Matrix alerts
- **Super Alignment:** Orchestrator runs hourly, processes roadmap, coordinates multi-agent workflows

### 3. MCP Hot-Reload Proxy System (from Multiverse School)

**Source:** `/Users/annhoward/src/themultiverse.school/multiverse_mcp/`
**Destination:** `mcp_proxy_system/`

**Components:**
- `servers/proxy_server.py` (v1)
- `servers/proxy_server_v2.py` (improved)
- `servers/proxy_server_v3.py` (recommended)
- `utils/mcp_proxy.py` - Python client library
- `utils/dynamic_server_loader.py` - Subprocess manager
- `utils/mcp_installer.py` - Git-based installer
- `README.md` - Full documentation

**What it does:**
- **94% context savings** - Load 3 proxy tools instead of 50+ individual tools
- **Hot-reload** - Add/remove MCP servers without restarting Claude Code
- **Programmatic orchestration** - Call tools in loops, conditionals, workflows
- **Dynamic installation** - Install from git repos instantly

**When to use:**
- Projects with multiple MCP servers (3+)
- Development workflows requiring hot-reload
- Programmatic tool orchestration (batch operations)
- Large tool catalogs that exceed context limits

**Real-world usage:**
- **Multiverse School:** Registrar MCP (student management), Matrix MCP (messaging), Dashboard MCP (analytics) all hot-loaded dynamically

### 4. Research Validation Agents (from Super Alignment to Utopia)

**Already Present - Verified:** ✅

**Agents:**
- `agents/super-alignment-researcher.md` - Deep research specialist
- `agents/research-skeptic.md` (Cynthia) - Research validation and skepticism
- `agents/architecture-skeptic.md` (Sylvia) - Architecture review and critique

**What they do:**
- **Researcher:** Finds authoritative sources, synthesizes findings, provides evidence-based recommendations
- **Cynthia (Research Skeptic):** Validates sources, challenges assumptions, ensures epistemic rigor
- **Sylvia (Architecture Skeptic):** Reviews architecture decisions, identifies flaws, enforces best practices

**When to use:**
- Research-heavy projects
- AI alignment and safety research
- Technical decision validation
- Quality gates for complex implementations

**Pattern:**
1. Researcher gathers information and proposes approach
2. Cynthia validates sources and challenges assumptions
3. Researcher refines based on feedback
4. Sylvia reviews architecture and implementation
5. Only proceeds if both skeptics approve (Quality Gates)

### 5. Agent Memory System (from Super Alignment to Utopia)

**Already Present - Verified:** ✅

**Location:** `agents/memories/`

**Components:**
- `README.md` - Memory system documentation
- `cynthia-memory.json` - Research skeptic memory
- `sylvia-memory.json` - Architecture skeptic memory
- Individual memory files for each agent

**What it does:**
- Persistent memory across Claude Code sessions
- MCP-based storage and retrieval
- Context preservation for long-running projects
- Learning and adaptation over time

**When to use:**
- Multi-session projects
- Agents that need to recall past decisions
- Learning from mistakes
- Maintaining consistency across sessions

## Integration Patterns

### Pattern 1: Autonomous DevOps Monitoring

**Use case:** Monitor production/staging, fix issues autonomously

**Setup:**
1. Copy `autonomous_worker_templates/` to your project
2. Customize `autonomous-worker.sh.template` for your infrastructure
3. Copy `agents/devops.md` to your agents directory
4. Configure systemd timer (hourly recommended)
5. Set up Matrix MCP for alerts

**Example workflow:**
```
Every hour:
  → DevOps agent checks staging health (WebFetch)
  → If backend down: SSH + restart service
  → If frontend missing: SSH + rebuild + deploy
  → If NATS queue backed up: Process errors
  → Send Matrix alert with status
```

**Real-world:** AI Tutor staging monitor runs every hour on GCP VM

### Pattern 2: Research-Driven Development

**Use case:** Validate technical decisions with research skepticism

**Setup:**
1. Use existing researcher, Cynthia, Sylvia agents
2. Enable agent memory system
3. Create OpenSpec proposals for features
4. Set up quality gates (Cynthia + Sylvia approval required)

**Example workflow:**
```
Feature proposal:
  → Researcher investigates best practices
  → Cynthia validates sources and assumptions
  → Researcher refines approach
  → Feature implementer builds
  → Sylvia reviews architecture
  → Only merge if both skeptics approve
```

**Real-world:** Super Alignment simulation uses this for AI safety research

### Pattern 3: MCP Hot-Reload Development

**Use case:** Rapid iteration on MCP servers

**Setup:**
1. Copy `mcp_proxy_system/` to your project
2. Add proxy to `.mcp.json` (one-time restart)
3. Configure target servers in `.mcp_servers.json`
4. Use `load_mcp_server_dynamically()` and `call_dynamic_server_tool()`

**Example workflow:**
```
Development cycle:
  → Edit MCP server code
  → load_mcp_server_dynamically("my-server")  # Hot reload!
  → call_dynamic_server_tool("my-server", "test_tool", {...})
  → Verify behavior
  → Repeat (no restart needed)
```

**Real-world:** Multiverse School uses this for Registrar/Matrix/Dashboard MCPs

### Pattern 4: Multi-Agent Orchestration

**Use case:** Complex workflows requiring multiple specialized agents

**Setup:**
1. Define agents in `agents/` directory
2. Use OpenSpec for proposal management
3. Set up autonomous worker for orchestration
4. Enable quality gates (PM validator + Test validator)

**Example workflow:**
```
Autonomous worker (hourly):
  → Pull approved proposals from openspec/changes/
  → Orchestrator delegates to specialists:
    - Researcher investigates
    - Feature implementer writes code
    - Test writer creates tests
    - PM validator checks requirements
    - Test validator ensures quality
  → Create PR with completed work
  → Archive proposal when merged
```

**Real-world:** Super Alignment uses this for simulation iterations

## Configuration Examples

### .env Configuration for Multi-Pattern Project

```bash
# Project identification
PROJECT_NAME=my_project
NATS_NAMESPACE=my_project

# NATS configuration (for autonomous workers)
NATS_URL=nats://your-nats-server:4222
NATS_USER=orchestrator
NATS_PASSWORD=your-password
NATS_CONTEXT=gcp-orchestrator

# Matrix configuration (for DevOps alerts)
MATRIX_HOMESERVER=https://matrix.your-domain.com
MATRIX_BOT_USER=@agent-bot:your-domain.com
MATRIX_ACCESS_TOKEN=your-token

# Database (if applicable)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Memory system
AGENT_MEMORY_PATH=./agents/memories

# Claude Code limits
MAX_BUDGET_USD=10.0
PREFERRED_MODEL=haiku
```

### .mcp.json Configuration

```json
{
  "mcpServers": {
    "proxy": {
      "command": "python3",
      "args": ["-m", "mcp_proxy_system.servers.proxy_server_v3"],
      "cwd": "/absolute/path/to/project",
      "env": {
        "PYTHONPATH": "/absolute/path/to/project",
        "MCP_CONFIG_PATH": "./.mcp_servers.json"
      }
    }
  }
}
```

### Systemd Timer Configuration

```systemd
# /etc/systemd/system/autonomous-worker.timer
[Unit]
Description=Autonomous Worker Hourly Timer
Requires=autonomous-worker.service

[Timer]
OnCalendar=hourly
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

## Red Team / Blue Team

**Status:** Not applicable (course topics, not agents)

During investigation, we found that "red team" and "blue team" in AI Tutor refer to security courses:
- **7 Hacks 7 Weeks** - Offensive security course (red team)
- **7 Layers 7 Weeks** - Defensive security course (blue team)

These are **not dedicated agent personas**. If you need security testing agents, you would create them following the agent template pattern.

## Migration Checklist

When migrating patterns to a new project:

- [ ] Copy relevant agent definitions from `agents/`
- [ ] Copy `autonomous_worker_templates/` if using scheduled workers
- [ ] Copy `mcp_proxy_system/` if using multiple MCP servers
- [ ] Configure `.env` with project-specific values
- [ ] Set up `.mcp.json` if using MCP proxy
- [ ] Configure `.mcp_servers.json` for target MCP servers
- [ ] Update NATS namespace to project name
- [ ] Set up systemd timers/services on VMs
- [ ] Enable agent memory system
- [ ] Configure OpenSpec workflow
- [ ] Set up quality gates (architect, PM validator, test validator)
- [ ] Configure Matrix/email alerts
- [ ] Test autonomous worker manually
- [ ] Deploy to VM and verify systemd timer

## Best Practices

### 1. Namespace Everything

Use project-specific namespacing to avoid conflicts:

```bash
# NATS streams
NATS_NAMESPACE=my_project
# Becomes: MY_PROJECT_ERROR_REPORTS

# Git branches
auto/worker-TIMESTAMP
# Becomes: auto/my-project-worker-20241217_143022

# Log files
/var/log/autonomous_worker.log
# Becomes: /var/log/my_project_worker.log
```

### 2. Start Conservative

When setting up autonomous workers:
- Start with **daily** schedule, not hourly
- Set **low budget limits** initially ($1-5)
- Use **haiku model** for cost savings
- **Monitor closely** for first week
- **Scale up** after proven stable

### 3. Quality Gates

Always enforce quality gates:
- **Architect** approves all proposals
- **PM validator** verifies requirements met
- **Test validator** ensures no placeholders
- **Manual review** before production deployment

### 4. Monitoring

Set up comprehensive monitoring:
- Systemd timer status
- Log aggregation
- NATS queue depth
- Error rates and types
- Budget consumption
- PR creation rate

### 5. Security

Protect secrets and credentials:
- Never commit `.env` files
- Use `.env.example` templates
- Store API keys in environment variables
- Limit VM user permissions
- Review all autonomous PRs before merge
- Set budget limits to prevent overuse

## Cost Estimates

### Autonomous Workers (Monthly)

**Hourly schedule + haiku model:**
- ~$0.50 per run
- 24 runs/day × 30 days = 720 runs/month
- **Total: ~$360/month**

**Daily schedule + haiku model:**
- ~$0.50 per run
- 30 runs/month
- **Total: ~$15/month**

**Hourly schedule + sonnet model:**
- ~$5 per run
- 720 runs/month
- **Total: ~$3,600/month**

**Recommendation:** Start with daily + haiku ($15/month), scale to hourly only if needed.

### MCP Proxy System

**No ongoing costs** - Just saves context (94% reduction = faster responses)

### Agent Memory System

**No ongoing costs** - Local JSON files

## Support and Troubleshooting

### Common Issues

**1. Autonomous worker not running**
```bash
systemctl status autonomous-worker.timer
sudo journalctl -u autonomous-worker.service -n 50
```

**2. NATS connection failed**
```bash
source .env
nats stream list --context=$NATS_CONTEXT
```

**3. MCP server won't load**
```bash
python -m mcp_proxy_system.servers.proxy_server_v3
# Check for errors
```

**4. Agent memory not persisting**
```bash
ls -la agents/memories/
# Verify JSON files exist and are writable
```

### Getting Help

1. Check README files in each component directory
2. Review logs: `logs/autonomous/worker_*.log`
3. Test components manually before automation
4. Review source projects for working examples:
   - AI Tutor: `/Users/annhoward/src/ai_tutor/`
   - Super Alignment: `/Users/annhoward/src/super_alignment_to_utopia/`
   - Multiverse School: `/Users/annhoward/src/themultiverse.school/`

## Evolution

This is a living document. As new patterns emerge from production projects, they will be:
1. Extracted and generalized
2. Documented here
3. Added to Abstract Agent Team
4. Made available for reuse

**Continuous improvement through abstraction.**

## See Also

- [README.md](README.md) - Project overview
- [QUICKSTART_NEW_PROJECT.md](QUICKSTART_NEW_PROJECT.md) - 5-minute setup
- [INTEGRATION.md](INTEGRATION.md) - Integration guide
- [NATS_INTEGRATION.md](NATS_INTEGRATION.md) - NATS setup
- [openspec/AGENTS.md](openspec/AGENTS.md) - OpenSpec workflow
- [autonomous_worker_templates/README.md](autonomous_worker_templates/README.md) - Worker setup
- [mcp_proxy_system/README.md](mcp_proxy_system/README.md) - MCP proxy guide
