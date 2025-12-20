# Compliance OS - Development Startup Guide

**Version**: 1.0
**Last Updated**: December 2024

This guide provides quick start commands to resume development work at any phase.

---

## Quick Start Commands

### 1. Start Backend Server

```bash
cd "/Users/gopal/Cursor/Compliance OS/backend"
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Verify**:
```bash
curl http://localhost:8000/health | python3 -m json.tool
```

### 2. Start Frontend Server

```bash
cd "/Users/gopal/Cursor/Compliance OS/frontend"
npm run dev
```

**Expected Output**:
```
▲ Next.js 14.0.4
- Local: http://localhost:3000
✓ Ready in ~2s
```

### 3. Start Background Workers (When Needed)

```bash
# Terminal 3: Celery Worker
cd "/Users/gopal/Cursor/Compliance OS/backend"
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info

# Terminal 4: Celery Beat (scheduler)
celery -A app.celery_app beat --loglevel=info
```

---

## Verify Everything Works

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend accessible
curl http://localhost:3000 | head -10

# Run backend tests
cd backend && source venv/bin/activate && pytest -v

# Run frontend tests
cd frontend && npm test
```

---

## Access URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API Docs | http://localhost:8000/docs |
| Backend ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

---

## Development Database Commands

### PostgreSQL

```bash
# Connect to development database
psql -U gopal -d compliance_os

# Connect to test database
psql -U gopal -d compliance_os_test

# Inside psql:
\dt           # List tables
\d table_name # Describe table
\q            # Quit
```

### Redis

```bash
redis-cli
> PING        # Should return PONG
> KEYS *      # List all keys
> FLUSHDB     # Clear database
> quit
```

### Alembic Migrations

```bash
cd backend && source venv/bin/activate

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

---

## Code Quality Commands

### Backend

```bash
cd backend && source venv/bin/activate

# Format code
black app/

# Lint code
flake8 app/

# Type check
mypy app/

# Run tests with coverage
pytest --cov=app --cov-report=term-missing -v
```

### Frontend

```bash
cd frontend

# Lint
npm run lint

# Type check
npm run type-check

# Format
npm run format

# Run tests
npm test
```

### Pre-commit (All)

```bash
# Run all hooks
pre-commit run --all-files

# Skip hooks temporarily (use sparingly)
git commit --no-verify
```

---

## Git Workflow

### Feature Development

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, then commit
git add .
git commit -m "feat: your feature description"

# Push branch
git push origin feature/your-feature-name

# Create PR on GitHub
```

### Commit Message Format

```
feat: Add new feature
fix: Fix bug in X
docs: Update documentation
test: Add tests for X
refactor: Refactor X for clarity
chore: Update dependencies
```

---

## Troubleshooting

### Backend Won't Start

**ModuleNotFoundError**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Database connection error**:
```bash
# Check PostgreSQL is running
brew services list
brew services start postgresql

# Verify connection
psql -U gopal -d compliance_os
```

**Redis connection error**:
```bash
# Check Redis is running
brew services list
brew services start redis

# Verify connection
redis-cli ping  # Should return PONG
```

### Frontend Won't Start

**Module not found**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Port 3000 in use**:
```bash
# Find process
lsof -ti:3000

# Kill process
kill -9 $(lsof -ti:3000)

# Or use different port
PORT=3001 npm run dev
```

### Tests Failing

**Database not clean**:
```bash
# Reset test database
psql -U gopal
DROP DATABASE compliance_os_test;
CREATE DATABASE compliance_os_test;
\q

cd backend && alembic upgrade head
```

**Import errors**:
```bash
export PYTHONPATH=/Users/gopal/Cursor/Compliance\ OS/backend
cd backend && pytest
```

---

## Environment Variables

### Backend (`.env`)

```env
DATABASE_URL=postgresql://gopal@localhost:5432/compliance_os
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Frontend (`.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Reference Documents

| Document | Purpose |
|----------|---------|
| `IMPLEMENTATION_PLAN.md` | Phase-by-phase roadmap |
| `PROGRESS.md` | Current development status |
| `ARCHITECTURE.md` | System design |
| `SCHEMA_DESIGN.md` | Database design |
| `CLAUDE.md` | AI assistant guidelines |
| `DEPLOYMENT.md` | Cloud deployment guide |
| `GIT_BEST_PRACTICES.md` | Git workflow |

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| System Admin | admin@testgcc.com | Admin123! |
| CFO | cfo@testgcc.com | CFO123! |
| Tax Lead | taxlead@testgcc.com | Tax123! |

---

## Daily Development Workflow

1. **Start servers** (Terminals 1-2)
2. **Check git status**: `git status && git log --oneline -5`
3. **Run tests**: `cd backend && pytest -v`
4. **Make changes**
5. **Verify with tests**
6. **Commit with meaningful message**
7. **Push to feature branch**

---

**Ready to code!**
