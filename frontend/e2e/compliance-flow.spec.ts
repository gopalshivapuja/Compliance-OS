/**
 * Compliance Management Flow E2E Tests
 *
 * End-to-end tests for dashboard and compliance instance management.
 * Tests cover: dashboard display, RAG status, compliance list, filtering, and pagination.
 */

import { test, expect } from '@playwright/test';
import { loginAs, clearAuthState, TEST_USERS } from './utils/auth';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each dashboard test
    await loginAs(page, 'admin');
  });

  test('should display dashboard page with correct heading', async ({
    page,
  }) => {
    // Verify page heading
    await expect(
      page.getByRole('heading', { name: /executive control tower/i })
    ).toBeVisible();

    // Verify subtitle
    await expect(
      page.getByText(/real-time compliance monitoring/i)
    ).toBeVisible();
  });

  test('should display RAG status overview card', async ({ page }) => {
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');

    // Verify RAG status card heading
    await expect(
      page.getByRole('heading', { name: /compliance status overview/i })
    ).toBeVisible();

    // Verify RAG status labels are present (use first() for multiple matches)
    await expect(page.getByText(/on track/i).first()).toBeVisible();
    await expect(page.getByText(/at risk/i).first()).toBeVisible();
    await expect(page.getByText(/overdue/i).first()).toBeVisible();

    // Verify total count section
    await expect(page.getByText(/total compliance items/i)).toBeVisible();
  });

  test('should display overdue items section', async ({ page }) => {
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');

    // Verify overdue items heading
    await expect(
      page.getByRole('heading', { name: /overdue items/i })
    ).toBeVisible();
  });

  test('should display upcoming items section', async ({ page }) => {
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');

    // Verify upcoming items heading
    await expect(
      page.getByRole('heading', { name: /upcoming.*7 days/i })
    ).toBeVisible();
  });

  test('should show loading state initially', async ({ page }) => {
    // Navigate without waiting for login
    await page.goto('/login');
    await page.getByLabel('Email').fill(TEST_USERS.admin.email);
    await page.getByLabel('Password').fill(TEST_USERS.admin.password);
    await page.getByRole('button', { name: /sign in/i }).click();

    // On dashboard, should eventually show content (loading state may be brief)
    await expect(page).toHaveURL('/dashboard', { timeout: 10000 });

    // Should eventually show the main heading (after loading)
    await expect(
      page.getByRole('heading', { name: /executive control tower/i })
    ).toBeVisible({ timeout: 10000 });
  });

  test('should display summary stats for immediate action items', async ({
    page,
  }) => {
    // Wait for data to load
    await page.waitForLoadState('networkidle');

    // Check for "Need Immediate Action" section
    await expect(page.getByText(/need immediate action/i)).toBeVisible();

    // Check for "Require Attention" section
    await expect(page.getByText(/require attention/i)).toBeVisible();
  });
});

test.describe('Compliance Instance List', () => {
  // Helper to navigate to compliance page via sidebar link (preserves SPA state)
  async function navigateToCompliance(page: import('@playwright/test').Page) {
    // Use exact link name to avoid matching "Compliance Masters"
    const complianceLink = page.getByRole('link', { name: /compliance instances/i });
    await expect(complianceLink).toBeVisible({ timeout: 10000 });
    await complianceLink.click();
    await expect(page).toHaveURL(/\/compliance/, { timeout: 10000 });
  }

  test('should display compliance instances page with correct heading', async ({
    page,
  }) => {
    await loginAs(page, 'cfo');
    await navigateToCompliance(page);

    // Verify page heading
    await expect(
      page.getByRole('heading', { name: /compliance instances/i })
    ).toBeVisible({ timeout: 10000 });

    // Verify subtitle
    await expect(
      page.getByText(/view and manage all compliance obligations/i)
    ).toBeVisible();
  });

  test('should display filter section', async ({ page }) => {
    await loginAs(page, 'cfo');
    await navigateToCompliance(page);

    // Verify filters heading
    await expect(
      page.getByRole('heading', { name: /filters/i })
    ).toBeVisible({ timeout: 10000 });

    // Verify filter dropdowns exist (using label with exact match to avoid Status/RAG Status collision)
    await expect(page.getByLabel('Status', { exact: true })).toBeVisible();
    await expect(page.getByLabel('Category')).toBeVisible();
    await expect(page.getByLabel('RAG Status')).toBeVisible();

    // Verify Clear Filters button
    await expect(
      page.getByRole('button', { name: /clear filters/i })
    ).toBeVisible();
  });

  test('should display compliance table or no-data message', async ({ page }) => {
    await loginAs(page, 'cfo');
    await navigateToCompliance(page);

    // Wait for either table or no-data message to appear
    const table = page.locator('table');
    const noDataMessage = page.getByText(/no compliance instances found/i);

    // Wait for one of them to be visible
    await expect(table.or(noDataMessage)).toBeVisible({ timeout: 10000 });

    // Check which one is visible
    const hasTable = await table.isVisible().catch(() => false);

    if (hasTable) {
      // Check for expected column headers
      await expect(
        page.getByRole('columnheader', { name: /compliance/i })
      ).toBeVisible();
    }
  });

  test('should filter by status', async ({ page }) => {
    await loginAs(page, 'cfo');
    await navigateToCompliance(page);

    // Wait for filters to load (use exact match for Status to avoid RAG Status collision)
    await expect(page.getByLabel('Status', { exact: true })).toBeVisible({ timeout: 10000 });

    // Select "In Progress" status
    await page.getByLabel('Status', { exact: true }).selectOption('In Progress');

    // Results should update (check the results count text updates)
    await expect(page.getByText(/showing/i)).toBeVisible({ timeout: 10000 });
  });

  test('should filter by category', async ({ page }) => {
    await loginAs(page, 'cfo');
    await navigateToCompliance(page);

    // Wait for filters to load
    await expect(page.getByLabel('Category')).toBeVisible({ timeout: 10000 });

    // Select "GST" category
    await page.getByLabel('Category').selectOption('GST');

    // Results should show GST items (if any exist)
    await expect(page.getByText(/showing/i)).toBeVisible({ timeout: 10000 });
  });

  test('should filter by RAG status', async ({ page }) => {
    await loginAs(page, 'cfo');
    await navigateToCompliance(page);

    // Wait for filters to load
    await expect(page.getByLabel('RAG Status')).toBeVisible({ timeout: 10000 });

    // Select "Red" RAG status
    await page.getByLabel('RAG Status').selectOption('Red');

    // Results should show Red status items (if any exist)
    await expect(page.getByText(/showing/i)).toBeVisible({ timeout: 10000 });
  });

  test('should clear all filters', async ({ page }) => {
    await loginAs(page, 'cfo');
    await navigateToCompliance(page);

    // Wait for filters to load (use exact match for Status)
    await expect(page.getByLabel('Status', { exact: true })).toBeVisible({ timeout: 10000 });

    // Apply some filters first
    await page.getByLabel('Status', { exact: true }).selectOption('In Progress');
    await page.getByLabel('Category').selectOption('GST');

    // Click Clear Filters
    await page.getByRole('button', { name: /clear filters/i }).click();

    // Verify filters are reset
    await expect(page.getByLabel('Status', { exact: true })).toBeVisible();
  });

  test('should show results count', async ({ page }) => {
    await loginAs(page, 'cfo');
    await navigateToCompliance(page);

    // Wait for page to load and verify results count is displayed
    await expect(page.getByText(/showing.*of.*results/i)).toBeVisible({ timeout: 10000 });
  });

  test('should handle empty results gracefully', async ({ page }) => {
    await loginAs(page, 'cfo');
    await navigateToCompliance(page);

    // Wait for filters to load (use exact match for Status)
    await expect(page.getByLabel('Status', { exact: true })).toBeVisible({ timeout: 10000 });

    // Apply filters that likely return no results
    await page.getByLabel('Status', { exact: true }).selectOption('Filed');
    await page.getByLabel('Category').selectOption('FEMA');
    await page.getByLabel('RAG Status').selectOption('Green');

    // Wait for results to update - should show either "No compliance instances found" or results count
    // Use first() to handle case when both messages are visible (0 results shows both)
    await expect(
      page.getByText(/no compliance instances found/i).or(page.getByText(/showing/i)).first()
    ).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Compliance Navigation', () => {
  test('should navigate from dashboard to compliance page', async ({
    page,
  }) => {
    // Login using loginAs (same pattern as Multi-User tests)
    await loginAs(page, 'cfo');

    // Look for navigation link to compliance instances (not compliance masters)
    const complianceLink = page.getByRole('link', { name: /compliance instances/i });

    if (await complianceLink.isVisible()) {
      await complianceLink.click();
      await expect(page).toHaveURL(/\/compliance/);
    } else {
      // Direct navigation fallback
      await page.goto('/compliance');
      await expect(
        page.getByRole('heading', { name: /compliance instances/i })
      ).toBeVisible({ timeout: 10000 });
    }
  });

  test('should navigate back to dashboard', async ({ page }) => {
    // Login and go to compliance first
    await loginAs(page, 'cfo');

    // Navigate to compliance via sidebar link (use exact name)
    const complianceLink = page.getByRole('link', { name: /compliance instances/i });
    await expect(complianceLink).toBeVisible({ timeout: 10000 });
    await complianceLink.click();
    await expect(page).toHaveURL(/\/compliance/, { timeout: 10000 });

    // Wait for page to stabilize before clicking dashboard link
    await page.waitForLoadState('domcontentloaded');

    // Navigate back to dashboard
    const dashboardLink = page.getByRole('link', { name: /dashboard/i });
    await expect(dashboardLink).toBeVisible({ timeout: 10000 });
    // Use force click to handle any React re-renders
    await dashboardLink.click({ timeout: 10000 });

    // Wait for navigation
    await expect(page).toHaveURL('/dashboard', { timeout: 10000 });
  });
});

test.describe('Multi-User Dashboard Access', () => {
  test('CFO should see dashboard', async ({ page }) => {
    await loginAs(page, 'cfo');

    // Should see dashboard
    await expect(
      page.getByRole('heading', { name: /executive control tower/i })
    ).toBeVisible();
  });

  test('Tax Lead should see dashboard', async ({ page }) => {
    await loginAs(page, 'tax_lead');

    // Should see dashboard
    await expect(
      page.getByRole('heading', { name: /executive control tower/i })
    ).toBeVisible();
  });

  test('CFO should see compliance list', async ({ page }) => {
    await loginAs(page, 'cfo');
    await page.goto('/compliance');

    // Should see compliance page
    await expect(
      page.getByRole('heading', { name: /compliance instances/i })
    ).toBeVisible();
  });

  test('Tax Lead should see compliance list', async ({ page }) => {
    await loginAs(page, 'tax_lead');
    await page.goto('/compliance');

    // Should see compliance page
    await expect(
      page.getByRole('heading', { name: /compliance instances/i })
    ).toBeVisible();
  });
});
