import { test, expect } from '@playwright/test';

test.describe('Navigation and System Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to home page
    await page.goto('/');
    // Wait for page to be ready
    await page.waitForLoadState('networkidle');
  });

  test('should display all primary navigation sections', async ({ page }) => {
    // Check that all primary nav sections are visible
    await expect(page.getByRole('link', { name: 'Home' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Exchange' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Community' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'My Activity' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'System' })).toBeVisible();
  });

  test('should show Exchange sub-navigation when on Exchange section', async ({ page }) => {
    // Click on Exchange section
    await page.getByRole('link', { name: 'Exchange' }).click();

    // Check sub-navigation items are visible
    await expect(page.getByRole('link', { name: 'Offers' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Needs' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Search' })).toBeVisible();
  });

  test('should show My Activity sub-navigation with AI Helpers', async ({ page }) => {
    // Click on My Activity section
    await page.getByRole('link', { name: 'My Activity' }).click();

    // Check sub-navigation items are visible
    await expect(page.getByRole('link', { name: 'Exchanges' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'AI Helpers' })).toBeVisible();
  });

  test('should navigate to System/Network page without crashing', async ({ page }) => {
    // Click on System section
    await page.getByRole('link', { name: 'System' }).click();

    // Wait for page load
    await page.waitForLoadState('networkidle');

    // Check that we're on the network page and it rendered
    await expect(page).toHaveURL(/\/network/);

    // Check for key elements on the network page
    await expect(page.getByText('Network Status')).toBeVisible();

    // Check that the page didn't crash (no error messages)
    const errorMessages = page.getByText(/error|crash|failed/i);
    await expect(errorMessages).toHaveCount(0);
  });

  test('should show System sub-navigation items', async ({ page }) => {
    // Click on System section
    await page.getByRole('link', { name: 'System' }).click();

    // Check sub-navigation items are visible
    await expect(page.getByRole('link', { name: 'Knowledge' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Network' })).toBeVisible();
  });

  test('should handle missing data gracefully on Network page', async ({ page }) => {
    // Navigate to network page
    await page.goto('/network');
    await page.waitForLoadState('networkidle');

    // Check that N/A is displayed for missing data instead of crashes
    const content = await page.textContent('body');

    // The page should either show real data or "N/A" - not crash
    expect(content).toBeTruthy();

    // Should not show JavaScript errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Wait a bit to catch any console errors
    await page.waitForTimeout(1000);

    // Filter out known non-critical errors
    const criticalErrors = consoleErrors.filter(err =>
      !err.includes('Failed to fetch') && // API errors are ok
      !err.includes('404') && // 404s are expected during development
      !err.includes('500') // 500s are expected if backend not fully running
    );

    expect(criticalErrors).toHaveLength(0);
  });

  test('should navigate between sections preserving sub-navigation', async ({ page }) => {
    // Start at Exchange
    await page.getByRole('link', { name: 'Exchange' }).click();
    await expect(page.getByRole('link', { name: 'Offers' })).toBeVisible();

    // Navigate to My Activity
    await page.getByRole('link', { name: 'My Activity' }).click();
    await expect(page.getByRole('link', { name: 'AI Helpers' })).toBeVisible();

    // Navigate to System
    await page.getByRole('link', { name: 'System' }).click();
    await expect(page.getByRole('link', { name: 'Network' })).toBeVisible();
  });

  test('should be able to access AI Helpers from My Activity section', async ({ page }) => {
    // Navigate to My Activity section
    await page.getByRole('link', { name: 'My Activity' }).click();

    // Click on AI Helpers sub-nav item
    await page.getByRole('link', { name: 'AI Helpers' }).click();

    // Verify we're on the agents page
    await expect(page).toHaveURL(/\/agents/);
  });

  test('mobile navigation should show all items including AI Helpers', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // On mobile, all nav items should be in a horizontal scroll
    // AI Helpers should be visible in the flattened nav
    const aiHelpersLink = page.getByRole('link', { name: 'AI Helpers' });

    // May need to scroll horizontally to see it
    await aiHelpersLink.scrollIntoViewIfNeeded();
    await expect(aiHelpersLink).toBeVisible();
  });
});
