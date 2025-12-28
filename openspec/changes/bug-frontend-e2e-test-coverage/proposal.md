# Frontend E2E Test Coverage

**Status:** Draft
**Priority:** Medium
**Component:** Frontend Testing
**Source:** USER_TESTING_REVIEW_2025-12-22.md Section 10.3, Opportunity 1

## Problem Statement

The frontend currently has partial E2E test coverage, which reduces confidence in full-stack functionality. While Playwright configuration exists, comprehensive end-to-end tests are not implemented.

**Impact:**
- Integration bugs may not be caught before deployment
- Manual testing burden increases with each feature
- Regression risk when making changes to critical user flows
- Reduced confidence in production deployments

**Evidence from Review:**
```
Frontend: 🟡 Beta Quality
- ⚠️ E2E test coverage incomplete

Testing Completeness Matrix:
| Frontend | ⚠️ Partial | ⚠️ Partial | ⚠️ Partial | 🟡 Needs Work |

Enhancement Opportunity 1: Frontend Integration Testing
- Add E2E tests for frontend application
- Playwright configuration exists but tests not comprehensive
- Would improve confidence in full-stack functionality
```

## Requirements

### Critical User Flows (MUST be tested)

1. **User Authentication Flow**
   - WHEN a new user visits the site
   - THEN they SHALL be redirected to onboarding
   - AND they MUST be able to complete the onboarding process
   - AND they SHALL be redirected to the home page upon completion

2. **Offer Creation Flow**
   - WHEN a user creates an offer
   - THEN the offer MUST appear in the offers list
   - AND the user MUST be able to edit the offer
   - AND the user MUST be able to delete the offer

3. **Need Creation Flow**
   - WHEN a user creates a need
   - THEN the need MUST appear in the needs list
   - AND the user MUST be able to edit the need
   - AND the user MUST be able to delete the need

4. **Community Selection Flow**
   - WHEN a user has no community selected
   - THEN they SHALL see empty state with call-to-action
   - AND they MUST be able to browse communities
   - AND they MUST be able to join a community
   - AND the offers/needs SHALL update to show community content

5. **Filtering and Search**
   - WHEN a user filters offers by category
   - THEN only matching offers SHALL be displayed
   - AND the count MUST update correctly
   - WHEN a user searches for a term
   - THEN only matching results SHALL be displayed

### Test Infrastructure (MUST implement)

1. **Test Data Management**
   - Test database seeding with realistic data
   - Cleanup between test runs
   - Isolated test environments

2. **Mock Services**
   - Mock authentication for test users
   - Mock community data
   - Mock offer/need data

3. **Assertions**
   - Visual regression testing (screenshots)
   - Accessibility testing (ARIA labels)
   - Performance testing (page load times)

### Test Organization (SHOULD implement)

1. **Test Structure**
   - Page object models for maintainability
   - Reusable test fixtures
   - Clear test naming conventions

2. **CI/CD Integration**
   - Tests run automatically on PR
   - Tests block merge if failing
   - Test reports visible in CI

## Success Criteria

- [ ] At least 5 critical user flows have comprehensive E2E tests
- [ ] Tests run successfully in CI/CD pipeline
- [ ] Test coverage report shows >80% of critical paths tested
- [ ] All tests pass consistently (no flaky tests)
- [ ] Test documentation added to frontend/tests/README.md

## Non-Goals

- Unit test coverage (separate concern)
- Backend API testing (covered by backend tests)
- Performance benchmarking (separate concern)

## Dependencies

- Playwright already configured in `frontend/playwright.config.ts`
- Backend services must be running for tests
- Test database seeding scripts

## Acceptance Tests

### Scenario 1: Offer Creation E2E
```
GIVEN a logged-in user
WHEN they navigate to /offers/create
AND they fill in the title "Fresh Tomatoes"
AND they enter quantity "5" and unit "kg"
AND they click "Create Offer"
THEN they are redirected to /offers
AND they see "Fresh Tomatoes" in the offers list
AND they see a success toast notification
```

### Scenario 2: Community Selection Impact
```
GIVEN a user with no community selected
WHEN they view /offers
THEN they see "No Community Selected" message
WHEN they click "Browse Communities"
AND they select a community
AND they navigate back to /offers
THEN they see offers from that community
```

### Scenario 3: Edit and Delete Flow
```
GIVEN a user with an existing offer
WHEN they click "Edit" on their offer
AND they update the quantity to "10"
AND they click "Save"
THEN the offer shows the new quantity
WHEN they click "Delete" on the offer
AND they confirm the deletion
THEN the offer no longer appears in the list
```

## Implementation Notes

**Files to Create:**
- `frontend/tests/e2e/auth.spec.ts`
- `frontend/tests/e2e/offers.spec.ts`
- `frontend/tests/e2e/needs.spec.ts`
- `frontend/tests/e2e/community.spec.ts`
- `frontend/tests/e2e/search-filter.spec.ts`
- `frontend/tests/helpers/test-data.ts`
- `frontend/tests/helpers/page-objects.ts`

**Example Test Structure:**
```typescript
// frontend/tests/e2e/offers.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Offer Creation', () => {
  test('should create an offer successfully', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');

    // Create offer
    await page.goto('/offers/create');
    await page.fill('[name="title"]', 'Fresh Tomatoes');
    await page.fill('[name="quantity"]', '5');
    await page.selectOption('[name="unit"]', 'kg');
    await page.click('button[type="submit"]');

    // Verify
    await expect(page).toHaveURL('/offers');
    await expect(page.locator('text=Fresh Tomatoes')).toBeVisible();
  });
});
```

## Estimated Effort

- Test infrastructure setup: 4 hours
- Critical flow tests (5 flows × 2 hours): 10 hours
- CI/CD integration: 2 hours
- Documentation: 1 hour

**Total: ~17 hours**

## Related Issues

- UI_TESTING_REPORT_2025-12-26.md - All 10 bugs should be validated by E2E tests after fixes
- Frontend currently at "Beta Quality" per review section 12.2
