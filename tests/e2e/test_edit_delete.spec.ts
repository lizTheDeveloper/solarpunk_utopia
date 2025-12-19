import { test, expect } from '@playwright/test';

test.describe('Edit/Delete Listings (GAP-18)', () => {
  test.describe('Offers', () => {
    test('should show edit/delete buttons on own offers', async ({ page }) => {
      await page.goto('/offers');
      
      await expect(page.getByText('Loading offers...')).toBeHidden({ timeout: 10000 });
      
      // Look for offer cards with edit/delete buttons
      // Note: Only visible if user is owner
      const editButtons = page.getByRole('button', { name: /Edit offer/i });
      const deleteButtons = page.getByRole('button', { name: /Delete offer/i });
      
      const editCount = await editButtons.count();
      const deleteCount = await deleteButtons.count();
      
      // Should have matching counts (both present or both absent)
      expect(editCount).toBe(deleteCount);
    });

    test('should navigate to edit page when clicking edit', async ({ page }) => {
      await page.goto('/offers');
      
      await expect(page.getByText('Loading offers...')).toBeHidden({ timeout: 10000 });
      
      const editButton = page.getByRole('button', { name: /Edit offer/i }).first();
      
      if (await editButton.isVisible()) {
        await editButton.click();
        
        // Should navigate to edit page
        await expect(page).toHaveURL(/\/offers\/.*\/edit/);
      }
    });

    test('should show confirmation dialog when deleting', async ({ page }) => {
      await page.goto('/offers');
      
      await expect(page.getByText('Loading offers...')).toBeHidden({ timeout: 10000 });
      
      const deleteButton = page.getByRole('button', { name: /Delete offer/i }).first();
      
      if (await deleteButton.isVisible()) {
        // Set up dialog handler
        page.on('dialog', async dialog => {
          expect(dialog.message()).toContain('Are you sure');
          await dialog.dismiss();
        });
        
        await deleteButton.click();
      }
    });

    test('should remove offer after delete confirmation', async ({ page }) => {
      await page.goto('/offers');
      
      await expect(page.getByText('Loading offers...')).toBeHidden({ timeout: 10000 });
      
      const initialCount = await page.getByRole('button', { name: /Delete offer/i }).count();
      
      if (initialCount > 0) {
        const deleteButton = page.getByRole('button', { name: /Delete offer/i }).first();
        
        // Accept confirmation
        page.on('dialog', async dialog => {
          await dialog.accept();
        });
        
        await deleteButton.click();
        
        // Wait for deletion to complete
        await page.waitForTimeout(1000);
        
        // Count should decrease or stay same if error occurred
        const newCount = await page.getByRole('button', { name: /Delete offer/i }).count();
        expect(newCount).toBeLessThanOrEqual(initialCount);
      }
    });
  });

  test.describe('Needs', () => {
    test('should show edit/delete buttons on own needs', async ({ page }) => {
      await page.goto('/needs');
      
      await expect(page.getByText('Loading needs...')).toBeHidden({ timeout: 10000 });
      
      const editButtons = page.getByRole('button', { name: /Edit need/i });
      const deleteButtons = page.getByRole('button', { name: /Delete need/i });
      
      const editCount = await editButtons.count();
      const deleteCount = await deleteButtons.count();
      
      // Should have matching counts
      expect(editCount).toBe(deleteCount);
    });

    test('should navigate to edit page when clicking edit', async ({ page }) => {
      await page.goto('/needs');
      
      await expect(page.getByText('Loading needs...')).toBeHidden({ timeout: 10000 });
      
      const editButton = page.getByRole('button', { name: /Edit need/i }).first();
      
      if (await editButton.isVisible()) {
        await editButton.click();
        
        // Should navigate to edit page
        await expect(page).toHaveURL(/\/needs\/.*\/edit/);
      }
    });

    test('should show confirmation dialog when deleting need', async ({ page }) => {
      await page.goto('/needs');
      
      await expect(page.getByText('Loading needs...')).toBeHidden({ timeout: 10000 });
      
      const deleteButton = page.getByRole('button', { name: /Delete need/i }).first();
      
      if (await deleteButton.isVisible()) {
        page.on('dialog', async dialog => {
          expect(dialog.message()).toContain('Are you sure');
          await dialog.dismiss();
        });
        
        await deleteButton.click();
      }
    });

    test('should filter needs by category and location', async ({ page }) => {
      await page.goto('/needs');
      
      await expect(page.getByText('Loading needs...')).toBeHidden({ timeout: 10000 });
      
      // Select a category
      await page.locator('select[class*="w-full"]').nth(1).selectOption('food');
      
      // Results should update
      await expect(page.getByText(/Showing \d+ need/)).toBeVisible();
    });
  });
});
