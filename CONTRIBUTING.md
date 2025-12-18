# Contributing to Solarpunk Mesh Network

Thank you for your interest in contributing to infrastructure for regenerative communities! 🌱

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Architecture Overview](#architecture-overview)
5. [Making Changes](#making-changes)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Pull Request Process](#pull-request-process)
9. [Communication](#communication)

---

## Code of Conduct

This project is built for **mutual aid, solidarity, and regenerative communities**. We expect all contributors to:

- **Be kind and respectful** - We're building tools for community care
- **Assume good intentions** - Everyone is learning and growing
- **Center community needs** - Real communities will use this software
- **Embrace transparency** - Explain your reasoning, show your work
- **Practice consent** - No surveillance features, always opt-in
- **Share knowledge** - Document what you learn

**We will not tolerate:**
- Harassment, discrimination, or exclusion
- Surveillance features or tracking without consent
- Extractive or exploitative patterns
- Dishonesty or bad faith arguments

---

## Getting Started

### Prerequisites

- **Python 3.12+** for backend
- **Node.js 18+** for frontend
- **Git** for version control
- **Docker** (optional) for deployment
- **Basic understanding** of gift economies, ValueFlows, and mesh networks

### First Time Setup

1. **Read the documentation:**
   - [QUICKSTART.md](QUICKSTART.md) - Get the system running
   - [BUILD_STATUS.md](BUILD_STATUS.md) - What's implemented
   - [CLAUDE.md](CLAUDE.md) - Repository architecture
   - [FINAL_SUMMARY.md](FINAL_SUMMARY.md) - Complete overview

2. **Understand the vision:**
   - [BUILD_PLAN.md](BUILD_PLAN.md) - Original specification
   - [openspec/](openspec/) - System proposals

3. **Run the system locally:**
   ```bash
   git clone https://github.com/yourusername/solarpunk_utopia.git
   cd solarpunk_utopia
   ./run_all_services.sh
   cd frontend && npm run dev
   ```

4. **Run the tests:**
   ```bash
   pytest tests/integration/ -v -s
   ```

---

## Development Setup

### Backend (Python)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run individual services
python -m app.main                    # DTN Bundle System
python -m valueflows_node.main        # ValueFlows Node
python -m discovery_search.main       # Discovery & Search
python -m file_chunking.main          # File Chunking
python -m mesh_network.bridge_node.main  # Bridge Management
```

### Frontend (React + TypeScript)

```bash
cd frontend
npm install
npm run dev     # Development server
npm run build   # Production build
npm run lint    # Type checking
```

### Database

- **SQLite** databases created automatically on first run
- Located in `{service}/data/` directories
- Reset: `rm -f */data/*.db && ./run_all_services.sh`

---

## Architecture Overview

### System Layers

```
TIER 2: Intelligence (AI Agents)
   ↓
TIER 1: Core Functionality (Discovery, Files, Mesh)
   ↓
TIER 0: Foundation (DTN, ValueFlows)
```

### Key Systems

1. **DTN Bundle System** (`/app/`)
   - Store-and-forward networking
   - Ed25519 signing, priority queues
   - Entry point: `app/main.py`

2. **ValueFlows Node** (`/valueflows_node/`)
   - Gift economy coordination
   - 13 VF object types
   - Entry point: `valueflows_node/app/main.py`

3. **Discovery & Search** (`/discovery_search/`)
   - Distributed indexes and queries
   - Entry point: `discovery_search/main.py`

4. **File Chunking** (`/file_chunking/`)
   - Content-addressed distribution
   - Entry point: `file_chunking/main.py`

5. **Multi-AP Mesh** (`/mesh_network/`)
   - Bridge node coordination
   - Entry point: `mesh_network/bridge_node/main.py`

6. **Unified Frontend** (`/frontend/`)
   - React + TypeScript UI
   - Entry point: `frontend/src/main.tsx`

### Code Patterns

- **FastAPI** for all REST APIs
- **Pydantic** for data validation
- **SQLite** for persistence
- **asyncio** for async operations
- **React Query** for data fetching
- **TypeScript** for type safety

---

## Making Changes

### Branch Naming

- `feature/add-xyz` - New features
- `fix/issue-123` - Bug fixes
- `docs/improve-readme` - Documentation
- `refactor/simplify-xyz` - Code improvements
- `test/add-integration-test` - Testing

### Commit Messages

Follow the existing pattern:

```
Short summary (50 chars or less)

- Detailed explanation of what changed
- Why the change was needed
- Any trade-offs or decisions made

Closes #issue-number (if applicable)
```

**Example:**
```
Add perishables priority to bundle forwarding

- Perishables now get higher priority than normal bundles
- TTL shortened to 48 hours for food items
- Updated forwarding service to check resource category

This ensures food reaches recipients before spoiling.

Closes #42
```

### Code Style

**Python:**
- Follow PEP 8
- Use type hints everywhere
- Docstrings for public functions
- Keep functions focused and small
- Comprehensive error handling

**TypeScript:**
- Use strict mode
- Explicit types (no `any`)
- Functional components with hooks
- Descriptive variable names

**Example Python:**
```python
async def create_bundle(
    payload: Dict[str, Any],
    priority: BundlePriority,
    ttl_hours: int = 72
) -> Bundle:
    """
    Create a new DTN bundle with signing.
    
    Args:
        payload: Bundle payload data
        priority: Priority level for forwarding
        ttl_hours: Time-to-live in hours
        
    Returns:
        Signed bundle ready for transmission
    """
    bundle = Bundle(
        payload=payload,
        priority=priority,
        expires_at=calculate_expiry(ttl_hours)
    )
    bundle.signature = sign_bundle(bundle)
    return bundle
```

---

## Testing

### Running Tests

```bash
# Backend unit tests
pytest app/tests/ -v
pytest valueflows_node/tests/ -v
pytest discovery_search/tests/ -v

# Integration tests (requires services running)
./run_all_services.sh
pytest tests/integration/ -v -s

# Frontend tests (when added)
cd frontend && npm test
```

### Writing Tests

1. **Unit tests** for individual functions/classes
2. **Integration tests** for system interactions
3. **End-to-end tests** for complete workflows

**Example integration test:**
```python
@pytest.mark.asyncio
async def test_offer_propagates_via_dtn():
    """Test that a ValueFlows offer propagates as a DTN bundle"""
    
    # Create offer
    offer = await create_offer(
        agent_id="alice",
        resource="tomatoes",
        quantity=5.0
    )
    
    # Verify bundle created
    bundles = await get_dtn_bundles(topic="valueflows")
    assert any(b.payload_type == "vf:Listing" for b in bundles)
    
    # Verify signature
    bundle = find_bundle_for_offer(bundles, offer.id)
    assert verify_signature(bundle)
```

### Test Coverage

Aim for:
- **80%+ coverage** for critical paths
- **100% coverage** for security-sensitive code (signing, verification)
- All API endpoints tested
- Edge cases and error conditions

---

## Documentation

### What to Document

1. **Code comments** - For complex logic only
2. **Docstrings** - For all public functions/classes
3. **README files** - For each major system
4. **API docs** - Auto-generated via FastAPI
5. **Architecture docs** - For design decisions

### Documentation Standards

- **Clear and concise** - No jargon without explanation
- **Examples included** - Show how to use the code
- **Updated with code** - Never let docs go stale
- **Accessible language** - Not everyone is a senior dev

**Example README section:**
```markdown
## Creating an Offer

To create a new offer in the gift economy:

1. Create an Agent (person or group)
2. Create a ResourceSpec (what you're offering)
3. Create a Listing (the actual offer)

```python
# 1. Create agent
alice = Agent(name="Alice", type="person")

# 2. Create resource
tomatoes = ResourceSpec(name="Tomatoes", category="food", unit="lbs")

# 3. Create offer
offer = Listing(
    listing_type="offer",
    provider_agent_id=alice.id,
    resource_spec_id=tomatoes.id,
    quantity=5.0,
    available_until="2025-12-20T00:00:00Z"
)
```

The offer will automatically:
- Get signed with Ed25519
- Publish as a DTN bundle
- Appear in discovery indexes
- Be visible to AI matchmaker
```

---

## Pull Request Process

### Before Submitting

1. **Run all tests** - `pytest tests/integration/ -v`
2. **Update documentation** - README, docstrings, etc.
3. **Check code style** - Follow existing patterns
4. **Test manually** - Actually use the feature
5. **Update CHANGELOG** - If applicable

### PR Template

When you submit a PR, include:

```markdown
## Description
What does this PR do? Why is it needed?

## Changes Made
- List of specific changes
- Files modified
- New features added

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Documentation
- [ ] Code comments added
- [ ] README updated
- [ ] API docs generated

## Screenshots (if UI changes)
[Add screenshots showing before/after]

## Related Issues
Closes #issue-number
```

### Review Process

1. **Automated checks** run (tests, linting)
2. **Code review** by maintainer
3. **Feedback addressed** (if any)
4. **Merged to main**

**We look for:**
- ✅ Code quality and clarity
- ✅ Test coverage
- ✅ Documentation completeness
- ✅ Alignment with project values
- ✅ Real-world utility for communities

---

## Communication

### Where to Ask Questions

- **GitHub Discussions** - General questions, ideas
- **GitHub Issues** - Bug reports, feature requests
- **Pull Requests** - Code-specific discussions

### Response Time

This is a community project. We aim to respond within:
- **Issues:** 1-3 days
- **Pull Requests:** 3-7 days
- **Discussions:** Best effort

Be patient and kind. We're all volunteers building infrastructure for a better world.

---

## Areas Needing Help

### High Priority

1. **Phone Deployment System** (3 systems deferred)
   - APK packaging (Python → Android)
   - Provisioning automation (adb scripts)
   - Content loading (Kiwix, maps)

2. **Load Testing**
   - Test with 20+ concurrent users
   - Measure actual propagation times
   - Optimize bottlenecks

3. **Hardware Deployment**
   - Raspberry Pi testing
   - Android bridge node testing
   - Real-world mesh validation

### Medium Priority

1. **Additional Agents**
   - Red Team security testing agent
   - Blue Team monitoring agent
   - Resource forecasting agent

2. **Mode B Research**
   - Wi-Fi Direct viability
   - Multi-group support
   - Battery impact analysis

3. **Cross-Commune Sync**
   - NATS integration
   - Federation patterns
   - Inter-commune routing

### Low Priority

1. **UI/UX Polish**
   - Mobile-first design improvements
   - Accessibility enhancements
   - Offline-first indicators

2. **Performance Optimization**
   - Database query optimization
   - Bundle compression
   - Cache efficiency

3. **Documentation**
   - Video tutorials
   - Translation to other languages
   - Community deployment guides

---

## Learning Resources

### Gift Economy & ValueFlows
- [ValueFlows Specification](https://valueflo.ws/)
- [The Gift Economy](https://en.wikipedia.org/wiki/Gift_economy)
- "The Gift" by Lewis Hyde

### Delay-Tolerant Networking
- [DTN Architecture RFC](https://datatracker.ietf.org/doc/html/rfc4838)
- [Bundle Protocol](https://datatracker.ietf.org/doc/html/rfc5050)

### Mesh Networks
- [BATMAN-adv Documentation](https://www.open-mesh.org/)
- [Wireless Mesh Networks](https://en.wikipedia.org/wiki/Wireless_mesh_network)

### Solarpunk & Regeneration
- [Solarpunk Movement](https://en.wikipedia.org/wiki/Solarpunk)
- "Braiding Sweetgrass" by Robin Wall Kimmerer
- "The Mushroom at the End of the World" by Anna Tsing

---

## Recognition

### Contributors

All contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Appreciated by communities using this software

### Types of Contributions

We value **all** contributions:
- 💻 Code (features, fixes, refactoring)
- 📖 Documentation (guides, examples, translations)
- 🧪 Testing (writing tests, bug reports)
- 💡 Ideas (proposals, designs, discussions)
- 🎨 Design (UI/UX, graphics, branding)
- 🌐 Community (workshops, deployment, support)

---

## Questions?

- Read [CLAUDE.md](CLAUDE.md) for repository guide
- Check [FINAL_SUMMARY.md](FINAL_SUMMARY.md) for overview
- Ask in GitHub Discussions
- Open an issue if you find bugs

**Thank you for contributing to infrastructure for regenerative communities! 🌱**

**Together, we're building tools for mutual aid, solidarity, and a better world.**
