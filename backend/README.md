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
│   ├── models/                # SQLAlchemy models (TODO)
│   ├── schemas/               # Pydantic schemas (TODO)
│   ├── services/              # Business logic services (TODO)
│   │   ├── compliance_engine.py
│   │   ├── workflow_engine.py
│   │   ├── evidence_service.py
│   │   ├── audit_service.py
│   │   └── notification_service.py
│   └── tasks/                 # Celery background tasks (TODO)
│       ├── compliance_tasks.py
│       └── reminder_tasks.py
├── alembic/                   # Database migrations
├── tests/                     # Tests (TODO)
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
# Run tests (TODO: Add tests)
pytest

# With coverage
pytest --cov=app
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

## 🚧 TODO

- [ ] Create SQLAlchemy models based on schema.sql
- [ ] Create Pydantic schemas for request/response validation
- [ ] Implement business logic in services
- [ ] Implement authentication endpoints
- [ ] Implement CRUD endpoints
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Set up CI/CD pipeline

## 📚 API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔐 Security Notes

- Always use HTTPS in production
- Rotate `JWT_SECRET_KEY` regularly
- Use strong passwords for database
- Enable rate limiting in production
- Review CORS origins before deployment
