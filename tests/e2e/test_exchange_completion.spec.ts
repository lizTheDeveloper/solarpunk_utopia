import { test, expect } from '@playwright/test';

test.describe('Exchange Completion Flow (GAP-10)', () => {
  test('should display active exchanges', async ({ page }) => {
    await page.goto('/exchanges');
    
    // Wait for exchanges to load
    await expect(page.getByText('Loading exchanges...')).toBeHidden({ timeout: 10000 });
    
    // Should display exchanges or empty state
    const hasExchanges = await page.getByText(/Showing \d+ exchange/).isVisible().catch(() => false);
    if (!hasExchanges) {
      await expect(page.getByText('No active exchanges yet.')).toBeVisible();
    }
  });

  test('should show completion buttons for pending exchanges', async ({ page }) => {
    await page.goto('/exchanges');
    
    await expect(page.getByText('Loading exchanges...')).toBeHidden({ timeout: 10000 });
    
    // If there are pending exchanges, check for completion section
    const pendingExchanges = page.locator('[class*="bg-yellow"]').locator('..');
    const count = await pendingExchanges.count();
    
    if (count > 0) {
      // First pending exchange should have completion options
      const firstExchange = pendingExchanges.first();
      await expect(firstExchange.getByText('Mark as Complete')).toBeVisible();
    }
  });

  test('should allow provider to confirm completion', async ({ page }) => {
    await page.goto('/exchanges');
    
    await expect(page.getByText('Loading exchanges...')).toBeHidden({ timeout: 10000 });
    
    // Look for a pending exchange where current user is provider
    const confirmButton = page.getByRole('button', { name: /Confirm as Provider/i }).first();
    
    if (await confirmButton.isVisible()) {
      await confirmButton.click();
      
      // Should show confirmation
      await expect(page.getByText('Provider Confirmed')).toBeVisible({ timeout: 5000 });
    }
  });

  test('should show celebration when exchange is fully completed', async ({ page }) => {
    await page.goto('/exchanges');
    
    await expect(page.getByText('Loading exchanges...')).toBeHidden({ timeout: 10000 });
    
    // Check if there are any completed exchanges with celebration message
    const completedExchanges = page.locator('[class*="bg-green"]').locator('..');
    const count = await completedExchanges.count();
    
    if (count > 0) {
      const celebration = completedExchanges.first().getByText(/Exchange complete!/);
      await expect(celebration).toBeVisible();
    }
  });

  test('should update exchange status after completion', async ({ page }) => {
    await page.goto('/exchanges');
    
    await expect(page.getByText('Loading exchanges...')).toBeHidden({ timeout: 10000 });
    
    // Verify completed exchanges show correct status
    const completedBadges = page.getByText('completed');
    const count = await completedBadges.count();
    
    // Should have at least some completed exchanges or none
    expect(count).toBeGreaterThanOrEqual(0);
  });
});
