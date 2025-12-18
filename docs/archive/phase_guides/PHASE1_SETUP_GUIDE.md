# Phase 1 Setup Guide - Database Foundation

## What We've Built

✅ **All SQLAlchemy Models Created** (11 models):
- `base.py` - Base model with mixins (UUID, Timestamp, Audit, TenantScoped)
- `tenant.py` - Tenant model
- `role.py` - Role model with user_roles junction table
- `user.py` - User model with password hashing
- `entity.py` - Entity model with entity_access junction table
- `compliance_master.py` - ComplianceMaster with JSONB fields
- `compliance_instance.py` - ComplianceInstance with RAG status
- `workflow_task.py` - WorkflowTask model
- `tag.py` - Tag model
- `evidence.py` - Evidence model with versioning
- `audit_log.py` - AuditLog (append-only)
- `notification.py` - Notification model

✅ **Seed Data Created**:
- 25+ Indian GCC compliance templates (GST, Direct Tax, Payroll, MCA, FEMA, FP&A)
- 7 system roles (System Admin, Tenant Admin, CFO, Tax Lead, HR Lead, Company Secretary, FP&A Lead)

✅ **Configuration Files**:
- `.env` - Environment variables for local development
- Alembic configured to discover all models

---

## Prerequisites

Before proceeding, ensure you have:

1. **PostgreSQL 15+** installed and running
2. **Python 3.11+** installed
3. **Redis 7+** installed and running (for later phases, but good to have now)

### Quick PostgreSQL Setup (macOS)

```bash
# Install PostgreSQL via Homebrew (if not already installed)
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Create database
createdb compliance_os

# Verify connection
psql compliance_os -c "SELECT version();"
```

### Quick PostgreSQL Setup (Linux/Ubuntu)

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres createdb compliance_os

# Create user (optional, for non-postgres user)
sudo -u postgres createuser --superuser $USER
```

### Quick PostgreSQL Setup (Windows)

1. Download installer from https://www.postgresql.org/download/windows/
2. Install with default settings
3. Open pgAdmin or psql terminal
4. Create database: `CREATE DATABASE compliance_os;`

---

## Step-by-Step Execution

### Step 1: Navigate to Backend Directory

```bash
cd "Compliance OS/backend"
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python3 -m venv venv

# Activate venv
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

You should see `(venv)` prefix in your terminal.

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- FastAPI, Uvicorn
- SQLAlchemy, Alembic, psycopg2-binary
- Pydantic, python-jose, passlib
- Redis, Celery
- And all other dependencies

**Expected time**: 2-3 minutes

### Step 4: Verify Environment Variables

Check the `.env` file created in the backend directory:

```bash
cat .env
```

**Important**: Update `DATABASE_URL` if your PostgreSQL setup is different:

```env
# Default (works for most local setups)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/compliance_os

# If you created a different user or password:
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/compliance_os
```

### Step 5: Generate Alembic Migration

```bash
# From backend directory with venv activated
alembic revision --autogenerate -m "Initial schema - all tables"
```

**Expected output**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'tenants'
INFO  [alembic.autogenerate.compare] Detected added table 'roles'
...
  Generating /path/to/alembic/versions/abc123_initial_schema_all_tables.py ...  done
```

This creates a migration file in `alembic/versions/`.

### Step 6: Review Migration File (Optional but Recommended)

```bash
# List migration files
ls alembic/versions/

# View the generated migration
cat alembic/versions/*_initial_schema_all_tables.py
```

Verify that:
- All 11 tables are being created
- Foreign keys are correct
- Indexes are present

### Step 7: Apply Migrations

```bash
alembic upgrade head
```

**Expected output**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Initial schema - all tables
```

This creates all tables in the `compliance_os` database.

### Step 8: Verify Database Schema

Connect to PostgreSQL and verify tables:

```bash
# Connect to database
psql compliance_os

# List all tables
\dt

# You should see:
# tenants, users, roles, user_roles, entities, entity_access,
# compliance_masters, compliance_instances, workflow_tasks,
# evidence, evidence_tag_mappings, tags, audit_logs, notifications
```

View a specific table structure:

```sql
\d tenants
\d compliance_masters
\d compliance_instances
```

Exit psql:
```bash
\q
```

### Step 9: Run Seed Script

```bash
# From backend directory with venv activated
python3 -m app.seeds.run_seed
```

**Expected output**:
```
======================================================================
COMPLIANCE OS - DATABASE SEED SCRIPT
======================================================================

Seeding roles...
  ✓ Created role: SYSTEM_ADMIN
  ✓ Created role: TENANT_ADMIN
  ✓ Created role: CFO
  ✓ Created role: TAX_LEAD
  ✓ Created role: HR_LEAD
  ✓ Created role: COMPANY_SECRETARY
  ✓ Created role: FPA_LEAD
Roles seeding completed!

Seeding compliance masters...
  ✓ Created: GSTR-1 - GSTR-1 - Outward Supplies Return
  ✓ Created: GSTR-3B - GSTR-3B - Summary Return
  ... (total 25+ compliances)

Compliance masters seeding completed!
  Created: 25
  Skipped: 0
  Total: 25

======================================================================
SEEDING COMPLETED SUCCESSFULLY!
======================================================================
```

### Step 10: Verify Seed Data

```bash
# Connect to database
psql compliance_os

# Check roles
SELECT role_code, role_name FROM roles;

# Check compliance masters
SELECT compliance_code, compliance_name, category, frequency
FROM compliance_masters
ORDER BY category, compliance_code;

# Exit
\q
```

You should see:
- 7 roles (SYSTEM_ADMIN, TENANT_ADMIN, CFO, TAX_LEAD, HR_LEAD, COMPANY_SECRETARY, FPA_LEAD)
- 25+ compliance masters across 6 categories

---

## Phase 1 Verification Checklist

Run through this checklist to ensure everything is working:

- [ ] Virtual environment created and activated
- [ ] All dependencies installed successfully
- [ ] Alembic migration generated
- [ ] Migration applied without errors
- [ ] All 14 tables created in database (11 main + 3 junction tables)
- [ ] 7 roles seeded
- [ ] 25+ compliance masters seeded
- [ ] Can connect to database and query tables

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'app'"

**Solution**: Make sure you're in the `backend` directory and venv is activated.

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### Issue: "psycopg2.OperationalError: could not connect to server"

**Solution**: PostgreSQL is not running or connection details are wrong.

```bash
# Check if PostgreSQL is running
# macOS:
brew services list | grep postgresql

# Linux:
sudo systemctl status postgresql

# Start if not running:
brew services start postgresql@15  # macOS
sudo systemctl start postgresql    # Linux
```

Verify DATABASE_URL in `.env` matches your PostgreSQL setup.

### Issue: "sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable)"

**Solution**: Tables already exist. Either:
1. Drop and recreate database:
   ```bash
   dropdb compliance_os
   createdb compliance_os
   alembic upgrade head
   ```

2. Or downgrade and re-run migrations:
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

### Issue: "Seed script fails with IntegrityError"

**Solution**: Data already seeded. The seed script checks for existing data, but if partial seeding occurred:

```bash
# Connect to database
psql compliance_os

# Check what exists
SELECT COUNT(*) FROM roles;
SELECT COUNT(*) FROM compliance_masters;

# If you want to re-seed, clear tables:
TRUNCATE roles, compliance_masters CASCADE;
\q

# Re-run seed
python3 -m app.seeds.run_seed
```

---

## Next Steps

Congratulations! Phase 1 is complete. You now have:
✅ A fully structured database with all tables
✅ Pre-loaded roles and compliance templates
✅ A working Alembic migration system

### Ready for Phase 2: Backend Authentication & Authorization

Phase 2 will implement:
- Login/logout endpoints
- JWT token generation and validation
- RBAC middleware
- Audit logging service

To start Phase 2:
```bash
# Make sure backend server can start (won't have auth yet, but should run)
uvicorn app.main:app --reload

# Visit API docs
open http://localhost:8000/docs
```

The server should start without errors and show the FastAPI Swagger UI with placeholder endpoints.

---

## Database Backup (Optional but Recommended)

After successful Phase 1 completion, backup your database:

```bash
# Create backups directory
mkdir -p ../backups

# Backup database
pg_dump compliance_os > ../backups/phase1_complete_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh ../backups/
```

To restore if needed:
```bash
dropdb compliance_os
createdb compliance_os
psql compliance_os < ../backups/phase1_complete_YYYYMMDD_HHMMSS.sql
```

---

## Summary

**Phase 1 Achievements**:
- ✅ 11 SQLAlchemy models with proper relationships
- ✅ Alembic migrations working
- ✅ 25+ Indian GCC compliance templates
- ✅ 7 system roles
- ✅ Database fully seeded and ready

**Time Taken**: ~30-45 minutes (including setup)

**Ready to proceed to Phase 2!** 🚀
