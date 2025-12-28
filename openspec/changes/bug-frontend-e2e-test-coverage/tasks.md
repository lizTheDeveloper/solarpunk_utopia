# Tasks: Frontend E2E Test Coverage

## Phase 1: Test Infrastructure Setup

### Task 1.1: Set up test data management
- [ ] Create `frontend/tests/helpers/test-data.ts`
- [ ] Add functions for seeding test database
- [ ] Add functions for cleaning up test data
- [ ] Create test fixtures for users, offers, needs, communities
- [ ] Document test data patterns

### Task 1.2: Configure Playwright
- [ ] Review existing `playwright.config.ts`
- [ ] Add base URL configuration
- [ ] Configure test database connection
- [ ] Set up parallel test execution
- [ ] Add screenshot/video capture on failure

### Task 1.3: Create page object models
- [ ] Create `frontend/tests/helpers/page-objects.ts`
- [ ] Add LoginPage class
- [ ] Add OffersPage class
- [ ] Add NeedsPage class
- [ ] Add CommunityPage class
- [ ] Document page object pattern

## Phase 2: Critical Flow Tests

### Task 2.1: Authentication flow test
- [ ] Create `frontend/tests/e2e/auth.spec.ts`
- [ ] Test: New user onboarding flow
- [ ] Test: Login with valid credentials
- [ ] Test: Login with invalid credentials
- [ ] Test: Logout flow
- [ ] Test: Redirect to onboarding if not completed

### Task 2.2: Offer creation flow test
- [ ] Create `frontend/tests/e2e/offers.spec.ts`
- [ ] Test: Create offer with all fields
- [ ] Test: Create offer with minimal fields
- [ ] Test: Create anonymous gift
- [ ] Test: Validation errors display correctly
- [ ] Test: Success message and redirect

### Task 2.3: Offer edit/delete flow test
- [ ] Test: Edit existing offer
- [ ] Test: Only owner can edit offer
- [ ] Test: Delete offer with confirmation
- [ ] Test: Offer removed from list after delete

### Task 2.4: Need creation flow test
- [ ] Create `frontend/tests/e2e/needs.spec.ts`
- [ ] Test: Create need with all fields
- [ ] Test: Create need with minimal fields
- [ ] Test: Validation errors display correctly
- [ ] Test: Success message and redirect

### Task 2.5: Need edit/delete flow test
- [ ] Test: Edit existing need
- [ ] Test: Only owner can edit need
- [ ] Test: Delete need with confirmation
- [ ] Test: Need removed from list after delete

### Task 2.6: Community selection flow test
- [ ] Create `frontend/tests/e2e/community.spec.ts`
- [ ] Test: No community selected shows empty state
- [ ] Test: Browse communities
- [ ] Test: Join a community
- [ ] Test: Community offers/needs update after selection

### Task 2.7: Filtering and search test
- [ ] Create `frontend/tests/e2e/search-filter.spec.ts`
- [ ] Test: Filter offers by category
- [ ] Test: Filter offers by location
- [ ] Test: Search offers by term
- [ ] Test: Combined filters work correctly
- [ ] Test: Clear filters resets results
- [ ] Test: Results count updates correctly

## Phase 3: CI/CD Integration

### Task 3.1: Add tests to CI pipeline
- [ ] Update `.github/workflows/test.yml` (if exists)
- [ ] Add Playwright test step
- [ ] Configure test environment variables
- [ ] Set up test database for CI
- [ ] Ensure tests run on all PRs

### Task 3.2: Configure test reporting
- [ ] Add test result reporting to CI
- [ ] Generate HTML test reports
- [ ] Upload test artifacts (screenshots/videos) on failure
- [ ] Add test coverage badge to README

## Phase 4: Documentation

### Task 4.1: Write test documentation
- [ ] Create `frontend/tests/README.md`
- [ ] Document how to run tests locally
- [ ] Document page object pattern
- [ ] Document test data management
- [ ] Add troubleshooting section

### Task 4.2: Update contributing guide
- [ ] Add E2E testing requirements to CONTRIBUTING.md
- [ ] Document when to add E2E tests
- [ ] Add examples of good test structure

## Acceptance Checklist

- [ ] All 5 critical user flows have passing E2E tests
- [ ] Tests run in CI/CD pipeline
- [ ] Tests are stable (no flaky failures)
- [ ] Test coverage >80% of critical paths
- [ ] Documentation is complete and clear
- [ ] All tests pass locally and in CI

## Estimated Timeline

- Phase 1: 4 hours
- Phase 2: 10 hours
- Phase 3: 2 hours
- Phase 4: 1 hour
- **Total: ~17 hours**
