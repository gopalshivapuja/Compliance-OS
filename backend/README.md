# Compliance OS - Backend API

FastAPI backend for Compliance OS V1.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Virtual environment (recommended)

### Installation

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Set up database:**
```bash
# Create database
createdb compliance_os

# Run migrations (after creating models)
alembic upgrade head
```

5. **Run the server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   └── v1/
│   │       ├── router.py       # Main API router
│   │       └── endpoints/      # API endpoint modules
│   │           ├── auth.py
│   │           ├── tenants.py
│   │           ├── entities.py
│   │           ├── compliance_masters.py
│   │           ├── compliance_instances.py
│   │           ├── workflow_tasks.py
│   │           ├── evidence.py
│   │           ├── audit_logs.py
│   │           └── dashboard.py
│   ├── core/
│   │   ├── config.py           # Settings (Pydantic)
│   │   ├── database.py        # SQLAlchemy setup
│   │   ├── redis.py           # Redis client
│   │   ├── security.py        # JWT, password hashing
│   │   └── dependencies.py   # FastAPI dependencies
│   ├── models/                # SQLAlchemy ORM models (11 core + 3 junction)
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/              # Business logic services
│   │   ├── compliance_engine.py
│   │   ├── workflow_engine.py
│   │   ├── evidence_service.py
│   │   ├── audit_service.py
│   │   ├── notification_service.py
│   │   └── email_service.py
│   └── tasks/                 # Celery background tasks
│       ├── compliance_tasks.py
│       └── reminder_tasks.py
├── alembic/                   # Database migrations
├── tests/                     # Unit and integration tests (583 tests)
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

## 🔧 Configuration

Key environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `AWS_S3_BUCKET_NAME`: S3 bucket for evidence storage
- `SENDGRID_API_KEY`: Email service API key

## 🗄️ Database Migrations

Using Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## 🔄 Background Jobs

Using Celery for background tasks:

```bash
# Start Celery worker
celery -A app.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A app.celery_app beat --loglevel=info

# Start Flower (monitoring)
celery -A app.celery_app flower
```

## 🧪 Testing

```bash
# Run all tests (583 tests)
pytest

# With coverage
pytest --cov=app

# Run specific test file
pytest tests/integration/api/test_dashboard.py -v
```

## 📝 Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

## ✅ Implementation Status (Phases 1-5 Complete)

- [x] SQLAlchemy models (11 core + 3 junction tables)
- [x] Pydantic schemas for all modules
- [x] Business logic services (compliance, workflow, evidence, audit, notification, email)
- [x] Authentication endpoints (JWT with refresh tokens)
- [x] CRUD endpoints (31 API endpoints)
- [x] Compliance Engine (due date calculation, RAG status, period calculation)
- [x] Workflow Engine (task creation, state transitions, sequence enforcement)
- [x] Notification Service (in-app notifications, 8 types)
- [x] Email Service (SendGrid integration, 7 Jinja2 templates)
- [x] Celery tasks (reminder engine, instance generation, email notifications)
- [x] Unit tests + Integration tests (583 tests, 100% pass rate)
- [x] CI/CD pipeline (GitHub Actions)

## 📚 API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Health Endpoints
- `GET /api/v1/health/health` - Basic health check
- `GET /api/v1/health/live` - Kubernetes liveness probe
- `GET /api/v1/health/ready` - Kubernetes readiness probe

## 🔐 Security Notes

- Always use HTTPS in production
- Rotate `JWT_SECRET_KEY` regularly
- Use strong passwords for database
- Enable rate limiting in production
- Review CORS origins before deployment
