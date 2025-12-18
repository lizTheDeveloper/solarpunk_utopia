# Abstract Agent Team Integration Guide

**How to add Abstract Agent Team with OpenSpec to any project**

---

## Quick Start (Automated)

```bash
# 1. Navigate to your project
cd /path/to/your/new/project

# 2. Run the initialization script
/path/to/abstract_agent_team/scripts/init_new_project.sh

# 3. Follow the prompts
# That's it! OpenSpec and agents are ready to use.
```

---

## What Gets Installed

### OpenSpec Structure

```
your-project/
├── openspec/
│   ├── specs/              # Living requirements
│   ├── changes/            # Active proposals
│   ├── archive/            # Completed work
│   ├── project.md          # Project conventions
│   ├── AGENTS.md           # Agent workflow instructions
│   ├── WORKFLOW_SUMMARY.md # Workflow overview
│   └── README.md           # Quick start guide
```

### NATS Configuration

```
your-project/
├── .env                    # Environment config with your namespace
├── .nats_config           # Shell-sourceable NATS config
├── NATS_INTEGRATION.md    # Full NATS documentation
├── NATS_CREDENTIALS.md    # Quick reference
└── NATS_NAMESPACING.md    # Namespacing guide
```

### Agent Definitions

```
your-project/
├── agents/
│   ├── orchestrator.md          # Workflow coordinator
│   ├── architect.md             # Proposal validator & archivist
│   ├── feature-implementer.md   # Implementation specialist
│   ├── pm-validator.md          # Requirements validator
│   ├── test-validator.md        # Quality validator
│   ├── memories/                # Agent memory storage
│   └── AGENT_MEMORY_MCP_SETUP.md
```

### Supporting Files

```
your-project/
├── scripts/
│   └── nats_helpers.sh         # NATS helper functions
├── coordination_templates/     # Handoff templates
└── .gitignore                  # Protects secrets
```

---

## Post-Installation Setup

### 1. Configure Your Project

Edit `.env` to customize:
```bash
# Your project's unique namespace
NATS_NAMESPACE=your_project_name

# Optional: Add Matrix credentials if using chatroom
MATRIX_HOMESERVER=https://matrix.org
MATRIX_USER=@your-bot:matrix.org
MATRIX_PASSWORD=your-password
```

### 2. Create Initial Specs

Create your first capability spec:

```bash
mkdir -p openspec/specs/core-features
```

Create `openspec/specs/core-features/spec.md`:
```markdown
# Core Features Specification

**Domain:** Core Features
**Last Updated:** 2025-12-06
**Status:** Active

## Requirements

### Requirement: User Authentication

The system SHALL provide secure user authentication.

#### Scenario: Successful login

- WHEN a user provides valid credentials
- THEN they receive an authentication token
- AND can access protected resources
```

### 3. Install Dependencies

#### NATS CLI (for stream management)
```bash
curl -sf https://binaries.nats.dev/nats-io/natscli/nats@latest | sh
```

#### Python packages (if using Python agents)
```bash
pip install nats-py spacy
python -m spacy download en_core_web_sm
```

#### Node packages (if using MCP chatroom)
```bash
cd mcp-chatroom
npm install
npm run build
```

### 4. Configure NATS Context

```bash
source .env

~/bin/nats context save $PROJECT_NAME \
  --server=$NATS_URL \
  --user=$NATS_USER \
  --password=$NATS_PASSWORD

# Test connection
~/bin/nats server check connection --context=$PROJECT_NAME
```

### 5. Create Your First Proposal

Agents can now create proposals in `openspec/changes/`:

```bash
mkdir -p openspec/changes/user-authentication
```

Create `openspec/changes/user-authentication/proposal.md`:
```markdown
# Proposal: User Authentication

**Submitted By:** orchestrator
**Date:** 2025-12-06
**Status:** Draft
**Complexity:** 3 systems

## Problem Statement

Need secure user authentication for the application.

## Proposed Solution

Implement JWT-based authentication with...

## Requirements

### Requirement: Login Endpoint

The system SHALL provide a login endpoint...

#### Scenario: Valid credentials
- WHEN user submits valid credentials
- THEN JWT token is returned
```

---

## Using the System

### Agent Workflow

1. **Any agent identifies needed work**
   - Creates proposal in `openspec/changes/[feature-name]/`
   - Posts to coordination channel

2. **Architect validates**
   - Reviews proposal for quality
   - Approves or requests changes

3. **Feature Implementer executes**
   - Claims approved proposal
   - Implements according to tasks
   - Posts progress updates

4. **PM & Testing validate**
   - PM checks requirements met
   - Testing checks code quality
   - Both must pass

5. **Architect archives**
   - Moves to `openspec/archive/`
   - Updates changelog

### For Claude Code Users

If using Claude Code, you may have access to OpenSpec slash commands:
- `/openspec:proposal` - Generate proposal from description
- `/openspec:apply` - Apply approved proposal changes
- `/openspec:archive` - Archive completed proposal

Check if these are available by typing `/openspec` in Claude Code.

### Using NATS Helper Functions

```bash
# Source helpers
source scripts/nats_helpers.sh

# Create project-namespaced streams
nats_create_stream "error_reports" "errors.>" "workqueue"
nats_create_stream "tasks" "tasks.>" "workqueue"

# List your project's streams
nats_list_project_streams

# Publish to namespaced subject
nats_publish "tasks.test" '{"task": "example"}'

# Subscribe to namespaced subject
nats_subscribe "errors.>"
```

---

## Customization

### Adjust Agent Behavior

Edit agent files in `agents/` to customize:
- Agent personality and communication style
- Domain expertise and knowledge
- Decision-making patterns
- Quality gates and validation rules

### Add More Agents

Copy additional agents from abstract_agent_team:
- `super-alignment-researcher.md` - Research specialist
- `research-skeptic.md` - Critical validation
- `architecture-skeptic.md` - Performance review
- Others in the agents/ directory

### Customize Project Conventions

Edit `openspec/project.md`:
- Development standards
- Testing requirements
- Documentation standards
- Complexity estimation rules

---

## Verification

### Check OpenSpec Setup

```bash
# Directory structure should exist
ls -la openspec/

# Should see: specs, changes, archive, *.md files
```

### Check NATS Configuration

```bash
# Environment variables set
source .env
echo $NATS_NAMESPACE  # Should show your project name

# Can use helper functions
source scripts/nats_helpers.sh
nats_stream_name "test"  # Should show YOUR_PROJECT_TEST
```

### Check Agents Installed

```bash
# Core agents present
ls agents/orchestrator.md
ls agents/architect.md
ls agents/feature-implementer.md
ls agents/pm-validator.md
ls agents/test-validator.md
```

---

## Troubleshooting

### "OpenSpec not found"
Install OpenSpec:
```bash
npm install -g @fission-ai/openspec@latest
```

### "NATS connection refused"
Check if NATS server is running:
```bash
nc -zv 34.185.163.86 4222
```

If down, start the GCP VM:
```bash
gcloud compute instances start nats-jetstream --zone=europe-west3-a
```

### "Namespace conflicts"
Make sure `NATS_NAMESPACE` in `.env` is unique to your project. Each project should have a different namespace.

---

## Documentation References

After installation, these files provide detailed guidance:

| File | Purpose |
|------|---------|
| `openspec/WORKFLOW_SUMMARY.md` | Complete workflow overview |
| `openspec/AGENTS.md` | Detailed agent instructions |
| `openspec/project.md` | Project conventions |
| `NATS_INTEGRATION.md` | Full NATS documentation |
| `NATS_NAMESPACING.md` | Namespacing guide |
| `NATS_CREDENTIALS.md` | Quick credential reference |

---

## Support

- **OpenSpec Issues:** https://github.com/Fission-AI/OpenSpec/issues
- **Abstract Agent Team Issues:** Create issue in your project
- **NATS Documentation:** https://docs.nats.io/

---

## Next Steps

1. ✅ Installation complete
2. ⬜ Create your first spec in `openspec/specs/`
3. ⬜ Have an agent create a proposal
4. ⬜ Walk through the validation workflow
5. ⬜ Set up NATS streams for your project
6. ⬜ Configure MCP chatroom (optional)

Start with the workflow in `openspec/WORKFLOW_SUMMARY.md`!
