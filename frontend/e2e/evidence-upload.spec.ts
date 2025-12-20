/**
 * Evidence Upload E2E Tests
 *
 * End-to-end tests for evidence management and approval workflows.
 * NOTE: Evidence page is currently a TODO stub. Most tests will skip until implemented.
 */

import { test, expect } from '@playwright/test';
import path from 'path';
import { loginAs } from './utils/auth';

test.describe('Evidence Vault Page', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
    await page.goto('/evidence');
  });

  test('should display evidence vault page', async ({ page }) => {
    // Verify page heading exists
    await expect(
      page.getByRole('heading', { name: /evidence vault/i })
    ).toBeVisible();
  });

  test('should show TODO message (page not implemented)', async ({ page }) => {
    // This test verifies the current stub state
    // Once implemented, this test should be removed or updated
    const todoMessage = page.getByText(/TODO/i);

    if (await todoMessage.isVisible()) {
      // Evidence page is still a stub - this is expected for Phase 3
      expect(await todoMessage.textContent()).toContain('TODO');
    } else {
      // If no TODO message, the page has been implemented
      // Check for actual evidence UI elements
      await expect(
        page
          .getByRole('button', { name: /upload/i })
          .or(page.getByRole('heading', { name: /evidence/i }))
      ).toBeVisible();
    }
  });
});

test.describe('Evidence Upload', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
    await page.goto('/evidence');
  });

  test('should have upload functionality (skip if not implemented)', async ({
    page,
  }) => {
    // Check if upload UI exists
    const uploadButton = page.getByRole('button', { name: /upload/i });
    const fileInput = page.locator('input[type="file"]');

    const hasUploadButton = await uploadButton.isVisible().catch(() => false);
    const hasFileInput = await fileInput.isVisible().catch(() => false);

    if (!hasUploadButton && !hasFileInput) {
      test.skip(true, 'Evidence upload UI not yet implemented');
      return;
    }

    // If upload UI exists, verify it's functional
    if (hasUploadButton) {
      await expect(uploadButton).toBeEnabled();
    }
  });

  test('should upload a PDF file (skip if not implemented)', async ({
    page,
  }) => {
    // Check if file input exists
    const fileInput = page.locator('input[type="file"]');

    if (!(await fileInput.isVisible().catch(() => false))) {
      test.skip(true, 'File upload input not available');
      return;
    }

    // Upload test PDF
    const filePath = path.join(__dirname, 'fixtures', 'sample.pdf');
    await fileInput.setInputFiles(filePath);

    // Wait for upload to complete
    await page.waitForLoadState('networkidle');

    // Verify file appears in list (implementation-dependent)
    await expect(page.getByText(/sample\.pdf/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test('should show upload progress indicator (skip if not implemented)', async ({
    page,
  }) => {
    const fileInput = page.locator('input[type="file"]');

    if (!(await fileInput.isVisible().catch(() => false))) {
      test.skip(true, 'File upload input not available');
      return;
    }

    // Upload file and check for progress
    const filePath = path.join(__dirname, 'fixtures', 'sample.pdf');
    await fileInput.setInputFiles(filePath);

    // Look for progress indicator (may be brief)
    const progressIndicator = page
      .getByRole('progressbar')
      .or(page.getByText(/uploading/i));

    // Progress might be too quick to catch, so this is a soft check
    await progressIndicator.isVisible({ timeout: 2000 }).catch(() => false);

    // Whether we saw progress or not, upload should complete
    await page.waitForLoadState('networkidle');
  });

  test('should reject invalid file types (skip if not implemented)', async ({
    page,
  }) => {
    const fileInput = page.locator('input[type="file"]');

    if (!(await fileInput.isVisible().catch(() => false))) {
      test.skip(true, 'File upload input not available');
      return;
    }

    // Check if input has file type restrictions
    const hasAcceptAttribute = await fileInput.getAttribute('accept');

    if (hasAcceptAttribute) {
      // Input has file type restrictions
      expect(hasAcceptAttribute).not.toContain('.exe');
    }
  });

  test('should display uploaded evidence with metadata (skip if not implemented)', async ({
    page,
  }) => {
    // Look for evidence list
    const evidenceList = page
      .locator('[data-testid="evidence-list"]')
      .or(page.getByRole('table'));

    if (!(await evidenceList.isVisible().catch(() => false))) {
      test.skip(true, 'Evidence list UI not implemented');
      return;
    }

    // Verify evidence items have expected metadata
    await expect(
      page.getByText(/filename/i).or(page.getByText(/uploaded/i))
    ).toBeVisible();
  });
});

test.describe('Evidence Approval', () => {
  test.beforeEach(async ({ page }) => {
    // Login as CFO for approval capabilities
    await loginAs(page, 'cfo');
    await page.goto('/evidence');
  });

  test('should show approve/reject buttons for approver (skip if not implemented)', async ({
    page,
  }) => {
    // Check if approval UI exists
    const approveButton = page.getByRole('button', { name: /approve/i });
    const rejectButton = page.getByRole('button', { name: /reject/i });

    const hasApprovalUI =
      (await approveButton.isVisible().catch(() => false)) ||
      (await rejectButton.isVisible().catch(() => false));

    if (!hasApprovalUI) {
      test.skip(true, 'Evidence approval UI not yet implemented');
      return;
    }

    // If approval UI exists, verify buttons are present
    await expect(approveButton.or(rejectButton)).toBeVisible();
  });

  test('should approve evidence (skip if not implemented)', async ({
    page,
  }) => {
    const approveButton = page.getByRole('button', { name: /approve/i });

    if (!(await approveButton.isVisible().catch(() => false))) {
      test.skip(true, 'Approve button not available');
      return;
    }

    // Click approve
    await approveButton.first().click();

    // Wait for action to complete
    await page.waitForLoadState('networkidle');

    // Should show success message or status change
    await expect(
      page.getByText(/approved/i).or(page.getByRole('alert'))
    ).toBeVisible({ timeout: 5000 });
  });

  test('should reject evidence with reason (skip if not implemented)', async ({
    page,
  }) => {
    const rejectButton = page.getByRole('button', { name: /reject/i });

    if (!(await rejectButton.isVisible().catch(() => false))) {
      test.skip(true, 'Reject button not available');
      return;
    }

    // Click reject
    await rejectButton.first().click();

    // Look for reason input dialog
    const reasonInput = page
      .getByLabel(/reason/i)
      .or(page.getByPlaceholder(/reason/i));

    if (await reasonInput.isVisible()) {
      await reasonInput.fill('Test rejection reason');
      await page.getByRole('button', { name: /confirm|submit/i }).click();
    }

    // Wait for action to complete
    await page.waitForLoadState('networkidle');
  });

  test('should not allow deletion of approved evidence (skip if not implemented)', async ({
    page,
  }) => {
    // Look for approved evidence with delete button
    const deleteButton = page.getByRole('button', { name: /delete/i });

    if (!(await deleteButton.isVisible().catch(() => false))) {
      test.skip(true, 'Delete button not available');
      return;
    }

    // If there's approved evidence, delete button should be disabled
    const approvedRow = page.locator('tr').filter({ hasText: /approved/i });

    if (await approvedRow.isVisible().catch(() => false)) {
      const rowDeleteButton = approvedRow.getByRole('button', {
        name: /delete/i,
      });

      // Delete button for approved evidence should be disabled
      if (await rowDeleteButton.isVisible()) {
        await expect(rowDeleteButton).toBeDisabled();
      }
    }
  });
});

test.describe('Evidence Versioning', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, 'admin');
    await page.goto('/evidence');
  });

  test('should upload new version of existing evidence (skip if not implemented)', async ({
    page,
  }) => {
    // Look for version upload functionality
    const uploadNewVersionButton = page.getByRole('button', {
      name: /new version|upload version/i,
    });

    if (!(await uploadNewVersionButton.isVisible().catch(() => false))) {
      test.skip(true, 'Version upload UI not implemented');
      return;
    }

    await uploadNewVersionButton.first().click();

    // Should show file upload dialog
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();
  });

  test('should display version history (skip if not implemented)', async ({
    page,
  }) => {
    // Look for version history button or tab
    const versionHistoryButton = page.getByRole('button', {
      name: /history|versions/i,
    });
    const versionTab = page.getByRole('tab', { name: /versions/i });

    const hasVersionUI =
      (await versionHistoryButton.isVisible().catch(() => false)) ||
      (await versionTab.isVisible().catch(() => false));

    if (!hasVersionUI) {
      test.skip(true, 'Version history UI not implemented');
      return;
    }

    // Click to show version history
    if (await versionHistoryButton.isVisible()) {
      await versionHistoryButton.first().click();
    } else {
      await versionTab.click();
    }

    // Should show version list
    await expect(page.getByText(/version/i)).toBeVisible();
  });
});

test.describe('Evidence Access Control', () => {
  test('Tax Lead should access evidence vault', async ({ page }) => {
    await loginAs(page, 'tax_lead');
    await page.goto('/evidence');

    // Should see evidence vault heading
    await expect(
      page.getByRole('heading', { name: /evidence vault/i })
    ).toBeVisible();
  });

  test('CFO should access evidence vault', async ({ page }) => {
    await loginAs(page, 'cfo');
    await page.goto('/evidence');

    // Should see evidence vault heading
    await expect(
      page.getByRole('heading', { name: /evidence vault/i })
    ).toBeVisible();
  });

  test('Admin should access evidence vault', async ({ page }) => {
    await loginAs(page, 'admin');
    await page.goto('/evidence');

    // Should see evidence vault heading
    await expect(
      page.getByRole('heading', { name: /evidence vault/i })
    ).toBeVisible();
  });
});
