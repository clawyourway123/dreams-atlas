import { test, expect } from '@playwright/test';

test.describe('DreaMS Atlas Smoke Tests', () => {
  test('homepage loads and has title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/DreaMS|Atlas/i);
    await expect(page.locator('body')).toBeVisible();
  });

  test('explore page loads', async ({ page }) => {
    await page.goto('/explore');
    await expect(page).toHaveURL(/explore/);
    await expect(page.locator('body')).toBeVisible();
  });

  test('technology page loads', async ({ page }) => {
    await page.goto('/technology');
    await expect(page).toHaveURL(/technology/);
    await expect(page.locator('body')).toBeVisible();
  });

  test('team page loads', async ({ page }) => {
    await page.goto('/team');
    await expect(page).toHaveURL(/team/);
    await expect(page.locator('body')).toBeVisible();
  });

  test('contact page loads', async ({ page }) => {
    await page.goto('/contact');
    await expect(page).toHaveURL(/contact/);
    await expect(page.locator('body')).toBeVisible();
  });

  test('API health endpoint responds', async ({ request }) => {
    const apiUrl = process.env.API_URL || 'http://localhost:8000';
    const response = await request.get(`${apiUrl}/healthz`);
    expect(response.ok()).toBeTruthy();
  });

  test('navigation between pages works', async ({ page }) => {
    await page.goto('/');
    const nav = page.locator('nav');
    if (await nav.isVisible()) {
      const links = nav.locator('a');
      const count = await links.count();
      expect(count).toBeGreaterThan(0);
    }
  });
});
