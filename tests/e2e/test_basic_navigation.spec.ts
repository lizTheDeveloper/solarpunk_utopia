import { test, expect } from '@playwright/test';

test.describe('Basic Navigation (No Auth)', () => {
  test('should load homepage and show basic UI', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Should have a title
    await expect(page).toHaveTitle(/Solarpunk/i);

    // Page should render without crashes
    const body = await page.locator('body');
    await expect(body).toBeVisible();
  });

  test('should handle node configuration or show navigation', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait a bit for redirects
    await page.waitForTimeout(1000);

    // Either we see the node config page OR the navigation
    const hasNodeConfig = await page.locator('text=Configure Your Node').isVisible().catch(() => false);
    const hasNavigation = await page.locator('nav').isVisible().catch(() => false);

    // One of them should be visible
    expect(hasNodeConfig || hasNavigation).toBeTruthy();
  });

  test('should navigate to network page without crashing', async ({ page }) => {
    await page.goto('/network');
    await page.waitForLoadState('networkidle');

    // Wait for any redirects
    await page.waitForTimeout(1000);

    // Check for console errors (critical ones)
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Wait a bit to catch console errors
    await page.waitForTimeout(2000);

    // Filter out expected errors (API failures, etc)
    const criticalErrors = consoleErrors.filter(err =>
      err.includes('RangeError') ||
      err.includes('TypeError') ||
      err.includes('slice is not a function') ||
      err.includes('Invalid time value')
    );

    // Should not have critical JavaScript errors
    expect(criticalErrors).toHaveLength(0);
  });
});

test.describe('Navigation with Mock Config', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the node config API to say we're configured
    await page.route('**/api/node/config/status', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ configured: true })
      });
    });

    // Mock a successful config response
    await page.route('**/api/node/config', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          mesh_name: 'test-mesh',
          description: 'Test mesh network',
          enable_ai_inference: false,
          enable_bridge: false
        })
      });
    });
  });

  test('should display all primary navigation sections', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check that navigation is visible
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();

    // Check for key nav items
    const hasHome = await page.getByText('Home').isVisible().catch(() => false);
    const hasExchange = await page.getByText('Exchange').isVisible().catch(() => false);

    expect(hasHome || hasExchange).toBeTruthy();
  });

  test('should navigate to network page and show network status', async ({ page }) => {
    // Mock network status API
    await page.route('**/api/network/status', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          node_id: 'test-node-123456789',
          current_island_id: 'island-abc123',
          mode: 'A',
          connected_to_internet: true,
          active_bridges: 2,
          bundles_in_outbox: 5,
          known_islands: 3,
          last_bridge_contact: new Date().toISOString()
        })
      });
    });

    await page.goto('/network');
    await page.waitForLoadState('networkidle');

    // Should show network status heading
    await expect(page.getByText('Network Status')).toBeVisible();

    // Should show mode
    const hasMode = await page.getByText('Mode').isVisible().catch(() => false);
    expect(hasMode).toBeTruthy();
  });

  test('should handle missing network data gracefully', async ({ page }) => {
    // Mock network status with minimal data
    await page.route('**/api/network/status', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          node_id: null,
          current_island_id: null,
          mode: 'A',
          connected_to_internet: false,
          active_bridges: 0,
          bundles_in_outbox: 0,
          known_islands: 0,
          last_bridge_contact: null
        })
      });
    });

    await page.goto('/network');
    await page.waitForLoadState('networkidle');

    // Page should still render
    await expect(page.getByText('Network Status')).toBeVisible();

    // Should show N/A for missing data instead of crashing
    const pageContent = await page.textContent('body');
    expect(pageContent).toContain('N/A');

    // No JavaScript errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.waitForTimeout(1000);

    const criticalErrors = consoleErrors.filter(err =>
      err.includes('RangeError') ||
      err.includes('TypeError') ||
      err.includes('slice is not a function')
    );

    expect(criticalErrors).toHaveLength(0);
  });
});
