/**
 * Authentication utilities for E2E tests
 *
 * Provides helper functions for login/logout flows and test user management.
 */

import { Page } from '@playwright/test';

/**
 * Test user credentials for E2E testing.
 * These users are created by running: python create_test_user.py
 */
export const TEST_USERS = {
  admin: {
    email: 'admin@testgcc.com',
    password: 'Admin123!', // pragma: allowlist secret
    role: 'System Administrator',
  },
  cfo: {
    email: 'cfo@testgcc.com',
    password: 'CFO12345!', // pragma: allowlist secret
    role: 'CFO / Approver',
  },
  tax_lead: {
    email: 'tax@testgcc.com',
    password: 'Tax12345!', // pragma: allowlist secret
    role: 'Tax Lead',
  },
} as const;

export type TestUserType = keyof typeof TEST_USERS;

/**
 * Login as a specific test user.
 *
 * @param page - Playwright page object
 * @param userType - Type of user to login as (admin, cfo, or tax_lead)
 * @param options - Optional settings
 * @param options.waitForDashboard - Whether to wait for dashboard to load (default: true)
 */
export async function loginAs(
  page: Page,
  userType: TestUserType,
  options: { waitForDashboard?: boolean } = {}
): Promise<void> {
  const { waitForDashboard = true } = options;
  const user = TEST_USERS[userType];

  // Navigate to login page
  await page.goto('/login');

  // Fill in credentials
  await page.getByLabel('Email').fill(user.email);
  await page.getByLabel('Password').fill(user.password);

  // Submit form
  await page.getByRole('button', { name: /sign in/i }).click();

  // Wait for redirect to dashboard
  if (waitForDashboard) {
    await page.waitForURL('/dashboard', { timeout: 10000 });
  }
}

/**
 * Logout the current user.
 *
 * @param page - Playwright page object
 */
export async function logout(page: Page): Promise<void> {
  // Click on user menu or logout button
  // Note: This depends on the actual UI implementation
  const logoutButton = page.getByRole('button', { name: /logout/i });

  if (await logoutButton.isVisible()) {
    await logoutButton.click();
  } else {
    // Try clicking on user menu first
    const userMenu = page.getByRole('button', { name: /user menu/i });
    if (await userMenu.isVisible()) {
      await userMenu.click();
      await page.getByRole('menuitem', { name: /logout/i }).click();
    }
  }

  // Wait for redirect to login
  await page.waitForURL('/login', { timeout: 5000 });
}

/**
 * Check if user is currently logged in.
 *
 * @param page - Playwright page object
 * @returns true if user appears to be logged in
 */
export async function isLoggedIn(page: Page): Promise<boolean> {
  // Check for dashboard elements or auth state
  const dashboardHeading = page.getByRole('heading', {
    name: /executive control tower/i,
  });
  return await dashboardHeading.isVisible({ timeout: 2000 }).catch(() => false);
}

/**
 * Clear authentication state by clearing local storage and cookies.
 *
 * @param page - Playwright page object
 */
export async function clearAuthState(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
    // Clear accessToken cookie used by middleware
    document.cookie = 'accessToken=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/';
  });

  // Also clear cookies via Playwright context
  await page.context().clearCookies();
}
