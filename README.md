# Compliance OS V1

**FP&A Control Tower for GCC Operations**

A comprehensive compliance management system designed for Global Capability Centers (GCCs) operating in India.

**Phases 1-6**: ✅ Complete | **Overall Progress**: 50% (6/12 phases) | **Current Phase**: Phase 7 - Frontend Dashboard Views

## 📋 Overview

Compliance OS is a multi-tenant SaaS application that helps GCCs manage their compliance obligations across GST, Direct Tax, Payroll, MCA, FEMA, and FP&A domains. It provides real-time visibility, workflow management, evidence vault, and audit-ready documentation.

## 🏗️ Project Structure

```
Compliance OS/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints (✅ 31 endpoints)
│   │   ├── core/        # Core configuration
│   │   ├── models/      # SQLAlchemy models (✅ 11 models)
│   │   ├── schemas/     # Pydantic schemas (✅ Complete)
│   │   ├── services/    # Business logic (✅ 4 engines)
│   │   ├── tasks/       # Celery background tasks (✅ Complete)
│   │   └── seeds/       # Database seed data (22 compliance masters)
│   ├── alembic/         # Database migrations (✅ Complete)
│   ├── tests/           # Test suite (✅ 583 tests)
│   └── requirements.txt
├── frontend/            # Next.js frontend
│   ├── src/
│   │   ├── app/        # Next.js App Router pages
│   │   ├── components/ # React components
│   │   └── lib/        # Utilities and API client
│   ├── public/          # Static assets
│   └── package.json
├── schema.sql          # PostgreSQL database schema
├── PRD.md              # Product Requirements Document
├── ARCHITECTURE.md      # System architecture documentation
├── SCHEMA_DESIGN.md     # Database schema design
├── IMPLEMENTATION_PLAN.md # Phase-wise roadmap
├── PHASE1_SETUP_GUIDE.md # Developer setup guide
└── CLAUDE.md           # AI assistant instructions
```

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.11+, PostgreSQL 15+, Redis 7+
- **Frontend**: Node.js 18+

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations (after creating models)
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

Backend API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

Frontend will be available at http://localhost:3000

## 🛠️ Utility Scripts

The `scripts/` directory contains helpful utilities for common development tasks:

### Quick Setup
For first-time contributors, use the automated setup script:
```bash
./scripts/setup.sh
```

This will:
- Check prerequisites (Python, Node.js, Docker)
- Set up backend virtual environment and dependencies
- Install frontend dependencies
- Create `.env` files from templates
- Provide next steps guidance

### Health Checks
Verify all services are running correctly:
```bash
./scripts/health-check.sh
```

Checks:
- Docker container status (PostgreSQL, Redis, Backend, Celery, Frontend)
- HTTP endpoint health (Backend API, Frontend)
- Database and Redis connectivity

**Output Legend:**
- ✓ Green: Service is healthy
- ⚠ Yellow: Service is running but may have issues
- ✗ Red: Service is not running or unreachable

For more scripts and detailed usage, see [scripts/README.md](./scripts/README.md)

## 📚 Documentation

- **[PRD.md](./PRD.md)**: Product Requirements Document
- **[ARCHITECTURE.md](./ARCHITECTURE.md)**: System architecture and component responsibilities
- **[SCHEMA_DESIGN.md](./SCHEMA_DESIGN.md)**: Database schema design and rationale
- **[schema.sql](./schema.sql)**: PostgreSQL schema SQL

## 🎯 Key Features (V1)

- ✅ **Compliance Master Library**: Structured definitions of compliance obligations
- ✅ **Compliance Instance Engine**: Time-bound instances with status tracking
- ✅ **Workflow & Ownership**: Task assignment, approvals, escalations
- ✅ **Evidence Vault**: Secure file storage with versioning and approval
- ✅ **Dashboards**: Executive Control Tower, Compliance Calendar, Owner View
- ✅ **Audit Trail**: Immutable logging of all actions

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Cache**: Redis
- **Background Jobs**: Celery
- **Authentication**: JWT (python-jose)
- **File Storage**: AWS S3 (or compatible)

### Frontend
- **Framework**: Next.js 14 (React)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: Zustand
- **Data Fetching**: React Query (TanStack Query)
- **HTTP Client**: Axios
- **Forms**: React Hook Form + Zod

## 📁 What's Included

### Backend Structure (Phases 1-5 Complete)
- ✅ FastAPI application setup with CORS and compression
- ✅ Database connection (PostgreSQL with connection pooling)
- ✅ Redis connection for caching and sessions
- ✅ JWT authentication system (login, logout, refresh, token validation)
- ✅ RBAC middleware and entity access control
- ✅ Audit logging service (immutable trail with before/after snapshots)
- ✅ Dashboard API (overview, overdue, upcoming, owner heatmap)
- ✅ Compliance instances API with RBAC enforcement
- ✅ Audit logs API (CFO/System Admin only)
- ✅ SQLAlchemy models (11 complete models with relationships)
- ✅ Database migrations with Alembic
- ✅ Seed data (22 compliance masters across 6 categories)
- ✅ Pydantic schemas (complete for all modules)
- ✅ Service layer (audit, entity_access, compliance_engine, workflow_engine, notification, evidence)
- ✅ CRUD endpoints (entities, users, tenants, compliance masters, instances, workflow tasks, evidence)
- ✅ Evidence upload/download with file validation and SHA-256 hashing
- ✅ Compliance Engine (due date calculation, RAG status, period calculation)
- ✅ Workflow Engine (task creation, state transitions, sequence enforcement)
- ✅ Notification Service (in-app notifications, 8 notification types)
- ✅ Email Service (SendGrid integration, 7 Jinja2 templates)
- ✅ Celery background tasks (reminder engine, instance generation, email notifications)
- ✅ Backend tests (583 tests, 100% pass rate)

### Frontend Structure (Phase 2 Partial)
- ✅ Next.js 14 App Router setup
- ✅ TypeScript configuration
- ✅ TailwindCSS with custom RAG colors (Green #10b981, Amber #f59e0b, Red #ef4444)
- ✅ API client with JWT interceptors
- ✅ Auth store (Zustand with localStorage persistence)
- ✅ Login page with form validation (React Hook Form + Zod)
- ✅ Executive Control Tower dashboard (RAG cards, category chart, overdue table)
- ✅ Compliance instances list page
- ✅ Audit log viewer (role-restricted)
- ✅ React Query hooks (useDashboard, useCompliance, useAuditLogs)
- ✅ Dashboard components (RAGStatusCard, CategoryChart, OverdueTable, ComplianceTable, AuditLogTable)
- ⏳ Full layout components (Header, Sidebar - TODO Phase 6)
- ⏳ Form components (TODO Phase 6-10)
- ⏳ Remaining pages (entities, users, workflow, evidence - TODO Phase 6-10)

## 🚧 Next Steps (Phase 6 - Frontend Authentication & Layout)

1. **Login Page Enhancement**: Improve existing login with better error handling
2. **Protected Route Middleware**: Next.js middleware for auth checking
3. **Dashboard Layout**: Sidebar navigation with responsive design
4. **User Profile Page**: Settings and preferences
5. **Entity Management UI**: CRUD interface for entities
6. **User Management UI**: User administration pages

See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for detailed roadmap.

**Phases 1-5 Complete**: Backend is production-ready with 31 endpoints, 4 business logic engines, email service with SendGrid, and 583 passing tests!

## 🔐 Security Considerations

- Multi-tenant isolation enforced at application level
- JWT tokens for authentication
- Role-based access control (RBAC)
- Entity-level access control
- Evidence immutability after approval
- Append-only audit logs

## 📊 Database Schema

The database schema is defined in `schema.sql` and includes:
- Tenants, Users, Roles
- Entities (legal entities)
- Compliance Masters and Instances
- Workflow Tasks
- Evidence (with versioning)
- Audit Logs (append-only)

See [SCHEMA_DESIGN.md](./SCHEMA_DESIGN.md) for detailed design rationale.

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)

## 📝 License

MIT License - See [LICENSE](./LICENSE) for details

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](./CONTRIBUTING.md) before submitting pull requests.

## 📖 Additional Documentation

- [CHANGELOG.md](./CHANGELOG.md) - Version history and changes
- [PHASE1_SETUP_GUIDE.md](./PHASE1_SETUP_GUIDE.md) - Detailed setup instructions
- [PROGRESS.md](./PROGRESS.md) - Development progress tracking

---

**Remember**: "If it cannot stand up to an auditor, it does not ship." 🎯
