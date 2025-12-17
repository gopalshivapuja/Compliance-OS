# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Compliance OS V1** is a multi-tenant SaaS application for GCC (Global Capability Centers) compliance management in India. It manages GST, Direct Tax, Payroll, MCA, FEMA, and FP&A compliance obligations with RAG status tracking, workflow management, evidence vault, and full audit trail.

**Core Principle**: "If it cannot stand up to an auditor, it does not ship."

## Tech Stack

### Backend (FastAPI/Python)
- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL 15+ with SQLAlchemy
- **Cache**: Redis 7+ for session/caching
- **Background Jobs**: Celery with Redis
- **Auth**: JWT tokens (python-jose)
- **Storage**: AWS S3 (boto3) for evidence files
- **Migrations**: Alembic

### Frontend (Next.js/TypeScript)
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: TailwindCSS (custom RAG colors: Green #10b981, Amber #f59e0b, Red #ef4444)
- **State**: Zustand (auth), React Query (data fetching)
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Axios with interceptors

## Common Commands

### Backend Development
```bash
cd backend

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
alembic downgrade -1

# Background jobs
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat --loglevel=info
celery -A app.celery_app flower  # Monitoring UI

# Code quality
black app/              # Format
flake8 app/             # Lint
mypy app/               # Type check
pytest                  # Tests
pytest --cov=app        # With coverage
```

### Frontend Development
```bash
cd frontend

# Setup and run
npm install
npm run dev             # Development server (localhost:3000)

# Build and production
npm run build           # Production build
npm run start           # Production server

# Code quality
npm run lint            # ESLint
npm run type-check      # TypeScript checking
npm run format          # Prettier formatting
npm run format:check    # Check formatting
```

## Architecture Overview

### Multi-Tenant Design
- **Application-level isolation**: Every query filters by `tenant_id`
- **Denormalized `tenant_id`**: Present in compliance_instances table to avoid expensive joins on dashboard queries
- **Access control**: `entity_access` table controls user-entity permissions
- **JWT includes**: `tenant_id`, `user_id`, `roles[]` for request context

### Core Business Logic Flow

**Compliance Instance Generation (Background Job)**:
1. Cron scheduler triggers daily
2. Reads `compliance_masters` with frequency rules
3. Generates `compliance_instances` for applicable entities
4. Calculates `due_date` from `due_date_rule` JSONB
5. Creates workflow tasks based on master definition
6. Notifies assigned owners

**RAG Status Calculation**:
- **Green**: On track (due date > 7 days away, no blockers)
- **Amber**: At risk (due date < 7 days, or dependencies pending)
- **Red**: Overdue or critical blocker

**Evidence Workflow**:
1. File uploaded → Stored in S3, SHA-256 hash generated
2. Record created with `approval_status = 'Pending'`
3. Approver reviews → Sets 'Approved' or 'Rejected'
4. Once approved → `is_immutable = true` (cannot delete)
5. Updates create new version with `parent_evidence_id` link

**Reminder Engine** (runs hourly):
- T-3 days: Notify owner
- Due date: Notify approver
- +3 days overdue: Escalate to CFO

### Database Schema Key Points

**Master vs Instance Separation**:
- `compliance_masters`: Templates/definitions (frequency, rules, defaults)
- `compliance_instances`: Time-bound occurrences for specific entities with status

**Audit-Ready Design**:
- `audit_logs` table is append-only (never update/delete)
- Every mutable table has `created_at`, `updated_at`, `created_by`, `updated_by`
- Evidence immutability after approval prevents tampering
- JSONB fields store before/after snapshots for complete auditability

**JSONB Fields**:
- `due_date_rule`: Flexible rule engine for varied compliance types
  ```json
  {"type": "monthly", "day": 11, "offset_days": 0}
  ```
- `dependencies`: Array of compliance codes that must complete first
- `metadata`: Tenant-specific configurations

**Performance Indexes**:
- `idx_*_tenant_id` on all tables for fast tenant filtering
- `idx_compliance_instances_entity_status_due` composite for common dashboard queries
- Trigram indexes (`pg_trgm`) on name fields for fuzzy search
- Descending indexes on `created_at` for recent-first queries

### File Structure

**Backend** (`backend/app/`):
- `main.py`: FastAPI app entry point
- `api/v1/endpoints/`: REST API endpoints (auth, tenants, entities, compliance, workflow, evidence, etc.)
- `core/`: config.py (Pydantic settings), database.py, redis.py, security.py (JWT/password)
- `models/`: SQLAlchemy ORM models (TODO: needs implementation)
- `schemas/`: Pydantic request/response schemas (TODO: needs implementation)
- `services/`: Business logic (compliance_engine, workflow_engine, evidence_service, audit_service)
- `tasks/`: Celery background tasks for instance generation, reminders
- `alembic/`: Database migration files

**Frontend** (`frontend/src/`):
- `app/`: Next.js App Router pages
  - `(dashboard)/`: Dashboard routes group (dashboard, compliance, evidence)
  - `login/`: Authentication page
  - `layout.tsx`: Root layout with providers
- `components/layout/`: Header, Sidebar navigation
- `components/ui/`: Reusable components (Button, RAGBadge)
- `lib/api/`: Axios client with JWT interceptors, API endpoint definitions
- `lib/store/`: Zustand stores (auth-store.ts)
- `types/`: TypeScript type definitions

## Development Workflow

### When Creating SQLAlchemy Models
1. Reference `schema.sql` for exact table definitions
2. Include all audit fields: `created_at`, `updated_at`, `created_by`, `updated_by`
3. Add `tenant_id` to all tenant-scoped tables
4. Use UUIDs for primary keys (security best practice)
5. Define relationships with proper foreign keys
6. After creating models, run: `alembic revision --autogenerate -m "Add [table] model"`

### When Creating API Endpoints
1. Create Pydantic schemas first (request/response validation)
2. Implement business logic in service layer, not directly in endpoint
3. Always filter by `tenant_id` from JWT context
4. Check entity-level access via `entity_access` table
5. Log actions to `audit_logs` for CREATE/UPDATE/DELETE/APPROVE/REJECT
6. Return proper HTTP status codes (201 for create, 204 for delete, etc.)

### When Working with Evidence
- Validate file type and size before S3 upload
- Generate SHA-256 hash for integrity verification
- Respect `is_immutable` flag (prevent deletion if true)
- Version updates by creating new rows with `version++` and `parent_evidence_id`
- Use signed URLs for secure downloads with expiration

### When Implementing Workflow Tasks
- Enforce sequence: tasks must complete in `sequence_order`
- Check `parent_task_id` dependencies before allowing completion
- Support assignment to user OR role (role resolves to users at runtime)
- Status transitions: Pending → In Progress → Completed/Rejected
- Trigger next task in workflow on completion

## Testing Strategy

**Backend Tests** (pytest):
- Unit tests for services (compliance_engine, workflow_engine)
- Integration tests for API endpoints with test database
- Mock external services (S3, email, Slack)

**Frontend Tests**:
- Component tests with testing-library
- E2E tests for critical flows (login, compliance creation, evidence upload)

## Security Considerations

- **Multi-tenant isolation**: ALWAYS filter by `tenant_id` in queries
- **Entity access**: Verify user has access to entity via `entity_access` table
- **JWT validation**: Middleware checks token on protected routes
- **Evidence immutability**: Once approved, cannot be deleted (audit requirement)
- **Input validation**: All inputs validated via Pydantic (backend) and Zod (frontend)
- **SQL injection**: Use parameterized queries (SQLAlchemy handles this)
- **File upload**: Validate file types, size limits, scan for viruses (optional ClamAV)
- **Secrets management**: Never commit `.env` files, use environment variables

## Current Implementation Status

**Completed**:
- FastAPI application scaffold with CORS, compression
- Database connection setup (SQLAlchemy)
- Redis connection for caching
- JWT authentication utilities
- API route structure (all endpoints scaffolded)
- Celery configuration for background jobs
- Alembic migration setup
- Next.js 14 App Router setup with TypeScript
- TailwindCSS with custom RAG colors
- API client with JWT interceptors
- Auth store (Zustand)
- Basic layout components

**TODO (High Priority)**:
- Create SQLAlchemy models from schema.sql
- Create Pydantic request/response schemas
- Implement business logic in service layer (compliance engine, workflow engine)
- Implement authentication endpoints (login, logout, token refresh)
- Implement CRUD operations for all endpoints
- Build frontend dashboard with RAG status visualization
- Implement evidence upload/download with S3
- Add form components with validation
- Write unit and integration tests

## Key Files Reference

- `schema.sql`: Complete PostgreSQL schema (source of truth for database)
- `ARCHITECTURE.md`: Detailed system architecture and component responsibilities
- `SCHEMA_DESIGN.md`: Database design rationale and query patterns
- `README.md`: Project overview and quick start
- `backend/app/core/config.py`: All environment configuration
- `backend/requirements.txt`: Python dependencies
- `frontend/package.json`: Frontend dependencies and scripts
- `frontend/src/lib/api/client.ts`: Axios client with JWT interceptors
- `frontend/src/lib/api/endpoints.ts`: API endpoint definitions

## API Documentation

When backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Deployment Notes

**India Data Residency**: Deploy database and storage in Mumbai region (AWS ap-south-1) to keep data within India borders.

**Environment Variables Required**:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret for JWT signing (rotate regularly)
- `AWS_S3_BUCKET_NAME`: S3 bucket for evidence storage
- `SENDGRID_API_KEY`: Email service (optional for V1)
- `SLACK_WEBHOOK_URL`: Slack notifications (optional for V1)
