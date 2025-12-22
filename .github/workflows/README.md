# CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing and quality assurance.

## Workflows

### 1. E2E Tests (`e2e-tests.yml`)

Runs end-to-end tests on every push and pull request.

**Jobs:**
- **Python E2E Tests**: Backend API flow tests (12 test files)
  - Rapid Response flow
  - Sanctuary Network flow
  - Web of Trust vouch chain
  - Mycelial Strike defense
  - Blocking with silent failure
  - DTN Mesh Sync
  - Cross-Community Discovery
  - Saturnalia role inversion
  - Ancestor Voting
  - Bakunin Analytics
  - Silence Weight in voting
  - Temporal Justice / Slow Exchanges
  - Care Outreach conversion

- **Playwright E2E Tests**: Full-stack UI flow tests
  - Onboarding flow
  - Steward Dashboard
  - Philosophical features (anonymous gifts, rest mode, conscientization)
  - Exchange completion
  - Edit/delete listings

**Services Started:**
- DTN Bundle System (port 8000)
- ValueFlows Node (port 8001)
- Frontend Dev Server (port 3000, Playwright only)

**Artifacts:**
- Coverage reports (uploaded to Codecov)
- Playwright HTML report
- Screenshots on failure

### 2. Unit & Integration Tests (`tests.yml`)

Runs unit and integration tests on every push and pull request.

**Jobs:**
- **Unit Tests**: Fast, isolated component tests
- **Integration Tests**: Multi-component interaction tests
- **ValueFlows Tests**: Gift economy core logic tests
- **Root Tests**: Panic features, fraud protections, governance

**Artifacts:**
- Coverage reports for each job

## Running Locally

### E2E Tests (Python)

```bash
# Start services
docker-compose up -d dtn-bundle-system valueflows-node

# Or manually
uvicorn app.main:app --port 8000 &
uvicorn valueflows_node.app.main:app --port 8001 &

# Run tests
pytest tests/e2e/ -v
```

### E2E Tests (Playwright)

```bash
# Start backend services (as above)

# Start frontend
cd frontend && npm run dev &

# Run Playwright tests
cd frontend && npx playwright test

# With UI
npx playwright test --ui
```

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

## Success Criteria

All workflows must pass before merging to main:
- ✅ All Python E2E tests passing
- ✅ All Playwright tests passing
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ Code coverage > 70% (target)

## Debugging Failed Tests

### Check workflow logs
1. Go to Actions tab in GitHub
2. Click on failed workflow run
3. Expand failed job
4. Review error messages

### Download artifacts
- Playwright reports: visual HTML report with screenshots
- Test screenshots: captured on failure
- Coverage reports: detailed coverage analysis

### Run locally
```bash
# Reproduce exact CI environment
act -j python-e2e  # Using nektos/act

# Or run manually as shown above
```

## Architecture Constraints

All tests verify compliance with:
1. **Old phones**: No heavy dependencies
2. **Fully distributed**: No central server required
3. **Works offline**: DTN mesh sync functional
4. **No big tech**: Zero external dependencies
5. **Seizure resistant**: Data compartmentalization
6. **Understandable**: Clear error messages
7. **No surveillance capitalism**: No tracking patterns
8. **Harm reduction**: Graceful degradation

See [ARCHITECTURE_CONSTRAINTS.md](../../openspec/ARCHITECTURE_CONSTRAINTS.md) for details.

## Workshop Readiness

Before workshop, all E2E tests must pass to ensure:
- 200+ attendees can onboard via event QR
- Mesh messaging works phone-to-phone
- Sanctuary features work correctly
- Rapid response system is reliable
- Web of Trust prevents infiltrators

Lives depend on these systems working correctly. E2E tests are non-negotiable.
