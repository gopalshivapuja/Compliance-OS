# Changelog

All notable changes to Compliance OS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for Phase 7 (Frontend Dashboard Views)
- Enhanced dashboard with interactive charts
- Compliance calendar view
- Owner workload heatmap
- Real-time updates

---

## [0.6.0] - 2024-12-21 - Phase 6 Complete: Frontend Authentication & Layout

### Added

#### Next.js Middleware (`frontend/src/middleware.ts`)
- **Server-Side Authentication**
  - Token check in cookies for protected routes
  - Automatic redirect to `/login` for unauthenticated users
  - Preserve intended destination URL for post-login redirect
  - Exclude public paths (`/login`, `/forgot-password`, `/reset-password`)
  - Skip static assets (`/_next`, `/api`, `/favicon.ico`)

#### Cookie Sync in Auth Store
- **Login/Logout Cookie Management**
  - `setCookie()` helper for setting auth cookie with expiry
  - `removeCookie()` helper for clearing auth cookie
  - Token automatically synced to cookie on login
  - Cookie cleared on logout
  - SameSite=Lax for CSRF protection

#### Notification System (`frontend/src/components/layout/NotificationsBell.tsx`)
- **Notification Types** (8 types)
  - `task_assigned` - Blue (UserPlus icon)
  - `reminder_t3` - Amber (Clock icon)
  - `reminder_due` - Amber (AlertTriangle icon)
  - `overdue` - Red (XCircle icon)
  - `approval_required` - Purple (CheckSquare icon)
  - `evidence_approved` - Green (CheckCircle icon)
  - `evidence_rejected` - Red (XCircle icon)
  - `system` - Gray (Info icon)

- **NotificationsBell Component**
  - Bell icon with unread count badge (max "9+")
  - Dropdown showing 5 most recent unread notifications
  - Type-specific icons and colors
  - Relative time formatting ("Just now", "5m ago", "2h ago")
  - Click to mark as read and navigate to link
  - "Mark all read" button
  - "View all notifications" link

- **Notifications Page** (`/notifications`)
  - Full page view of all notifications
  - Filter tabs: All, Unread, Read
  - Mark all as read button
  - Notification details with links

#### React Query Hooks (`frontend/src/lib/hooks/useNotifications.ts`)
- `useNotificationCount()` - Fetches unread count, 60-second polling
- `useNotifications()` - Lists notifications with filters
- `useRecentNotifications()` - For dropdown (default 5 items)
- `useMarkNotificationRead()` - Mutation to mark single as read
- `useMarkMultipleRead()` - Mutation to mark batch as read
- `useMarkAllRead()` - Mutation to mark all as read

#### API Endpoints (`frontend/src/lib/api/endpoints.ts`)
- `notificationsApi.list()` - List with pagination and is_read filter
- `notificationsApi.getCount()` - Get unread count
- `notificationsApi.get()` - Get single notification
- `notificationsApi.markRead()` - Mark single as read
- `notificationsApi.markMultipleRead()` - Mark batch as read
- `notificationsApi.markAllRead()` - Mark all as read
- `notificationsApi.delete()` - Delete single
- `notificationsApi.deleteMultiple()` - Delete batch

#### Enhanced Sidebar Navigation (`frontend/src/components/layout/Sidebar.tsx`)
- **Main Navigation**
  - Dashboard
  - Compliance Masters (new)
  - Compliance Instances
  - Workflow Tasks (new)
  - Evidence Vault

- **Administration Section** (role-restricted)
  - Users (Tenant Admin, System Admin)
  - Entities (Tenant Admin, System Admin)
  - Audit Logs (CFO, System Admin)

#### Placeholder Pages (Phase 7+)
- `/compliance-masters` - Compliance master definitions
- `/workflow-tasks` - User's assigned workflow tasks
- `/users` - User management (admin only)
- `/entities` - Entity management (admin only)
- `/notifications` - Full notifications list

### Changed

- **Auth Store** (`frontend/src/lib/store/auth-store.ts`)
  - Added `updateTokens()` method for token refresh
  - Login now sets cookie for middleware access
  - Logout now clears cookie

- **Header** (`frontend/src/components/layout/Header.tsx`)
  - Added NotificationsBell before user menu
  - Wrapped in flex container with gap

- **E2E Auth Utils** (`frontend/e2e/utils/auth.ts`)
  - `clearAuthState()` now clears cookies
  - Uses Playwright's `context.clearCookies()`

- **TypeScript Config** (`frontend/tsconfig.json`)
  - Excluded `src/__tests__` from compilation (Jest handles separately)

### Fixed

- **AuditLogTable** (`frontend/src/components/audit/AuditLogTable.tsx`)
  - Added missing action types: VIEW, DOWNLOAD, UPLOAD

### Statistics

- **New Files**: 9 files (~800 lines)
- **Modified Files**: 6 files (~200 lines)
- **Total**: ~1,000 lines of production code
- **Build Status**: Type check passing, build successful
- **Duration**: 1 day

---

## [0.5.0] - 2024-12-21 - Phase 5 Complete: Backend Background Jobs

### Added

#### Email Service (`app/services/email_service.py` - 389 lines)
- **SendGrid Integration**
  - `EmailService` class with configurable API key and from address
  - `send_email()` - Renders Jinja2 template and sends via SendGrid API
  - `EMAIL_ENABLED` toggle for dev/prod modes (disabled by default)
  - Automatic fallback to logging in development mode

- **Email Helper Functions**
  - `send_reminder_email()` - T-3 days, due date, and overdue reminders
  - `send_escalation_email()` - Overdue escalation to CFO with days count
  - `send_task_assigned_email()` - Task assignment notification
  - `send_evidence_status_email()` - Evidence approval/rejection with reason
  - `send_task_reminder_email()` - Task due date reminders

- **Singleton Pattern**
  - `get_email_service()` - Returns singleton EmailService instance
  - Lazy initialization on first use

#### Email Templates (`app/templates/email/` - 7 templates)
- **Base Template** (`base.html`)
  - Compliance OS branding with logo placeholder
  - Responsive email layout for all clients
  - RAG status badge styling (Green/Amber/Red)
  - Info box styling for key details
  - CTA button styling

- **Notification Templates**
  - `reminder_t3.html` - T-3 days compliance reminder
  - `reminder_due.html` - Due date compliance reminder
  - `escalation.html` - Overdue escalation with urgency styling
  - `task_assigned.html` - New task assignment notification
  - `evidence_approved.html` - Evidence approval confirmation
  - `evidence_rejected.html` - Evidence rejection with reason

#### Notification Tasks (`app/tasks/notification_tasks.py` - 260 lines)
- **Async Email Tasks** (6 Celery tasks)
  - `send_email_task()` - Generic email sending with retry logic
  - `send_reminder_email_task()` - Reminder email queueing
  - `send_escalation_email_task()` - Escalation email queueing
  - `send_task_assigned_email_task()` - Task assignment emails
  - `send_evidence_status_email_task()` - Evidence status emails
  - `send_task_reminder_email_task()` - Task reminder emails

- **Reliability Features**
  - Exponential backoff retry (max 3 retries, 60s base delay)
  - Database session management with proper cleanup
  - Comprehensive error logging
  - UUID string conversion for Celery serialization

#### Reminder Tasks Integration
- **Updated Functions** (`app/tasks/reminder_tasks.py`)
  - `send_t3_reminders()` - Now queues T-3 reminder emails
  - `send_due_date_reminders()` - Now queues due date emails
  - `escalate_overdue_items()` - Now queues escalation emails
  - `send_task_reminders()` - Now queues task reminder emails

- **Email Queue Pattern**
  ```python
  # After in-app notification, queue email
  notification = notify_reminder_t3(db, instance, owner)
  if notification:
      send_reminder_email_task.delay(
          user_id=str(owner.id),
          instance_id=str(instance.id),
          reminder_type="t3",
      )
  ```

### Testing

#### Unit Tests (43 new tests - 100% passing)

**Compliance Task Tests** (`test_compliance_tasks.py` - 15 tests):
- `TestGenerateComplianceInstancesDaily`
  - test_generates_instances_for_all_tenants
  - test_skips_when_no_active_tenants
  - test_handles_tenant_error_gracefully

- `TestRecalculateRagStatusHourly`
  - test_recalculates_rag_for_all_tenants
  - test_handles_redis_failure_gracefully
  - test_returns_no_tenants_when_empty

- `TestGenerateQuarterlyInstances`
  - test_generates_quarterly_instances

- `TestGenerateAnnualInstances`
  - test_generates_annual_instances_on_april_1
  - test_filters_annual_frequency_only

- `TestUpdateOverdueStatus`
  - test_marks_past_due_as_overdue
  - test_skips_completed_instances
  - test_handles_multiple_overdue_instances
  - test_handles_database_error

- `TestInvalidateDashboardCache`
  - test_deletes_dashboard_cache_keys
  - test_handles_redis_error

**Reminder Task Tests** (`test_reminder_tasks.py` - 15 tests):
- `TestSendT3Reminders`
  - test_sends_reminder_3_days_before_due
  - test_skips_completed_instances
  - test_handles_missing_owner

- `TestSendDueDateReminders`
  - test_sends_reminder_on_due_date
  - test_handles_missing_owner

- `TestEscalateOverdueItems`
  - test_escalates_3_days_overdue
  - test_prevents_duplicate_escalations
  - test_finds_cfo_for_escalation

- `TestSendTaskReminders`
  - test_sends_reminder_2_days_before_task_due
  - test_skips_completed_tasks

- `TestCleanupOldNotifications`
  - test_deletes_notifications_older_than_90_days
  - test_handles_empty_notifications

- `TestGetInstanceOwner`
  - test_finds_owner_by_role_and_entity_access (integration)

- `TestGetEscalationUser`
  - test_finds_cfo_first (integration)
  - test_falls_back_to_admin (integration)

**Email Service Tests** (`test_email_service.py` - 13 tests):
- `TestEmailService`
  - test_email_disabled_in_dev_mode
  - test_send_email_success
  - test_handles_sendgrid_error
  - test_handles_non_success_status_code

- `TestTemplateRendering`
  - test_template_renders_with_context
  - test_template_not_found_raises_error

- `TestEmailHelperFunctions`
  - test_send_reminder_email
  - test_send_escalation_email
  - test_send_task_assigned_email
  - test_send_evidence_status_email_approved
  - test_send_evidence_status_email_rejected

- `TestGetEmailService`
  - test_returns_singleton_instance
  - test_creates_new_instance_when_none

### Changed

- **Config Settings** (`app/core/config.py`)
  - Added `EMAIL_ENABLED: bool = False` toggle
  - Added `SENDGRID_API_KEY: str = ""` for SendGrid
  - Added `EMAIL_FROM_ADDRESS: str = "noreply@complianceos.com"`
  - Added `EMAIL_FROM_NAME: str = "Compliance OS"`

- **Type Hints** (`app/tasks/reminder_tasks.py`)
  - Fixed Python 3.9 compatibility (changed `User | None` to `Optional[User]`)

- **Exports**
  - `app/tasks/__init__.py` - Added notification task exports
  - `app/services/__init__.py` - Added email service exports

### Dependencies

- Added `sendgrid>=6.10.0` for email sending
- Added `Jinja2>=3.1.2` for email template rendering

### Statistics

- **Code**: ~1,200 lines of production code
- **Tests**: ~900 lines of test code (43 tests)
- **Templates**: ~500 lines of HTML templates
- **Total Unit Tests**: 359 (100% passing)
- **Duration**: 1 day

---

## [0.4.0] - 2024-12-20 - Phase 4 Complete: Backend Business Logic

### Added

#### Compliance Engine (`app/services/compliance_engine.py` - 591 lines)
- **Due Date Calculation**
  - `calculate_due_date()` - Calculates due dates from JSONB rule configuration
  - Supports 5 rule types: Monthly, Quarterly, Annual, Fixed Date, Event-Based
  - India FY calendar support (Apr-Mar fiscal year)
  - Configurable offset days for each rule type

- **Period Calculation**
  - `calculate_period_for_frequency()` - Returns period start/end dates
  - Monthly: Calendar month boundaries
  - Quarterly: India FY quarters (Q1=Apr-Jun, Q2=Jul-Sep, Q3=Oct-Dec, Q4=Jan-Mar)
  - Annual: Full fiscal year (Apr 1 - Mar 31)

- **Instance Generation**
  - `generate_instances_for_period()` - Creates instances for all entities
  - Checks for existing instances to prevent duplicates
  - Applies entity-specific configurations

- **RAG Status Calculation**
  - `calculate_rag_status()` - Determines compliance health status
  - Green: On track (due date > 7 days away)
  - Amber: At risk (due date ≤ 7 days)
  - Red: Overdue or blocked by dependency
  - Completed instances always return Green

- **Dependency Resolution**
  - `check_dependencies_met()` - Verifies blocking dependencies
  - Prevents task progression when blockers exist

#### Workflow Engine (`app/services/workflow_engine.py` - 596 lines)
- **Standard Workflow Definition**
  - `STANDARD_WORKFLOW` constant with 5-step process:
    1. Prepare Documentation (Tax Lead, 3 days)
    2. Review Submission (Tax Lead, 2 days)
    3. CFO Approval (CFO, 2 days)
    4. File with Authority (Tax Lead, 1 day)
    5. Archive Evidence (Tax Lead, 1 day)

- **Role Resolution**
  - `resolve_role_to_user()` - Maps role names to tenant users
  - Supports direct user assignment or role-based assignment

- **Task Lifecycle Management**
  - `create_workflow_tasks()` - Generates all tasks for an instance
  - `start_task()` - Transitions Pending → In Progress
  - `complete_task()` - Transitions In Progress → Completed
  - `reject_task()` - Transitions In Progress → Rejected with reason

- **Sequence Enforcement**
  - Parent task validation before child can start/complete
  - `check_instance_completion()` - Verifies all tasks completed

- **Task Queries**
  - `get_overdue_tasks()` - Tasks past due date
  - `get_tasks_due_soon()` - Tasks due within N days
  - `get_tasks_by_user()` - User's assigned tasks
  - `get_tasks_by_instance()` - All tasks for an instance

#### Notification Service (`app/services/notification_service.py` - 589 lines)
- **Notification Types** (8 types)
  - `task_assigned` - New task assignment
  - `reminder_t3` - 3 days before due date
  - `reminder_due` - On due date
  - `overdue` - Past due date
  - `approval_required` - Needs approval action
  - `evidence_approved` - Evidence was approved
  - `evidence_rejected` - Evidence was rejected
  - `system` - System announcements

- **CRUD Operations**
  - `create_notification()` - Create in-app notification
  - `get_user_notifications()` - List with pagination and filtering
  - `get_notification_by_id()` - Get single notification
  - `mark_notification_read()` - Mark single as read
  - `mark_all_read()` - Mark all user's notifications as read
  - `delete_notification()` - Delete single notification
  - `delete_notifications()` - Bulk delete

- **Notification Helpers**
  - `notify_task_assigned()` - Task assignment notification
  - `notify_reminder_t3()` - T-3 days reminder
  - `notify_reminder_due()` - Due date reminder
  - `notify_overdue_escalation()` - Escalation to approver

#### Evidence Service (`app/services/evidence_service.py` - 598 lines)
- **File Validation**
  - `validate_file()` - Type and size validation
  - 25 allowed extensions (PDF, Excel, Word, Images, CSV, ZIP, etc.)
  - `EXTENSION_MIME_MAP` constant for type mapping
  - Configurable max file size (default 25MB)

- **Hash Generation**
  - `generate_file_hash()` - SHA-256 hash for integrity
  - Hash comparison for duplicate detection

- **Approval Workflow**
  - `approve_evidence()` - Sets approval status and immutability
  - `reject_evidence()` - Rejects with reason
  - Immutable evidence cannot be deleted or modified

- **Versioning**
  - `create_evidence_version()` - Creates new version
  - Links to parent via `parent_evidence_id`
  - Increments version number

- **Directory Management**
  - `get_evidence_directory()` - Constructs organized path
  - Path format: `{base}/{tenant_id}/{entity_id}/{instance_id}/`

#### Notifications API (`app/api/v1/endpoints/notifications.py`)
- `GET /api/v1/notifications/` - List user's notifications
- `GET /api/v1/notifications/count` - Get unread count
- `GET /api/v1/notifications/{id}` - Get single notification
- `PUT /api/v1/notifications/{id}/read` - Mark as read
- `POST /api/v1/notifications/mark-all-read` - Mark all read
- `DELETE /api/v1/notifications/{id}` - Delete notification
- User isolation enforced on all endpoints

### Testing

#### Unit Tests (225 Phase 4 tests - 100% pass rate)

**Compliance Engine Tests** (53 tests):
- `test_compliance_engine.py`
  - Due date calculation for all 5 rule types
  - Period calculation for Monthly/Quarterly/Annual
  - RAG status calculation (Green/Amber/Red thresholds)
  - Dependency resolution and blocking logic
  - Edge cases: empty rules, None values, fiscal year boundaries

**Workflow Engine Tests** (60 tests):
- `test_workflow_engine.py`
  - STANDARD_WORKFLOW constant structure validation
  - Role resolution to user mapping
  - Task state transitions (start/complete/reject)
  - Sequence enforcement (parent-child dependencies)
  - Instance completion checks
  - Task queries (overdue, due soon, by user/instance)
  - Edge cases: whitespace reasons, custom dates

**Notification Service Tests** (60 tests):
- `test_notification_service.py`
  - NotificationType constants verification
  - CRUD operations with pagination
  - Mark read (single and batch)
  - Delete operations (single and bulk)
  - Notification helpers (task_assigned, reminders, escalation)
  - User isolation verification
  - Edge cases: empty notifications, read counts

**Evidence Service Tests** (52 tests):
- `test_evidence_service.py`
  - File validation (type, size)
  - Hash generation (SHA-256 consistency)
  - Approval/rejection workflow
  - Immutability enforcement
  - Versioning with parent linking
  - Directory path construction
  - Edge cases: large files, unknown extensions

#### Integration Tests (27 tests - 100% pass rate)

**Notifications API Tests**:
- `test_notifications.py`
  - List notifications with pagination
  - Filter by unread status
  - Get unread count
  - Mark single notification as read
  - Mark all notifications as read
  - Delete notifications
  - Multi-tenant isolation
  - User isolation

### Security

- **Multi-Tenant Isolation**
  - 101 tenant_id references across Phase 4 services
  - All queries filter by tenant_id from JWT
  - Cross-tenant access prevented at service layer

- **Audit Logging Integration**
  - 14 log_action calls in endpoint layer
  - State changes logged with before/after values
  - Approval/rejection actions tracked

- **User Isolation**
  - Notifications scoped to individual users
  - Users cannot access other users' notifications
  - Task assignments verified against user access

### Statistics

- **Code**: 4 service files (~2,374 lines production code)
- **Tests**: 5 test files (~3,000 lines test code)
- **Total Phase 4 Tests**: 252 tests (100% passing)
- **Coverage**:
  - notification_service.py: 100%
  - workflow_engine.py: 98%
  - evidence_service.py: 66%
  - compliance_engine.py: 59%
  - Average: 78%

---

## [0.3.0] - 2024-12-20 - Phase 3 Complete: Backend CRUD Operations

### Added

#### Entities Module (5 endpoints, 25 tests)
- **CRUD Operations with RBAC**
  - `POST /api/v1/entities` - Create entity (Tenant Admin only)
  - `GET /api/v1/entities` - List entities (filtered by user's accessible entities)
  - `GET /api/v1/entities/{id}` - Get entity details (entity access check)
  - `PUT /api/v1/entities/{id}` - Update entity (Tenant Admin only)
  - `DELETE /api/v1/entities/{id}` - Soft delete entity (prevents if active instances exist)
  - Multi-tenant isolation enforced on all queries
  - Entity-level access control via entity_access table
  - Search and filtering by status, entity_type

#### Compliance Masters Module (6 endpoints, 35 tests)
- **Full CRUD with System Template Support**
  - `POST /api/v1/compliance-masters` - Create compliance master
  - `GET /api/v1/compliance-masters` - List masters (includes system templates + tenant-specific)
  - `GET /api/v1/compliance-masters/{id}` - Get master details
  - `PUT /api/v1/compliance-masters/{id}` - Update master (system templates require System Admin)
  - `DELETE /api/v1/compliance-masters/{id}` - Delete master (force option if instances exist)
  - `POST /api/v1/compliance-masters/bulk-import` - Bulk import from CSV/Excel with validation
  - System templates (tenant_id = NULL) accessible to all tenants
  - Tenant-specific masters customizable by Tenant Admin
  - Category and frequency filtering
  - Overwrite and skip options for bulk import

#### Compliance Instances Module (5 endpoints, 31 tests)
- **Instance Management with RAG Calculation**
  - `POST /api/v1/compliance-instances` - Create instance manually (prevents duplicates)
  - `GET /api/v1/compliance-instances` - List with advanced filtering
  - `GET /api/v1/compliance-instances/{id}` - Get instance details
  - `PUT /api/v1/compliance-instances/{id}` - Update instance (status, owner, fields)
  - `POST /api/v1/compliance-instances/{id}/recalculate-status` - RAG recalculation endpoint
  - RAG calculation: Red (overdue), Amber (<7 days), Green (on track)
  - Blocking dependencies affect RAG status
  - Completed instances always Green
  - Advanced filtering: entity, status, RAG, category, owner, due_date range

#### Workflow Tasks Module (8 endpoints, 32 tests)
- **CRUD + Action Endpoints**
  - `POST /api/v1/workflow-tasks` - Create task
  - `GET /api/v1/workflow-tasks` - List tasks (filter by instance/user/status/type)
  - `GET /api/v1/workflow-tasks/{id}` - Get task details
  - `PUT /api/v1/workflow-tasks/{id}` - Update task (assignment, due date)
  - `DELETE /api/v1/workflow-tasks/{id}` - Delete task (Pending status only)
  - `POST /api/v1/workflow-tasks/{id}/start` - Start task (Pending → In Progress)
  - `POST /api/v1/workflow-tasks/{id}/complete` - Complete task (sets completed_at)
  - `POST /api/v1/workflow-tasks/{id}/reject` - Reject task (requires rejection_reason)
  - Parent-child task dependencies enforced
  - Dual assignment support (user OR role)
  - Status transition validation
  - Cannot delete in-progress or completed tasks

#### Evidence Module (7 endpoints, 27 tests)
- **File Upload/Download with Approval Workflow**
  - `POST /api/v1/evidence/upload` - Upload evidence with file validation (multipart/form-data)
  - `GET /api/v1/evidence` - List evidence (filter by instance/approval status)
  - `GET /api/v1/evidence/{id}` - Get evidence metadata
  - `GET /api/v1/evidence/{id}/download` - Generate signed URL for download (5-min expiry)
  - `POST /api/v1/evidence/{id}/approve` - Approve evidence (sets is_immutable = true)
  - `POST /api/v1/evidence/{id}/reject` - Reject evidence (requires rejection_reason)
  - `DELETE /api/v1/evidence/{id}` - Delete evidence (blocked if immutable)
  - File validation: PDF, Excel, Word, Images, CSV, ZIP (max 50MB)
  - SHA-256 hash generation for integrity verification
  - Immutability after approval (audit requirement)
  - Local storage with S3-ready architecture
  - Version tracking support via parent_evidence_id

#### Dashboard Module - Owner Heatmap (1 endpoint, 7 tests)
- **Workload Distribution**
  - `GET /api/v1/dashboard/owner-heatmap` - Compliance workload by owner
  - Shows total assigned, RAG breakdown, overdue count, upcoming count per owner
  - Includes unassigned items as separate entry
  - Sorted by workload (busiest owners first)
  - Multi-tenant isolation verified

#### Backend Services
- **evidence_service.py** - File handling utilities
  - `calculate_file_hash()` - SHA-256 hash generation
  - `generate_file_path()` - Organized storage paths
  - `save_file_locally()` - Local storage (S3-ready)
  - `delete_file_locally()` - File deletion
  - `generate_signed_url()` - Signed URL generation (mock for dev, S3 in prod)
  - `validate_file_type()` - File extension validation
  - `validate_file_size()` - Size limit enforcement

#### Pydantic Schemas (7 new schema files)
- **entity.py** - EntityBase, EntityCreate, EntityUpdate, EntityResponse, EntityListResponse
- **tenant.py** - TenantBase, TenantCreate, TenantUpdate, TenantResponse, TenantListResponse
- **user.py** - UserBase, UserCreate, UserUpdate, UserInDB, UserListResponse
- **compliance_master.py** - ComplianceMasterBase, Create, Update, Response, ListResponse, BulkImportRequest/Response
- **compliance_instance.py** - ComplianceInstanceBase, Create, Update, Response, ListResponse
- **workflow_task.py** - WorkflowTaskBase, Create, Update, ActionRequest, RejectRequest, Response, ListResponse
- **evidence.py** - EvidenceBase, UploadRequest, ApprovalRequest, RejectionRequest, Response, ListResponse, DownloadResponse
- All schemas use barrel exports from `__init__.py`

### Changed

- **schemas/__init__.py** - Updated barrel exports to include all Phase 3 schemas
- **Multi-Tenant Isolation Enhanced**
  - All new endpoints filter by `tenant_id` from JWT
  - Entity access checks enforce tenant boundaries
  - RBAC enforcement on all mutation operations

### Security

- **Multi-Tenant Isolation**
  - All queries filtered by `tenant_id` from JWT token
  - Entity-level access control via `entity_access` table
  - Users can only see entities they have permission to access

- **RBAC Enforcement**
  - Role-based checks on all endpoints (Tenant Admin, System Admin, CFO)
  - Entity access verified before read/write operations
  - 403 Forbidden responses for unauthorized access attempts

- **File Security**
  - File type validation (whitelist approach)
  - File size limits (50MB default, configurable)
  - SHA-256 hash generation for integrity verification
  - Signed URLs with expiration (5 minutes)
  - Immutability enforcement after approval

- **Audit Logging Integration**
  - All mutations logged with before/after snapshots
  - Complete trail for CREATE, UPDATE, DELETE, APPROVE, REJECT actions

### Performance

- **Query Optimization**
  - Efficient joins with proper foreign key relationships
  - Pagination on all list endpoints (default limit: 50, max: 500)
  - Strategic filtering reduces result set size

- **File Handling**
  - Local storage for development
  - S3-ready architecture for production scaling
  - Organized file paths for efficient retrieval

### Testing

- **Integration Tests** (157 tests, 100% pass rate)
  - `tests/integration/api/test_entities.py` (25 tests)
  - `tests/integration/api/test_compliance_masters.py` (35 tests)
  - `tests/integration/api/test_compliance_instances.py` (31 tests)
  - `tests/integration/api/test_workflow_tasks.py` (32 tests)
  - `tests/integration/api/test_evidence.py` (27 tests)
  - `tests/integration/api/test_dashboard.py` (7 new owner heatmap tests)
  - All tests verify RBAC enforcement, multi-tenant isolation, and entity access control

### Statistics

- **Backend**: 16 files created/modified (~3,500 lines)
- **Tests**: 6 test files (157 test cases, ~4,200 lines)
- **Total Endpoints**: 31 endpoints across 6 modules
- **Test Coverage**: 100% pass rate (157/157 tests)
- **Duration**: 3 days (estimated: 2 weeks - 4.7x faster than planned)

---

## [0.2.0] - 2025-12-18 - Phase 2 Complete: Auth & RBAC

### Added

#### Backend Authentication & Authorization
- **JWT Authentication System**
  - `POST /api/v1/auth/login` - Email/password authentication with JWT tokens
  - `POST /api/v1/auth/refresh` - Refresh access token using refresh token
  - `POST /api/v1/auth/logout` - Invalidate refresh token in Redis
  - `GET /api/v1/auth/me` - Get current user profile with roles
  - JWT payload includes: `tenant_id`, `user_id`, `email`, `roles[]`
  - Access tokens expire in 24 hours, refresh tokens in 7 days
  - Refresh tokens stored in Redis with TTL for automatic cleanup

#### Dashboard API
- **Executive Control Tower Endpoints**
  - `GET /api/v1/dashboard/overview` - RAG status counts, category breakdown, overdue summary
  - `GET /api/v1/dashboard/overdue` - List of overdue compliance instances
  - `GET /api/v1/dashboard/upcoming` - Compliance instances due in next 7 days
  - Redis caching with 5-minute TTL for performance
  - Denormalized `tenant_id` in compliance_instances for fast queries

#### RBAC & Entity Access Control
- **Role-Based Access Control**
  - `check_role_permission()` function in entity_access_service
  - `check_entity_access()` function for entity-level permissions
  - Multi-tenant isolation enforced on all queries (filter by `tenant_id` from JWT)
  - 403 Forbidden responses for unauthorized access
  - Entity access table integration for granular permissions

#### Compliance Instance Management
- **CRUD Operations with RBAC**
  - `GET /api/v1/compliance-instances` - List instances (filtered by accessible entities)
  - `GET /api/v1/compliance-instances/{id}` - Get single instance (entity access check)
  - `PUT /api/v1/compliance-instances/{id}` - Update instance (entity access check + audit logging)
  - All endpoints enforce multi-tenant isolation
  - Captures old/new values before updates for complete audit trail

#### Audit Logging System
- **Immutable Audit Trail**
  - `log_action()` - Create audit log entries with before/after snapshots
  - `get_audit_logs()` - Query logs with filters (resource_type, resource_id, user_id, action_type)
  - `get_resource_audit_trail()` - Get complete audit history for a specific resource
  - `GET /api/v1/audit-logs` - List all audit logs with pagination (CFO/System Admin only)
  - `GET /api/v1/audit-logs/resource/{type}/{id}` - Complete audit trail for a resource
  - `GET /api/v1/audit-logs/{id}` - Get single audit log by ID
  - Audit logs are append-only (no DELETE/UPDATE endpoints)
  - Captures: user_id, action_type, resource_type, resource_id, old_values, new_values, change_summary, IP address, user_agent, timestamp
  - Before/after snapshots stored as JSONB for complete auditability
  - All mutations (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, REJECT) logged automatically

#### Backend Services
- **audit_service.py** (171 lines) - Audit logging with JSONB snapshots
- **entity_access_service.py** (229 lines) - Entity access control and RBAC checks
  - `check_entity_access()` - Verify user has access to entity
  - `get_user_accessible_entities()` - Get list of accessible entity IDs
  - `check_role_permission()` - Check if user has required role
  - `get_user_roles()` - Get list of role names for a user
  - `grant_entity_access()` - Grant user access to entity
  - `revoke_entity_access()` - Revoke user's access to entity

#### Pydantic Schemas (4 new schema files)
- **auth.py** - LoginRequest, TokenResponse, UserResponse, RefreshTokenRequest, LogoutRequest
- **dashboard.py** - RAGCounts, CategoryBreakdown, DashboardOverviewResponse, ComplianceInstanceSummary
- **compliance_instance.py** - ComplianceInstanceResponse, ComplianceInstanceListResponse, ComplianceInstanceUpdate
- **audit.py** - AuditLogResponse, AuditLogListResponse, ResourceAuditTrailResponse
- All schemas use `Optional` for Python 3.9 compatibility (not `str | None`)

#### Frontend Pages
- **Login Page** (`frontend/src/app/login/page.tsx`)
  - Email and password fields with validation
  - React Hook Form + Zod schema validation
  - Error handling for invalid credentials
  - Redirect to dashboard on successful login
  - Loading state during authentication

- **Executive Control Tower Dashboard** (`frontend/src/app/(dashboard)/dashboard/page.tsx`)
  - RAG status cards showing Green/Amber/Red counts
  - Category breakdown chart
  - Overdue compliance instances table
  - Auto-refresh every 5 minutes
  - Responsive layout

- **Compliance Instances List** (`frontend/src/app/(dashboard)/compliance-instances/page.tsx`)
  - Filterable table of compliance instances
  - RAG status badges
  - Entity-level filtering based on user access
  - Pagination support

- **Audit Log Viewer** (`frontend/src/app/(dashboard)/audit-logs/page.tsx`)
  - Read-only audit log viewer
  - Role-restricted (CFO and System Admin only)
  - Filters: resource_type, action_type, user_id
  - Expandable rows showing before/after values

#### Frontend Components (8 new components)
- **RAGStatusCard.tsx** - Displays RAG status with count and percentage
- **CategoryChart.tsx** - Bar chart for category breakdown
- **OverdueTable.tsx** - Table showing overdue compliance instances
- **ComplianceTable.tsx** - Filterable compliance instances table
- **AuditLogTable.tsx** - Expandable audit log viewer with JSONB diff
- **useDashboard.ts** - React Query hooks for dashboard data fetching
- **useCompliance.ts** - React Query hooks for compliance instance data
- **useAuditLogs.ts** - React Query hooks for audit log data

#### Testing Infrastructure
- **Backend Tests** (3 test files, 38+ test cases)
  - `tests/integration/api/test_auth.py` (354 lines, 17 tests) - Authentication endpoints
  - `tests/unit/services/test_audit_service.py` (295 lines, 11 tests) - Audit service
  - `tests/unit/core/test_redis.py` (162 lines, 10 tests) - Redis token management
  - Test coverage: 75% (exceeds 70% target)

### Changed

- **Multi-Tenant Isolation Enhanced**
  - All compliance instance queries now filter by `tenant_id` from JWT
  - Entity access checks enforce tenant boundaries
  - Dashboard queries optimized with denormalized `tenant_id`

- **Compliance Instance Model**
  - Added denormalized `tenant_id` column for performance
  - Added indexes on `tenant_id`, `entity_id`, `status`, `due_date`

- **Database Schema**
  - Added indexes for audit log queries (tenant_id, created_at, resource_type, resource_id)
  - Added indexes for entity_access table (user_id, entity_id, tenant_id)

### Security

- **Multi-Tenant Isolation**
  - All queries filtered by `tenant_id` from JWT token
  - Entity-level access control via `entity_access` table
  - Users can only see entities they have permission to access

- **RBAC Enforcement**
  - Role-based checks on all sensitive endpoints
  - Audit logs restricted to CFO and System Admin roles
  - 403 Forbidden responses for unauthorized access attempts

- **Audit Log Immutability**
  - Audit logs are append-only (no UPDATE or DELETE endpoints)
  - Cannot be modified or deleted, ensuring tamper-proof audit trail
  - Complies with regulatory audit requirements

- **JWT Token Security**
  - Short-lived access tokens (24 hours)
  - Refresh token rotation with Redis storage
  - Automatic token cleanup via Redis TTL
  - Tokens include tenant_id for isolation

- **Password Security**
  - Bcrypt hashing with salt
  - Password verification in authentication service
  - No plaintext password storage

### Performance

- **Redis Caching**
  - Dashboard queries cached with 5-minute TTL
  - Refresh tokens stored in Redis for fast validation
  - Automatic cache invalidation on data changes

- **Database Optimizations**
  - Denormalized `tenant_id` in compliance_instances avoids expensive joins
  - Strategic indexes on common query patterns
  - Pagination on all list endpoints (default limit: 100, max: 1000)

- **Query Optimization**
  - Dashboard aggregation queries optimized for performance
  - Denormalized user info in audit log responses (cached lookups)

### Fixed

- Python 3.9 compatibility issues with type hints (changed `str | None` to `Optional[str]`)

### Statistics

- **Backend**: ~3,500 lines of code added (15 files)
- **Frontend**: ~1,800 lines of code added (12 files)
- **Tests**: 38+ test cases (3 test files)
- **Test Coverage**: 75% backend (target: 70%)
- **Documentation**: 1,500+ lines updated
- **Duration**: 2 days (estimated: 6-8 days - 3-4x faster than planned)

---

## [0.1.0] - 2024-12-18 - Phase 1 Complete

### Added

#### Backend Infrastructure
- FastAPI application setup with CORS middleware and compression
- PostgreSQL database connection with SQLAlchemy ORM (connection pooling configured)
- Redis connection for caching and session management
- Celery configuration for background job processing
- Alembic database migration framework setup
- JWT authentication utilities (`create_access_token`, `decode_access_token`, `verify_password`)
- Role-based access control dependencies (`get_current_user`, `require_role`)
- Pydantic settings management with environment variable support

#### Database Schema (15 Tables)
- **Core Tables**: `tenants`, `users`, `roles`, `user_roles`, `entity_access`
- **Compliance Tables**: `entities`, `compliance_masters`, `compliance_instances`
- **Workflow Tables**: `workflow_tasks`
- **Evidence Tables**: `evidence`, `evidence_tag_mappings`, `tags`
- **Audit Tables**: `audit_logs`, `notifications`

#### SQLAlchemy Models (11 Complete Models)
- `Tenant` - Multi-tenant isolation with metadata
- `User` - User accounts with password hashing
- `Role` - RBAC roles (System Admin, Tenant Admin, CFO, VP Finance, Tax Lead, Accountant, Auditor)
- `Entity` - Legal entities (branches, subsidiaries)
- `ComplianceMaster` - Compliance template definitions
- `ComplianceInstance` - Time-bound compliance occurrences
- `WorkflowTask` - Task management with dependencies
- `Evidence` - Audit-ready file storage with versioning
- `AuditLog` - Immutable audit trail
- `Notification` - User notification system
- `Tag` - Evidence categorization

#### Seed Data
- 22 Indian GCC compliance masters across 6 categories:
  - GST (6 compliance types): GSTR-3B, GSTR-1, GSTR-9, GSTR-9C, GST Refund, ITC Reversal
  - Direct Tax (5 compliance types): TDS 24Q, TDS 26Q, Advance Tax, ITR, Form 3CD
  - Payroll (4 compliance types): PF ECR, ESI Challan, Form 5A, ESI Half-Yearly
  - MCA (3 compliance types): AOC-4, MGT-7, DIR-3 KYC
  - FEMA (2 compliance types): FC-GPR, ODI Return
  - FP&A (2 compliance types): Monthly Operating Review, Budget Reforecast
- 7 predefined roles with permission structures

#### API Endpoints (10 Scaffolded)
- `/api/v1/auth/*` - Authentication (login, logout, refresh, profile)
- `/api/v1/tenants/*` - Tenant management (CRUD)
- `/api/v1/entities/*` - Entity management (CRUD)
- `/api/v1/compliance/masters/*` - Compliance template management
- `/api/v1/compliance/instances/*` - Compliance instance management
- `/api/v1/workflow/tasks/*` - Task management
- `/api/v1/evidence/*` - Evidence upload, download, approval
- `/api/v1/audit-logs/*` - Audit trail access
- `/api/v1/dashboard/*` - Dashboard data (overview, overdue, upcoming)
- `/health` - Health check endpoint

#### Services & Engines (Structured, TODO Implementation)
- `compliance_engine.py` - Compliance instance generation logic
- `workflow_engine.py` - Workflow task orchestration
- `evidence_service.py` - S3 upload/download, hash verification
- `audit_service.py` - Audit log creation
- `notification_service.py` - Email and in-app notifications

#### Background Tasks (Celery)
- `compliance_tasks.py` - Instance generation and status recalculation
- `reminder_tasks.py` - T-3 days, due date, and overdue reminders

#### Frontend Infrastructure
- Next.js 14 App Router setup with TypeScript
- TailwindCSS configuration with custom RAG colors:
  - Green: `#10b981` (on track)
  - Amber: `#f59e0b` (at risk)
  - Red: `#ef4444` (overdue/critical)
- Axios HTTP client with JWT token interceptors
- Zustand state management for authentication (with localStorage persistence)
- React Query (TanStack Query) for data fetching (configured)
- React Hook Form + Zod for form validation (configured)

#### Frontend Components
- Layout components: `Header`, `Sidebar`
- UI components: `Button` (with variants), `RAGBadge` (status indicator)
- Page structures:
  - Dashboard layout with sidebar navigation
  - Login page scaffold
  - Dashboard page scaffold
  - Compliance list page scaffold
  - Evidence vault page scaffold

#### Frontend API Client
- Centralized Axios client with base URL configuration
- Automatic JWT token injection in request headers
- 401 error handling with token refresh
- API endpoint definitions for all backend routes
- TypeScript type definitions for API responses

#### Documentation
- **PRD.md** (45 pages) - Comprehensive product requirements:
  - Business objectives and target market analysis
  - 6 detailed user personas with pain points
  - 9 core features with technical specs
  - 22 compliance categories with due dates and penalties
  - Success metrics and KPIs
  - Non-functional requirements (performance, security, availability)
  - V1 scope and future roadmap (V2, V3, V4)
- **ARCHITECTURE.md** - System architecture with component responsibilities
- **SCHEMA_DESIGN.md** - Database design rationale and query patterns
- **IMPLEMENTATION_PLAN.md** - 5-phase implementation roadmap
- **PROGRESS.md** - Development progress tracking
- **PHASE1_SETUP_GUIDE.md** - Step-by-step developer setup
- **CLAUDE.md** - AI assistant development guidelines
- **README.md** - Project overview and quick start
- **CONTRIBUTING.md** - Contribution guidelines and code standards
- **LICENSE** - MIT License

#### Development Infrastructure
- Environment templates (`.env.example`) for backend and frontend
- Docker setup with `docker-compose.yml`:
  - PostgreSQL 15 with persistent volume
  - Redis 7 for caching
  - Backend service with hot reload
  - Celery worker and beat scheduler
  - Frontend service with hot reload
- Dockerfiles for backend (Python 3.11) and frontend (Node 18)
- `.dockerignore` files for optimized builds

#### CI/CD Pipelines (GitHub Actions)
- `backend-tests.yml` - Backend testing with PostgreSQL and Redis services
- `frontend-tests.yml` - Frontend linting, type checking, testing, and builds
- `code-quality.yml` - Black formatting, Flake8 linting, MyPy type checking

#### Developer Tools
- **Makefile** with common commands:
  - `make install` - Install all dependencies
  - `make dev` - Start development servers (backend + frontend)
  - `make test` - Run all tests
  - `make lint` - Run linters
  - `make format` - Format code
  - `make docker-up` - Start Docker containers
  - `make docker-down` - Stop Docker containers
  - `make migrate` - Run database migrations
  - `make seed` - Seed database with initial data
- **`.editorconfig`** - Consistent editor configuration across team
- ESLint, Prettier, and TypeScript configurations for frontend
- Black, Flake8, and MyPy configurations for backend

#### Test Infrastructure
- Backend test directories:
  - `tests/unit/` - Unit tests for models and services
  - `tests/integration/` - API endpoint integration tests
  - `tests/conftest.py` - Test fixtures and database setup
- Frontend test directories:
  - `src/__tests__/` - Component and integration tests
- Sample test files as templates

### Technical Details

**Backend Stack**:
- Python 3.11
- FastAPI 0.104.1
- SQLAlchemy (ORM)
- Alembic (migrations)
- PostgreSQL 15+
- Redis 7+
- Celery (background jobs)
- python-jose (JWT)
- boto3 (AWS S3)

**Frontend Stack**:
- Next.js 14 (App Router)
- TypeScript 5.x
- TailwindCSS 3.x
- Zustand (state management)
- React Query (data fetching)
- Axios (HTTP client)
- React Hook Form + Zod (forms)

**Database**:
- 15 tables with proper relationships
- Strategic indexes for performance
- JSONB fields for flexible metadata
- Trigram indexes for fuzzy search
- Multi-tenant isolation with `tenant_id`

**Deployment**:
- Docker and Docker Compose for local development
- GitHub Actions for CI/CD
- AWS infrastructure (PostgreSQL RDS, ElastiCache Redis, S3, ECS/Fargate)
- India data residency (Mumbai region: ap-south-1)

### Statistics

- **Total Files**: 90 files committed
- **Total Lines of Code**: 9,136 lines
- **Backend Files**: 47 Python files
- **Frontend Files**: 16 TypeScript/TSX files
- **Documentation**: 12 Markdown files
- **Models**: 11 SQLAlchemy models
- **Endpoints**: 10 API endpoint groups
- **Compliance Masters**: 22 templates
- **Test Files**: 3 sample tests

### Fixed

- Evidence model bug: `approved_at` field type changed from UUID to DateTime(timezone=True)

### Security

- Multi-tenant isolation enforced at application level (tenant_id in all queries)
- JWT-based authentication with access and refresh tokens
- Password hashing with bcrypt
- Role-based access control (RBAC) with 7 predefined roles
- Entity-level access control via `entity_access` table
- Evidence immutability after approval (`is_immutable` flag)
- Append-only audit logs for forensic analysis
- Environment variable management (no secrets in code)

---

## [0.0.1] - 2024-12-01 - Project Initialization

### Added
- Initial project repository setup
- Basic folder structure
- schema.sql with complete database schema

---

## Version Numbering

We use Semantic Versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Incompatible API changes (e.g., 1.0.0 → 2.0.0)
- **MINOR**: Backward-compatible functionality (e.g., 0.1.0 → 0.2.0)
- **PATCH**: Backward-compatible bug fixes (e.g., 0.1.0 → 0.1.1)

## Release Cycle

- **Phase 1** (Complete): Infrastructure and foundation - v0.1.0
- **Phase 2** (In Progress): Auth & RBAC - v0.2.0
- **Phase 3**: Compliance Engine - v0.3.0
- **Phase 4**: Evidence Vault - v0.4.0
- **Phase 5**: Dashboards & Reporting - v0.5.0
- **V1 GA** (General Availability): v1.0.0

---

**Core Principle**: "If it cannot stand up to an auditor, it does not ship." 🎯
