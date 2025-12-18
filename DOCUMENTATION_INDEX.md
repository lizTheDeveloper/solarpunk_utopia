# Documentation Index

Complete guide to all documentation in the Solarpunk Mesh Network repository.

---

## Quick Navigation

**Just getting started?** → [QUICKSTART.md](QUICKSTART.md)
**Want to deploy?** → [DEPLOYMENT.md](DEPLOYMENT.md)
**Understanding the build?** → [FINAL_SUMMARY.md](FINAL_SUMMARY.md)
**Contributing?** → [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Overview Documents

### [README.md](README.md)
**What:** Project overview and introduction
**When to read:** First thing when discovering the project
**Key content:**
- What is this project?
- Quick start commands
- Feature overview
- Architecture diagram
- Technology stack

### [FINAL_SUMMARY.md](FINAL_SUMMARY.md) ⭐
**What:** Complete comprehensive summary of everything built
**When to read:** To understand the full scope and achievement
**Length:** 900+ lines
**Key content:**
- Complete system breakdown (28 of 31 systems)
- Statistics (235+ files, 32,000+ lines)
- All features implemented
- Architecture highlights
- Performance characteristics
- Complete file structure

---

## Getting Started

### [QUICKSTART.md](QUICKSTART.md)
**What:** 5-minute guide to running the system
**When to read:** When you want to try it immediately
**Key content:**
- Prerequisites
- Setup commands
- Service endpoints
- Basic operations (create offer, search, upload file)
- Troubleshooting

### [CLAUDE.md](CLAUDE.md)
**What:** Repository guide for AI agents and developers
**When to read:** When working on the codebase
**Key content:**
- Repository purpose and architecture
- Key commands (build, test, deploy)
- Agent workflow patterns
- Critical patterns (NATS namespacing)
- Environment configuration

---

## Planning & Vision

### [BUILD_PLAN.md](BUILD_PLAN.md)
**What:** Original build plan and vision
**When to read:** To understand the "why" behind the project
**Updated:** Now includes completion status
**Key content:**
- Vision for regenerative communities
- 7 proposals (31 systems total)
- Implementation strategy
- Success criteria
- Post-workshop roadmap

### [BUILD_STATUS.md](BUILD_STATUS.md)
**What:** Detailed build status and metrics
**When to read:** To see what's complete and what's pending
**Length:** 600+ lines
**Key content:**
- Progress by tier (TIER 0/1/2)
- Code statistics (files, lines, endpoints, tests)
- API endpoints summary
- Features implemented
- Deferred components
- Integration status

---

## Deployment

### [DEPLOYMENT.md](DEPLOYMENT.md) ⭐
**What:** Complete production deployment guide
**When to read:** When deploying to production
**Length:** 800+ lines
**Key content:**
- Development deployment
- Production deployment (systemd, nginx)
- Docker deployment
- Hardware deployment (Raspberry Pi, Android)
- Monitoring & maintenance
- Troubleshooting
- Scaling strategies
- Security considerations
- Backup & recovery

---

## System-Specific Documentation

### DTN Bundle System
**Location:** `/app/`
**Docs:** No dedicated README (integrated in main docs)
**API Docs:** http://localhost:8000/docs
**Key files:**
- `app/models/bundle.py` - Bundle data model
- `app/services/crypto_service.py` - Ed25519 signing
- `app/database/queues.py` - Queue management

### ValueFlows Node
**Location:** `/valueflows_node/`
**Docs:**
- `valueflows_node/README.md` - System overview
- `valueflows_node/IMPLEMENTATION_SUMMARY.md` - Implementation details
**API Docs:** http://localhost:8001/docs
**Key features:** All 13 VF object types, gift economy coordination

### Discovery & Search
**Location:** `/discovery_search/`
**Docs:**
- `discovery_search/README.md` - Complete user guide
- `discovery_search/EXAMPLES.md` - 15 practical examples
- `discovery_search/IMPLEMENTATION_SUMMARY.md` - Technical details
**API Docs:** http://localhost:8003/docs
**Key features:** Distributed indexes, query propagation, speculative caching

### File Chunking
**Location:** `/file_chunking/`
**Docs:**
- `file_chunking/README.md` - User guide
- `file_chunking/DEPLOYMENT.md` - Production deployment
- `file_chunking/IMPLEMENTATION_SUMMARY.md` - Technical summary
**API Docs:** http://localhost:8004/docs
**Key features:** Content-addressed storage, Merkle trees, library caching

### Multi-AP Mesh Network
**Location:** `/mesh_network/`
**Docs:**
- `mesh_network/README.md` - System overview
- `mesh_network/QUICKSTART.md` - 5-minute setup
- `mesh_network/IMPLEMENTATION_SUMMARY.md` - Complete details
- `mesh_network/docs/deployment_guide.md` - Hardware deployment
- `mesh_network/docs/mode_a_requirements.md` - BATMAN-adv setup
- `mesh_network/ap_configs/README.md` - AP configuration guide
**API Docs:** http://localhost:8002/docs
**Key features:** Bridge nodes, Mode A/C, effectiveness tracking

### Agent System
**Location:** `/app/agents/`
**Docs:**
- `app/agents/README.md` - Agent overview and usage
**Key features:** 7 AI agents, proposal framework, approval gates

### Unified Frontend
**Location:** `/frontend/`
**Docs:**
- `frontend/README.md` - Frontend setup and architecture
**Key features:** React + TypeScript, 10 pages, 14 components

---

## OpenSpec Proposals

### [openspec/SOLARPUNK_PROPOSALS_OVERVIEW.md](openspec/SOLARPUNK_PROPOSALS_OVERVIEW.md)
**What:** Overview of all 7 proposals with dependencies
**Key content:**
- Dependency graph (TIER 0 → TIER 1 → TIER 2)
- Proposal summaries
- Implementation order
- Orchestration strategy
- Quality gates
- Workshop readiness checklist

### Individual Proposals
**Location:** `openspec/changes/*/`

Each proposal has:
- `proposal.md` - Requirements (SHALL/MUST, WHEN/THEN scenarios)
- `tasks.md` - Implementation breakdown with complexity

**TIER 0:**
- `dtn-bundle-system/` (5 systems)
- `valueflows-node-full/` (6 systems)
- `phone-deployment-system/` (3 systems - deferred)

**TIER 1:**
- `discovery-search-system/` (3 systems)
- `file-chunking-system/` (3 systems)
- `multi-ap-mesh-network/` (4 systems)

**TIER 2:**
- `agent-commune-os/` (7 systems)

---

## Contributing

### [CONTRIBUTING.md](CONTRIBUTING.md) ⭐
**What:** Complete contribution guide
**When to read:** Before making your first contribution
**Key content:**
- Code of conduct
- Development setup
- Architecture overview
- Making changes (branch naming, commit messages, code style)
- Testing guidelines
- Documentation standards
- Pull request process
- Areas needing help
- Learning resources

### [CHANGELOG.md](CHANGELOG.md)
**What:** Version history and release notes
**When to read:** To see what changed between versions
**Key content:**
- v1.0.0 release notes (initial release)
- Future plans (short/medium/long-term)

---

## Testing

### Integration Tests
**Location:** `tests/integration/`
**Files:**
- `test_end_to_end_gift_economy.py` - Complete gift economy flow
- `test_knowledge_distribution.py` - File chunking flow

**Run:** `pytest tests/integration/ -v -s`

### Component Tests
Each component has its own test suite:
- `app/tests/` - DTN tests
- `valueflows_node/tests/` - VF tests
- `discovery_search/tests/` - Discovery tests
- `file_chunking/tests/` - Chunking tests
- `mesh_network/bridge_node/tests/` - Bridge tests

---

## Infrastructure

### Docker
**Files:**
- `docker-compose.yml` - Service orchestration
- `docker/Dockerfile.*` - Individual service containers
- `docker/nginx.conf` - Reverse proxy configuration
- `.dockerignore` - Build optimization

**Commands:**
```bash
docker-compose up -d      # Start all services
docker-compose logs -f    # View logs
docker-compose down       # Stop all services
```

### Scripts
- `run_all_services.sh` - Start all backend services
- `stop_all_services.sh` - Stop all services
- `mesh_network/validate_installation.py` - Validate setup

---

## API Documentation

All APIs have auto-generated interactive documentation:

- **DTN Bundle System:** http://localhost:8000/docs
- **ValueFlows Node:** http://localhost:8001/docs
- **Bridge Management:** http://localhost:8002/docs
- **Discovery & Search:** http://localhost:8003/docs
- **File Chunking:** http://localhost:8004/docs

These are **live** and allow testing API calls directly in the browser.

---

## Historical/Reference Documents

These documents were created during development and provide context:

- `DTN_ARCHITECTURE.md` - DTN system architecture details
- `DTN_BUNDLE_SYSTEM_README.md` - Original DTN README
- `DTN_BUNDLE_SYSTEM_SUMMARY.md` - DTN build summary
- `AGENT_SYSTEM_SUMMARY.md` - Agent system details
- `AGENT_QUICK_START.md` - Quick agent guide
- Various `*_SUMMARY.md` files - Component summaries

These are preserved for historical context but may be superseded by newer docs.

---

## Documentation by Audience

### For Users (Running the System)
1. [README.md](README.md) - What is this?
2. [QUICKSTART.md](QUICKSTART.md) - How do I run it?
3. System READMEs - How do I use each feature?
4. API docs (http://localhost:{port}/docs) - How do I call the APIs?

### For Deployers (Production)
1. [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide
2. [BUILD_STATUS.md](BUILD_STATUS.md) - What's ready?
3. Component deployment docs - System-specific deployment
4. `mesh_network/docs/deployment_guide.md` - Hardware deployment

### For Developers (Contributing)
1. [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
2. [CLAUDE.md](CLAUDE.md) - Repository architecture
3. [BUILD_STATUS.md](BUILD_STATUS.md) - What's implemented
4. [FINAL_SUMMARY.md](FINAL_SUMMARY.md) - Complete overview
5. Component IMPLEMENTATION_SUMMARY.md files - Technical details

### For Planners (Understanding Vision)
1. [BUILD_PLAN.md](BUILD_PLAN.md) - Original vision
2. [openspec/SOLARPUNK_PROPOSALS_OVERVIEW.md](openspec/SOLARPUNK_PROPOSALS_OVERVIEW.md) - Proposal breakdown
3. Individual proposals - Detailed requirements

---

## Documentation Maintenance

### When to Update Documentation

- **Adding features:** Update component README + CHANGELOG
- **Fixing bugs:** Update CHANGELOG
- **Changing architecture:** Update CLAUDE.md + component docs
- **Deployment changes:** Update DEPLOYMENT.md
- **API changes:** Auto-generated, but update examples

### Documentation Standards

- **Clear and concise** - No unnecessary jargon
- **Examples included** - Show, don't just tell
- **Up to date** - Update docs with code changes
- **Accessible** - Write for various skill levels

---

## Quick Reference

| I want to... | Read this |
|-------------|-----------|
| Understand what this project is | [README.md](README.md) |
| Run it locally in 5 minutes | [QUICKSTART.md](QUICKSTART.md) |
| Deploy to production | [DEPLOYMENT.md](DEPLOYMENT.md) |
| See complete build details | [FINAL_SUMMARY.md](FINAL_SUMMARY.md) |
| Understand the vision | [BUILD_PLAN.md](BUILD_PLAN.md) |
| Contribute code | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Deploy to Raspberry Pi | `mesh_network/docs/deployment_guide.md` |
| Learn about a specific system | Component README in system directory |
| Test the APIs | http://localhost:{port}/docs |
| Write integration tests | `tests/integration/` examples |

---

## Total Documentation

- **Main docs:** 10 comprehensive guides (8,000+ lines)
- **Component docs:** 7 system READMEs
- **OpenSpec:** 7 proposals × 2 files = 14 specs
- **API docs:** 5 auto-generated sites
- **Total:** 30+ documentation files

---

## Getting Help

1. **Search the docs** - Use this index to find what you need
2. **Check examples** - Most docs include practical examples
3. **Read code comments** - Code is documented inline
4. **Ask in Discussions** - GitHub Discussions for questions
5. **Open an Issue** - For bugs or missing documentation

---

**This documentation is living and growing. Contribute improvements!**

**Built with ❤️ for regenerative gift economy communities 🌱**
