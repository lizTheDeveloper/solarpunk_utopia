/**
 * Authentication setup for Playwright tests
 *
 * This file creates an authenticated session that can be reused across tests.
 * Run: npx playwright test --project=setup
 */

import { test as setup, expect } from '@playwright/test';
import path from 'path';

const authFile = path.join(__dirname, '../../.auth/user.json');

setup('authenticate', async ({ page }) => {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:4444';

  // Go to login page
  await page.goto(`${BASE_URL}/login`);

  // Fill in test name (simple name-based auth, no password needed)
  await page.fill('#name', 'Test User');

  // Click login button
  await page.click('button[type="submit"]');

  // Wait for redirect to home or onboarding page (indicating successful login)
  // The app might redirect to /onboarding for first-time users or / for returning users
  await page.waitForURL(new RegExp(`${BASE_URL}/(onboarding)?`), { timeout: 10000 });

  // If redirected to onboarding, complete it by clicking through all steps
  const url = page.url();
  if (url.includes('/onboarding')) {
    // Click through onboarding steps using data-testid
    // Keep clicking "next" buttons until we get to the finish button
    let maxSteps = 10; // Safety limit
    while (maxSteps > 0) {
      maxSteps--;

      const nextButton = page.locator('[data-testid="onboarding-next"]');
      const finishButton = page.locator('[data-testid="onboarding-finish"]');

      // Check if we're on the last step
      if (await finishButton.isVisible({ timeout: 500 }).catch(() => false)) {
        await finishButton.click();
        break;
      }

      // Otherwise click next
      if (await nextButton.isVisible({ timeout: 500 }).catch(() => false)) {
        await nextButton.click();
        await page.waitForTimeout(300); // Brief wait for transition
      } else {
        // No more buttons, we're done
        break;
      }
    }

    // Wait for redirect to home
    await page.waitForURL(`${BASE_URL}/`, { timeout: 10000 });
  }

  // Verify we're logged in - should be on home page or have navigation visible
  await expect(page.locator('nav, header')).toBeVisible({ timeout: 5000 });

  // Save authentication state
  await page.context().storageState({ path: authFile });
});
