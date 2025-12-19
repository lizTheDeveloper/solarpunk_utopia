import { test, expect } from '@playwright/test';

test.describe('Seed Demo Data (GAP-04)', () => {
  test('should display seeded offers on the offers page', async ({ page }) => {
    await page.goto('/offers');
    
    // Wait for offers to load
    await expect(page.getByText('Loading offers...')).toBeHidden({ timeout: 10000 });
    
    // Should show multiple offers
    const offerCards = page.locator('[class*="grid"] > div');
    await expect(offerCards).toHaveCount({ min: 5 });
    
    // Check for some expected seeded items
    await expect(page.getByText('Tomatoes', { exact: false })).toBeVisible();
    await expect(page.getByText('Carpentry Skills', { exact: false })).toBeVisible();
  });

  test('should display seeded needs on the needs page', async ({ page }) => {
    await page.goto('/needs');
    
    // Wait for needs to load
    await expect(page.getByText('Loading needs...')).toBeHidden({ timeout: 10000 });
    
    // Should show multiple needs
    const needCards = page.locator('[class*="grid"] > div');
    await expect(needCards).toHaveCount({ min: 3 });
  });

  test('should allow filtering seeded offers by category', async ({ page }) => {
    await page.goto('/offers');
    
    await expect(page.getByText('Loading offers...')).toBeHidden({ timeout: 10000 });
    
    // Select food category
    await page.locator('select[class*="w-full"]').nth(1).selectOption('food');
    
    // Should only show food items
    const resultCount = page.getByText(/Showing \d+ offer/);
    await expect(resultCount).toBeVisible();
    
    // Verify food items are visible
    await expect(page.getByText('Tomatoes', { exact: false })).toBeVisible();
  });

  test('should display resource specifications', async ({ page }) => {
    await page.goto('/resources');
    
    // Wait for resource specs to load
    await expect(page.getByText('Loading')).toBeHidden({ timeout: 10000 });
    
    // Should show seeded resource specs
    await expect(page.getByText('Tomatoes')).toBeVisible();
    await expect(page.getByText('Carpentry Skills')).toBeVisible();
    await expect(page.getByText('Bicycle Repair Tools')).toBeVisible();
  });
});
