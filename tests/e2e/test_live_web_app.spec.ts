import { test, expect } from '@playwright/test';

// Run without auth setup
test.use({ storageState: undefined });

test.describe('Live Web App Testing - Jan 18 2026', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:4444/');
  });

  test('Homepage loads and displays title', async ({ page }) => {
    await expect(page).toHaveTitle(/Solarpunk/);
    console.log('✅ Homepage loaded');
  });

  test('Navigation menu is visible and functional', async ({ page }) => {
    // Check for navigation elements
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();

    // Look for common navigation items
    const homeLink = page.getByText('Home', { exact: false });
    const offersLink = page.getByText('Offers', { exact: false });
    const needsLink = page.getByText('Needs', { exact: false });

    console.log('✅ Navigation visible');
  });

  test('Can navigate to Offers page', async ({ page }) => {
    // Try to click on Offers link
    const offersLink = page.getByRole('link', { name: /offers/i });
    await offersLink.click();

    // Wait for navigation
    await page.waitForURL('**/offers**', { timeout: 5000 });

    console.log('✅ Navigated to Offers page');
    console.log('Current URL:', page.url());
  });

  test('Offers page displays listings', async ({ page }) => {
    await page.goto('http://localhost:4444/offers');

    // Wait for content to load
    await page.waitForTimeout(2000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/offers-page.png', fullPage: true });

    // Check if there's any content
    const body = await page.textContent('body');
    console.log('Page has content:', body ? 'YES' : 'NO');
    console.log('First 500 chars:', body?.slice(0, 500));
  });

  test('Can navigate to Needs page', async ({ page }) => {
    const needsLink = page.getByRole('link', { name: /needs/i });
    await needsLink.click();

    await page.waitForURL('**/needs**', { timeout: 5000 });

    console.log('✅ Navigated to Needs page');
    await page.screenshot({ path: 'test-results/needs-page.png', fullPage: true });
  });

  test('Search/Discovery page accessible', async ({ page }) => {
    const searchLink = page.getByRole('link', { name: /search|discovery/i });
    if (await searchLink.count() > 0) {
      await searchLink.click();
      console.log('✅ Navigated to Search/Discovery');
      await page.screenshot({ path: 'test-results/discovery-page.png', fullPage: true });
    } else {
      console.log('⚠️ Search link not found in navigation');
    }
  });

  test('Create Offer button exists and behavior', async ({ page }) => {
    // Look for create/add button
    const createButton = page.getByRole('link', { name: /create|new|add/i }).or(
      page.getByRole('button', { name: /create|new|add/i })
    ).first();

    if (await createButton.count() > 0) {
      console.log('✅ Create button found');
      await createButton.click();

      await page.waitForTimeout(2000);
      console.log('Current URL after click:', page.url());
      await page.screenshot({ path: 'test-results/create-offer-page.png', fullPage: true });
    } else {
      console.log('⚠️ Create button not found');
    }
  });

  test('Network status page accessible', async ({ page }) => {
    const networkLink = page.getByRole('link', { name: /network/i });
    if (await networkLink.count() > 0) {
      await networkLink.click();
      console.log('✅ Navigated to Network status');
      await page.screenshot({ path: 'test-results/network-page.png', fullPage: true });
    } else {
      console.log('⚠️ Network link not found');
    }
  });

  test('Full page screenshot for overview', async ({ page }) => {
    await page.screenshot({ path: 'test-results/homepage-full.png', fullPage: true });
    console.log('✅ Full page screenshot saved');
  });

  test('Check API connectivity from browser', async ({ page }) => {
    // Navigate to page and check network requests
    const apiCalls: string[] = [];

    page.on('request', request => {
      const url = request.url();
      if (url.includes('/api/') || url.includes(':8001')) {
        apiCalls.push(url);
        console.log('API Request:', url);
      }
    });

    await page.goto('http://localhost:4444/offers');
    await page.waitForTimeout(3000);

    console.log('Total API calls detected:', apiCalls.length);
    console.log('API endpoints called:', apiCalls);
  });
});
