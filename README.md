# Compliance OS V1

**FP&A Control Tower for GCC Operations**

A comprehensive compliance management system designed for Global Capability Centers (GCCs) operating in India.

## 📋 Overview

Compliance OS is a multi-tenant SaaS application that helps GCCs manage their compliance obligations across GST, Direct Tax, Payroll, MCA, FEMA, and FP&A domains. It provides real-time visibility, workflow management, evidence vault, and audit-ready documentation.

## 🏗️ Project Structure

```
Compliance OS/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core configuration
│   │   ├── models/      # SQLAlchemy models (TODO)
│   │   ├── schemas/     # Pydantic schemas (TODO)
│   │   └── services/    # Business logic (TODO)
│   ├── alembic/         # Database migrations
│   └── requirements.txt
├── frontend/            # Next.js frontend
│   ├── src/
│   │   ├── app/        # Next.js App Router pages
│   │   ├── components/ # React components
│   │   └── lib/        # Utilities and API client
│   └── package.json
├── schema.sql          # PostgreSQL database schema
├── ARCHITECTURE.md      # System architecture documentation
├── SCHEMA_DESIGN.md     # Database schema design
└── PRD.md              # Product Requirements Document
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

### Backend Structure
- ✅ FastAPI application setup
- ✅ Database connection (PostgreSQL)
- ✅ Redis connection for caching
- ✅ JWT authentication utilities
- ✅ API route structure (all endpoints scaffolded)
- ✅ Service layer structure (placeholder)
- ✅ Celery configuration for background jobs
- ✅ Alembic setup for migrations
- ⏳ SQLAlchemy models (TODO)
- ⏳ Pydantic schemas (TODO)
- ⏳ Business logic implementation (TODO)

### Frontend Structure
- ✅ Next.js 14 App Router setup
- ✅ TypeScript configuration
- ✅ TailwindCSS with custom RAG colors
- ✅ API client with interceptors
- ✅ API endpoint definitions
- ✅ Auth store (Zustand)
- ✅ Basic layout components
- ✅ Dashboard page structure
- ⏳ Form components (TODO)
- ⏳ Data visualization (TODO)
- ⏳ Full UI implementation (TODO)

## 🚧 Next Steps

1. **Database Models**: Create SQLAlchemy models based on `schema.sql`
2. **API Schemas**: Create Pydantic schemas for request/response validation
3. **Business Logic**: Implement services (compliance engine, workflow engine, etc.)
4. **Authentication**: Implement login/logout endpoints
5. **CRUD Operations**: Implement all endpoint logic
6. **Frontend Pages**: Build out dashboard, compliance list, evidence vault
7. **Forms**: Add form components with validation
8. **Testing**: Add unit and integration tests

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

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines]

---

**Remember**: "If it cannot stand up to an auditor, it does not ship." 🎯

