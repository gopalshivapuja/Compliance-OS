# Testing Strategy

**Version**: 1.0
**Last Updated**: December 2024
**Current Status**: Phase 3 Complete, Test Suite Foundation

---

## Overview

This document defines the testing strategy for Compliance OS, covering test categories, conventions, coverage requirements, and execution patterns.

**Core Principle**: "If it cannot stand up to an auditor, it does not ship."

---

## Test Categories

| Category | Location | Purpose | Phase |
|----------|----------|---------|-------|
| Unit Tests | `backend/tests/unit/` | Business logic isolation | All |
| Integration Tests | `backend/tests/integration/` | API endpoint testing | All |
| E2E Tests | `frontend/e2e/` | Critical user journeys | 11 |
| Component Tests | `frontend/src/__tests__/` | React component testing | 6+ |

---

## Directory Structure

```
backend/tests/
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── services/
│   │   ├── test_compliance_engine.py
│   │   ├── test_workflow_engine.py
│   │   ├── test_rag_calculator.py
│   │   └── test_due_date_calculator.py
│   ├── models/
│   │   └── test_model_validation.py
│   └── core/
│       └── test_security.py
├── integration/
│   └── api/
│       ├── test_auth.py
│       ├── test_tenants.py
│       ├── test_users.py
│       ├── test_entities.py
│       ├── test_compliance_masters.py
│       ├── test_compliance_instances.py
│       ├── test_workflow_tasks.py
│       ├── test_evidence.py
│       └── test_dashboard.py
└── e2e/
    └── workflows/
        └── test_full_compliance_cycle.py

frontend/
├── src/__tests__/
│   ├── components/
│   │   ├── Dashboard.test.tsx
│   │   ├── RAGBadge.test.tsx
│   │   └── ComplianceTable.test.tsx
│   ├── hooks/
│   │   ├── useAuth.test.ts
│   │   └── useDashboard.test.ts
│   ├── stores/
│   │   └── authStore.test.ts
│   └── api/
│       └── client.test.ts
└── e2e/
    ├── playwright.config.ts
    ├── login.spec.ts
    ├── compliance-flow.spec.ts
    └── evidence-upload.spec.ts
```

---

## Running Tests

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/integration/api/test_auth.py -v

# Run tests matching pattern
pytest -k "test_login" -v

# Run with parallel execution (faster)
pytest -n auto
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific test file
npm test -- Dashboard.test.tsx
```

### E2E Tests

```bash
cd frontend

# Run Playwright tests
npx playwright test

# Run with UI
npx playwright test --ui

# Run specific test
npx playwright test login.spec.ts
```

---

## Test Naming Conventions

### Backend (Python/pytest)

```python
# File naming
test_<module_name>.py

# Function naming
def test_<action>_<scenario>_<expected_result>():
    """Clear description of what is being tested."""
    pass

# Examples
def test_login_with_valid_credentials_returns_token():
def test_create_instance_without_entity_access_returns_403():
def test_rag_status_overdue_returns_red():
```

### Frontend (TypeScript/Jest)

```typescript
// File naming
<ComponentName>.test.tsx
<hookName>.test.ts

// Test naming
describe('ComponentName', () => {
  it('should <action> when <condition>', () => {});
});

// Examples
describe('RAGBadge', () => {
  it('should render green badge for Green status', () => {});
  it('should render red badge for overdue items', () => {});
});
```

---

## Fixture Patterns

### Backend Fixtures (conftest.py)

```python
@pytest.fixture
def db(request):
    """Create a database session with automatic rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for a test user."""
    # Login and return Authorization header
    pass

@pytest.fixture
def test_tenant(db):
    """Create a test tenant."""
    pass

@pytest.fixture
def test_user(db, test_tenant):
    """Create a test user with tenant."""
    pass
```

### Frontend Fixtures

```typescript
// test-utils.tsx
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

export function renderWithProviders(ui: React.ReactElement) {
  const testQueryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={testQueryClient}>{ui}</QueryClientProvider>
  );
}
```

---

## Coverage Requirements

| Phase | Backend Target | Frontend Target | E2E Target |
|-------|----------------|-----------------|------------|
| 3 | 70% | N/A | N/A |
| 4 | 75% | N/A | N/A |
| 5 | 75% | N/A | N/A |
| 6 | 75% | 50% | N/A |
| 7-10 | 80% | 70% | N/A |
| 11 | 80% | 80% | Critical paths |
| 12+ | 85% | 80% | All paths |

---

## CI/CD Test Execution

### GitHub Actions Workflow

Tests run automatically on:
- Pull requests to `main` and `develop`
- Pushes to `main` and `develop`

```yaml
# Backend tests
- pytest --cov=app --cov-report=xml

# Frontend tests
- npm test -- --coverage --watchAll=false

# E2E tests (Phase 11+)
- npx playwright test
```

### Coverage Reporting

Coverage reports are uploaded to Codecov for tracking:
- Backend: `backend/coverage.xml`
- Frontend: `frontend/coverage/coverage-final.json`

---

## Test Data Patterns

### Creating Test Data

```python
# Use factories for consistent test data
def create_test_compliance_instance(
    db: Session,
    tenant_id: UUID,
    entity_id: UUID,
    **kwargs
) -> ComplianceInstance:
    """Factory for creating test compliance instances."""
    defaults = {
        "status": "Pending",
        "rag_status": "Green",
        "due_date": date.today() + timedelta(days=30),
    }
    defaults.update(kwargs)

    instance = ComplianceInstance(
        tenant_id=tenant_id,
        entity_id=entity_id,
        **defaults
    )
    db.add(instance)
    db.commit()
    return instance
```

### Test Isolation

- Each test runs in its own transaction that rolls back
- No test should depend on another test's data
- Use fixtures for common setup, not shared state

---

## Security Testing

### Authentication Tests

- Test JWT token generation and validation
- Test token expiration handling
- Test refresh token rotation
- Test password hashing security

### Authorization Tests

- Test RBAC role enforcement
- Test entity-level access control
- Test multi-tenant isolation
- Test that users cannot access other tenants' data

### Input Validation Tests

- Test SQL injection prevention
- Test XSS prevention (frontend)
- Test file upload validation
- Test rate limiting

---

## Performance Testing (Phase 11+)

### Load Testing with Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class ComplianceOSUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_dashboard(self):
        self.client.get("/api/v1/dashboard/overview")

    @task(2)
    def list_instances(self):
        self.client.get("/api/v1/compliance-instances/")

    @task(1)
    def view_instance(self):
        self.client.get("/api/v1/compliance-instances/{id}")
```

### Performance Targets

| Endpoint | Target | Max |
|----------|--------|-----|
| Dashboard overview | <200ms | 500ms |
| List instances | <300ms | 800ms |
| Create instance | <500ms | 1s |
| Upload evidence | <2s | 5s |

---

## Debugging Test Failures

### Backend

```bash
# Run with verbose output
pytest -v --tb=long

# Drop into debugger on failure
pytest --pdb

# Run specific test with print output
pytest tests/integration/api/test_auth.py::test_login -v -s
```

### Frontend

```bash
# Debug mode
npm test -- --debug

# Update snapshots
npm test -- --updateSnapshot
```

---

## Mocking External Services

### S3 (Evidence Upload)

```python
@pytest.fixture
def mock_s3(mocker):
    """Mock S3 client for evidence tests."""
    mock = mocker.patch('boto3.client')
    mock.return_value.upload_fileobj.return_value = None
    mock.return_value.generate_presigned_url.return_value = "https://..."
    return mock
```

### Email (Notifications)

```python
@pytest.fixture
def mock_email(mocker):
    """Mock SendGrid for notification tests."""
    return mocker.patch('app.services.notification_service.send_email')
```

### Redis (Caching)

```python
@pytest.fixture
def mock_redis(mocker):
    """Mock Redis for cache tests."""
    return mocker.patch('app.core.redis.redis_client')
```

---

## Test Stub Templates

### Phase 4 Service Tests (Compliance Engine)

```python
# tests/unit/services/test_compliance_engine.py

"""
Compliance Engine Unit Tests

Tests for instance generation, due date calculation, and RAG status.
Phase 4 implementation.
"""

import pytest
from datetime import date, timedelta
from app.services.compliance_engine import (
    generate_monthly_instances,
    calculate_due_date,
    calculate_rag_status,
)


class TestInstanceGeneration:
    """Tests for compliance instance generation."""

    def test_generate_monthly_instances_creates_correct_count(self):
        """Monthly master should generate 12 instances per year."""
        # TODO: Implement in Phase 4
        pass

    def test_generate_quarterly_instances_creates_correct_count(self):
        """Quarterly master should generate 4 instances per year."""
        # TODO: Implement in Phase 4
        pass


class TestDueDateCalculation:
    """Tests for due date calculation rules."""

    def test_monthly_due_date_with_day_rule(self):
        """Monthly due date should fall on specified day."""
        # TODO: Implement in Phase 4
        pass

    def test_due_date_with_offset(self):
        """Due date should include offset days."""
        # TODO: Implement in Phase 4
        pass


class TestRAGStatusCalculation:
    """Tests for RAG status calculation."""

    def test_green_status_when_on_track(self):
        """Status should be Green when > 7 days to due date."""
        # TODO: Implement in Phase 4
        pass

    def test_amber_status_when_approaching_deadline(self):
        """Status should be Amber when <= 7 days to due date."""
        # TODO: Implement in Phase 4
        pass

    def test_red_status_when_overdue(self):
        """Status should be Red when past due date."""
        # TODO: Implement in Phase 4
        pass
```

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Library](https://testing-library.com/)

---

## Quick Reference

| Action | Command |
|--------|---------|
| Run backend tests | `cd backend && pytest -v` |
| Run frontend tests | `cd frontend && npm test` |
| Run E2E tests | `cd frontend && npx playwright test` |
| Check coverage | `pytest --cov=app` |
| Update snapshots | `npm test -- -u` |
