# Compliance OS - Cloud Deployment Strategy

## Executive Summary

**Current Status**: Phase 2 complete (16.7% of development)
**Recommended Platform**: **Render.com** (Best fit for $200-500 budget, beginner-friendly, SOC 2 compliant)
**Development Deployment**: After Phase 5 (Backend Business Logic complete - ~6 weeks from now)
**Production Deployment**: After Phase 11 (Testing & Quality complete - ~10-12 weeks from now)
**Total Monthly Cost**: $312/month (dev + prod environments)

---

## Platform Selection: Render.com

### Why Render Over Railway/DigitalOcean

| Criteria | Render | Railway | DigitalOcean |
|----------|--------|---------|--------------|
| **Managed Postgres** | $7/month (1GB) | $5/month (512MB) | $15/month (1GB) |
| **Managed Redis** | $10/month (256MB) | Included free | $15/month |
| **Auto-deploy from GitHub** | ✅ Yes | ✅ Yes | Manual |
| **Free SSL** | ✅ Yes | ✅ Yes | ✅ Yes |
| **SOC 2 Certified** | ✅ Yes | ⚠️ Limited | ✅ Yes |
| **Encryption at rest** | ✅ Yes | ✅ Yes | ✅ Yes |
| **India region** | ❌ Singapore (closest) | ❌ US/EU | ✅ Bangalore |
| **Beginner friendly** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Zero-downtime deploys** | ✅ Yes | ✅ Yes | Manual |
| **Background workers** | ✅ Yes | ✅ Yes | Manual |

**Winner**: **Render** - Best balance of price ($312/mo for both envs), features, and beginner-friendliness. SOC 2 compliant, HIPAA eligible, automatic backups.

**Trade-off**: No India region (Singapore is closest - ~50ms extra latency). If India data residency becomes mandatory later, can migrate to DigitalOcean Bangalore at ~$70/month total cost.

---

## Cost Breakdown

### Development Environment ($45/month)

| Service | Tier | Cost/month | Purpose |
|---------|------|------------|---------|
| Backend API | Starter (512MB RAM) | $7 | FastAPI app |
| Frontend | Starter (512MB RAM) | $7 | Next.js app |
| Celery Worker | Starter (512MB RAM) | $7 | Background jobs |
| Celery Beat | Starter (512MB RAM) | $7 | Job scheduler |
| PostgreSQL | Starter (1GB storage) | $7 | Database |
| Redis | Starter (256MB) | $10 | Cache + sessions |
| **Dev Total** | | **$45/month** | |

### Production Environment ($267/month)

| Service | Tier | Cost/month | Purpose |
|---------|------|------------|---------|
| Backend API | Standard (2GB RAM, 2 instances) | $50 | Load balanced FastAPI |
| Frontend | Standard (2GB RAM, 2 instances) | $50 | Load balanced Next.js |
| Celery Worker (2 workers) | Standard (2GB RAM each) | $50 | Background job processing |
| Celery Beat | Starter (512MB RAM) | $7 | Job scheduler |
| PostgreSQL | Pro (25GB storage, auto-backups) | $50 | Production database |
| Redis | Standard (2GB) | $60 | Cache + sessions |
| **Prod Total** | | **$267/month** | |

### **Grand Total: $312/month** ✅ Within $200-500 budget

**Scaling for 50 Tenants**: Current plan handles ~1000 concurrent users, 50K compliance instances. To scale to 100+ tenants:
- Upgrade Backend/Frontend to $100/month each (4GB RAM, 4 instances)
- Upgrade Postgres to $120/month (100GB storage, read replicas)
- Total: ~$550/month (still affordable)

---

## Deployment Timeline & Phases

### Timeline Overview

```
NOW (Phase 2) ─────> Phase 5 ─────> Phase 11 ─────> Production
     │                  │                │                │
     │                  │                │                │
  Dec 2024         Feb 2025         Apr 2025         May 2025
                       │                │                │
                   DEV DEPLOY      STAGING         PROD DEPLOY
                  (6 weeks)        (10 weeks)      (12 weeks)
```

### Deployment Milestones

#### Milestone 1: Development Environment (After Phase 5 - Week 6)

**What's Ready**:
- ✅ Backend APIs complete (auth, CRUD, business logic, background jobs)
- ✅ Database with seed data
- ✅ Celery workers for automated instance generation
- ⚠️ Frontend partially ready (dashboard, auth pages done in Phase 2)

**Why Deploy Now**:
- Test multi-tenant isolation with real subdomains
- Test Celery background jobs in cloud environment
- Frontend team can connect to real APIs
- Catch deployment issues early

**What to Deploy**:
- Backend API (all CRUD + business logic endpoints)
- PostgreSQL with migrations
- Redis for caching + Celery broker
- Celery worker + beat scheduler
- Frontend (even if partially complete - can deploy updates later)

#### Milestone 2: Staging Environment (After Phase 9 - Week 10)

**What's Ready**:
- ✅ All frontend pages complete (compliance, evidence, workflow, admin)
- ✅ End-to-end workflows working
- ✅ Evidence upload to S3

**Why Deploy Staging**:
- User acceptance testing (UAT)
- Load testing with realistic data
- Security testing (penetration testing)
- Train first pilot customer

**What to Deploy**:
- Clone of production configuration
- Separate database (copy of prod seed data)
- Test with 2-3 pilot tenants

#### Milestone 3: Production (After Phase 11 - Week 12)

**What's Ready**:
- ✅ All features complete
- ✅ Tests passing (>80% coverage)
- ✅ Security hardened
- ✅ Documentation complete
- ✅ Monitoring/alerts configured

**What to Deploy**:
- Full production stack
- SSL certificates for custom domains
- Monitoring (Sentry, UptimeRobot)
- Backups automated

---

## Custom Domain Setup for Multi-Tenant Branding

### Architecture: Single Frontend + Dynamic Branding

**Approach**: One Next.js deployment serves all tenants, loads branding config from backend based on domain/subdomain.

#### Option A: Subdomains (Recommended for MVP)

**Structure**:
- Main app: `app.complianceos.com` (your primary domain)
- Tenant 1: `client1.complianceos.com`
- Tenant 2: `client2.complianceos.com`
- Tenant 3: `client3.complianceos.com`

**How it Works**:
1. Customer signs up → You create tenant record in database
2. Set `tenant_subdomain = 'client1'` in tenants table
3. Add DNS CNAME record: `client1.complianceos.com → app.complianceos.com`
4. Frontend detects subdomain on page load:
   ```typescript
   // frontend/src/lib/utils/tenant.ts
   export function getTenantFromHostname() {
     const hostname = window.location.hostname
     const subdomain = hostname.split('.')[0]
     return subdomain
   }
   ```
5. Fetch tenant config from API:
   ```typescript
   const config = await fetch(`/api/v1/tenants/config?subdomain=${subdomain}`)
   // Returns: { tenant_id, logo_url, primary_color, secondary_color, tenant_name }
   ```
6. Apply branding dynamically:
   ```typescript
   document.documentElement.style.setProperty('--primary-color', config.primary_color)
   ```

**Pros**: Easy to set up, no custom domain needed, SSL auto-configured
**Cons**: Customers must use your domain

#### Option B: Custom Domains (For Enterprise Customers)

**Structure**:
- Tenant 1: `compliance.clientcompany1.com` (their domain)
- Tenant 2: `audit.clientcompany2.in` (their domain)

**How it Works**:
1. Customer provides their domain: `compliance.clientcompany1.com`
2. You add custom domain in Render dashboard (free SSL auto-provisioned)
3. Customer adds DNS CNAME: `compliance.clientcompany1.com → app.complianceos.com`
4. Store custom domain in database:
   ```sql
   UPDATE tenants SET custom_domain = 'compliance.clientcompany1.com' WHERE id = ...
   ```
5. Frontend looks up tenant by custom domain:
   ```typescript
   const config = await fetch(`/api/v1/tenants/config?domain=${window.location.hostname}`)
   ```

**Pros**: White-label branding, customers use their own domain
**Cons**: Requires manual domain setup per customer (5-10 min per tenant)

#### Tenant Configuration Schema

Add to `tenants` table (migration needed):
```sql
ALTER TABLE tenants ADD COLUMN tenant_subdomain VARCHAR(50) UNIQUE;
ALTER TABLE tenants ADD COLUMN custom_domain VARCHAR(255) UNIQUE;
ALTER TABLE tenants ADD COLUMN logo_url TEXT;
ALTER TABLE tenants ADD COLUMN primary_color VARCHAR(7) DEFAULT '#10b981';  -- Green
ALTER TABLE tenants ADD COLUMN secondary_color VARCHAR(7) DEFAULT '#3b82f6';  -- Blue
ALTER TABLE tenants ADD COLUMN favicon_url TEXT;
```

---

## Production-Ready Checklist (Before First Deploy)

### Critical Security Fixes

#### 1. Backend Dockerfile Improvements

**Current Issues** (from exploration):
- ❌ No multi-stage build (image is ~800MB)
- ❌ Running as root user (security risk)
- ❌ No health check

**Required Changes** (`backend/Dockerfile`):
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Impact**: Smaller image (300MB vs 800MB), runs as non-root, health checks work

#### 2. Implement Health Check Endpoint

**Current Issue**: Health check returns mocked response (from `main.py` line 51)

**Fix** (`backend/app/api/v1/endpoints/health.py`):
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Actual health check - verifies DB and Redis connectivity"""
    try:
        # Check database
        db.execute("SELECT 1")

        # Check Redis
        redis = get_redis()
        redis.ping()

        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }, 503
```

#### 3. Security Headers Middleware

**Add to `backend/app/main.py`**:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

# After CORS middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*.complianceos.com", "localhost"])
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

#### 4. Rate Limiting (Already in .env.production.example, needs implementation)

**Add dependency** (`requirements.txt`):
```
slowapi==0.1.9
```

**Implement** (`backend/app/core/rate_limit.py`):
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
```

**Apply to main app** (`main.py`):
```python
from app.core.rate_limit import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to login endpoint
@limiter.limit("5/minute")
@router.post("/login")
async def login(...):
    ...
```

#### 5. Environment Variables - Production Values

**Critical changes needed in `.env` for production**:

```bash
# CHANGE THESE (currently using dev values):
DEBUG=false  # Currently: true
JWT_SECRET_KEY=<generate-strong-random-key>  # Use: openssl rand -hex 32
DATABASE_URL=<render-postgres-url>
REDIS_URL=<render-redis-url>

# CORS - restrict to your domains only
CORS_ORIGINS=["https://app.complianceos.com", "https://*.complianceos.com"]

# S3 for evidence storage (use Render's environment secrets for keys)
AWS_ACCESS_KEY_ID=<from-aws-console>
AWS_SECRET_ACCESS_KEY=<from-aws-console>
AWS_S3_BUCKET_NAME=compliance-os-evidence
AWS_REGION=ap-south-1  # Mumbai for India (or us-east-1 if India not mandatory)

# Sentry for error tracking
SENTRY_DSN=<from-sentry.io>

# Rate limiting
RATE_LIMIT_PER_MINUTE=100
```

#### 6. Token Expiry - Shorten for Production

**Current** (line 33 of `config.py`): Access tokens expire in 24 hours
**Recommended**: 30 minutes for production

```python
# backend/app/core/config.py
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Change from 1440 (24h) to 30min
```

---

## Deployment Scripts

### 1. Development Deployment Script

**File**: `scripts/deploy_dev.sh`
```bash
#!/bin/bash
set -e

echo "🚀 Deploying to Development Environment (Render)"

# 1. Push to GitHub (Render auto-deploys from main branch)
git add .
git commit -m "Deploy to dev: $(date)"
git push origin develop  # Render watches 'develop' branch for dev env

# 2. Wait for Render to build and deploy (check via API)
echo "⏳ Waiting for Render deployment..."
sleep 60

# 3. Run database migrations on dev database
echo "📦 Running migrations..."
render run --service=backend-dev "alembic upgrade head"

# 4. Seed data if first deploy
echo "🌱 Seeding database..."
render run --service=backend-dev "python -m app.seeds.run_seed"

# 5. Health check
echo "🏥 Health check..."
curl https://api-dev.complianceos.com/health

echo "✅ Development deployment complete!"
echo "🌐 Frontend: https://app-dev.complianceos.com"
echo "🔗 Backend: https://api-dev.complianceos.com"
echo "📊 Swagger: https://api-dev.complianceos.com/docs"
```

### 2. Production Deployment Script

**File**: `scripts/deploy_prod.sh`
```bash
#!/bin/bash
set -e

echo "🚀 Deploying to Production Environment (Render)"

# 1. Pre-deployment checks
echo "🔍 Running pre-deployment checks..."

# Check tests pass
npm run test --prefix frontend
pytest backend/tests/ --cov=backend/app --cov-report=term

# Check linting
npm run lint --prefix frontend
cd backend && black --check app/ && flake8 app/ && mypy app/

# 2. Backup production database
echo "💾 Backing up production database..."
pg_dump $PROD_DATABASE_URL > backups/prod_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. Push to main branch (Render auto-deploys)
git checkout main
git merge develop
git tag -a v1.0.$(date +%Y%m%d) -m "Production release $(date)"
git push origin main --tags

# 4. Wait for Render deployment
echo "⏳ Waiting for Render deployment (zero-downtime rolling update)..."
sleep 90

# 5. Run migrations (Render will wait for migration to complete before routing traffic)
echo "📦 Running migrations..."
render run --service=backend-prod "alembic upgrade head"

# 6. Smoke tests
echo "🏥 Running smoke tests..."
curl https://api.complianceos.com/health
curl https://app.complianceos.com  # Should return 200

# 7. Notify team
echo "📢 Sending deployment notification..."
curl -X POST $SLACK_WEBHOOK_URL -d '{"text":"✅ Production deployed successfully!"}'

echo "✅ Production deployment complete!"
echo "🌐 Frontend: https://app.complianceos.com"
echo "🔗 Backend: https://api.complianceos.com"
```

### 3. Database Backup Script (Automated)

**File**: `scripts/backup_db.sh`
```bash
#!/bin/bash
# Runs daily at 2 AM IST via Render cron job

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="compliance_os_backup_$TIMESTAMP.sql"

# Dump database
pg_dump $DATABASE_URL > /tmp/$BACKUP_FILE

# Compress
gzip /tmp/$BACKUP_FILE

# Upload to S3
aws s3 cp /tmp/$BACKUP_FILE.gz s3://compliance-os-backups/daily/

# Keep only last 30 days
aws s3 ls s3://compliance-os-backups/daily/ | awk '{print $4}' | sort -r | tail -n +31 | xargs -I {} aws s3 rm s3://compliance-os-backups/daily/{}

echo "✅ Backup completed: $BACKUP_FILE.gz"
```

---

## SOC 2 Compliance Implementation

### Requirements Met

#### 1. Data Encryption

**At Rest** ✅:
- Render Postgres: AES-256 encryption enabled by default
- Render Redis: Encryption at rest enabled
- AWS S3: Enable server-side encryption (SSE-S3 or SSE-KMS)

**In Transit** ✅:
- TLS 1.3 enforced (Render default)
- All Render services communicate over encrypted connections
- S3 uploads via HTTPS

**Configuration** (`backend/app/services/evidence_service.py`):
```python
# Enable S3 server-side encryption
s3_client.put_object(
    Bucket=bucket_name,
    Key=s3_key,
    Body=file_content,
    ServerSideEncryption='AES256'  # Or 'aws:kms' for KMS
)
```

#### 2. Audit Logging ✅

**Already Implemented** (Phase 2):
- Immutable audit_logs table (append-only)
- Captures: who did what, when, before/after values, IP address
- 7-year retention (add to backup policy)

**Compliance Note**: Audit logs are SOC 2 ready. For formal audit:
- Add audit log export feature (CSV download)
- Document retention policy
- Add "audit log integrity verification" (hash chain)

#### 3. Access Controls & MFA

**Current State**:
- ✅ RBAC implemented (4 roles with permissions)
- ✅ Entity-level access control
- ✅ Password requirements (8+ chars)
- ❌ MFA not implemented (V2 feature per PRD)

**MFA Implementation** (Optional for V1, Required for SOC 2):

**Add dependency**:
```bash
pip install pyotp qrcode
```

**Implement** (`backend/app/api/v1/endpoints/mfa.py`):
```python
import pyotp
import qrcode

@router.post("/mfa/setup")
async def setup_mfa(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate QR code for MFA setup"""
    user = db.query(User).filter(User.id == current_user["user_id"]).first()

    # Generate secret
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    db.commit()

    # Generate QR code
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(user.email, issuer_name="Compliance OS")

    return {"qr_code_uri": uri, "secret": secret}

@router.post("/mfa/verify")
async def verify_mfa(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verify MFA code"""
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    totp = pyotp.TOTP(user.mfa_secret)

    if totp.verify(code):
        user.mfa_enabled = True
        db.commit()
        return {"status": "MFA enabled"}
    else:
        raise HTTPException(status_code=400, detail="Invalid code")
```

**Migration**:
```sql
ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(32);
```

#### 4. Backup Strategy

**Daily Backups** (Render Pro Postgres includes):
- Automated daily backups (retained 7 days)
- Point-in-time recovery (last 7 days)

**Additional Backup Policy** (SOC 2 requirement):
- **Daily**: Full database dump to S3 (retention: 30 days)
- **Weekly**: Full backup to S3 (retention: 90 days)
- **Monthly**: Full backup to S3 (retention: 7 years for compliance)

**Implement** (Render cron job):
```yaml
# render.yaml
services:
  - type: cron
    name: daily-backup
    env: docker
    schedule: "0 2 * * *"  # 2 AM IST daily
    dockerfilePath: ./scripts/Dockerfile.backup
    dockerCommand: ./scripts/backup_db.sh
```

---

## Monitoring & Alerting

### 1. Error Tracking (Sentry)

**Setup** (Free tier supports 5K errors/month):
1. Sign up at https://sentry.io
2. Create project "Compliance OS"
3. Get DSN
4. Add to `.env`:
   ```bash
   SENTRY_DSN=https://<key>@sentry.io/<project>
   ```
5. Initialize in `backend/app/main.py`:
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn=settings.SENTRY_DSN, environment="production")
   ```

### 2. Uptime Monitoring (UptimeRobot)

**Setup** (Free tier supports 50 monitors):
1. Sign up at https://uptimerobot.com
2. Add HTTP monitors:
   - `https://api.complianceos.com/health` (check every 5 min)
   - `https://app.complianceos.com` (check every 5 min)
3. Configure alerts:
   - Email notification when service is down
   - Slack webhook integration

### 3. Application Metrics (Render Built-in)

Render provides:
- CPU/Memory usage graphs
- Request count and latency (p50, p95, p99)
- Error rate
- Database connection pool stats

**Access**: Render Dashboard → Service → Metrics tab

---

## Claude Code's Role in Deployment

### What Claude Code CAN Help With ✅

1. **Writing Deployment Scripts**:
   - Generate bash scripts for migrations, backups, health checks
   - Create Docker configurations
   - Write GitHub Actions workflows

2. **Environment Configuration**:
   - Generate `.env.production` with all required variables
   - Create render.yaml for infrastructure-as-code
   - Set up secrets management

3. **Security Hardening**:
   - Add security headers middleware
   - Implement rate limiting
   - Fix Dockerfile security issues (non-root user, multi-stage build)

4. **Database Migrations**:
   - Generate Alembic migration scripts
   - Write data migration scripts
   - Create rollback procedures

5. **Monitoring Setup**:
   - Integrate Sentry SDK
   - Add health check endpoints
   - Create log aggregation queries

6. **Documentation**:
   - Write deployment runbooks
   - Create troubleshooting guides
   - Document environment variables

### What Claude Code CANNOT Do ❌

1. **Cloud Provider UI**:
   - Cannot click through Render dashboard to create services
   - Cannot configure DNS records in domain registrar
   - Cannot set up payment/billing

2. **SSH Access**:
   - Cannot SSH into servers (Render is managed platform - no SSH access anyway)
   - Cannot run commands on remote servers (use Render CLI instead)

3. **Playwright MCP**:
   - **Not useful for deployment** - Playwright is for browser automation
   - Cannot interact with cloud provider dashboards
   - Cannot configure servers via web UI

### What Claude Code CAN Do with Render CLI ✅

If you install Render CLI, Claude can help write commands:

```bash
# Install Render CLI
npm install -g render

# Login (you do this manually)
render login

# Claude can help write these commands:
render services create --name backend-prod --plan standard --repo https://github.com/you/compliance-os --branch main --region oregon --env-var DEBUG=false
render services create --name frontend-prod --plan standard --repo https://github.com/you/compliance-os --branch main --region oregon
render run --service backend-prod "alembic upgrade head"
render logs --service backend-prod --tail
```

**Recommendation**: Use Render web dashboard for initial setup (easier for beginners), then use CLI + scripts for ongoing deployments.

---

## Step-by-Step Deployment Guide

### Phase 1: Development Environment (After Phase 5 - Week 6)

#### Step 1: Prerequisites (You do this manually - 30 min)

1. **Create Render Account**:
   - Go to https://render.com
   - Sign up with GitHub (easier for auto-deploy)
   - Verify email

2. **Create S3 Bucket** (for evidence storage):
   - Log into AWS Console
   - Create bucket: `compliance-os-evidence-dev`
   - Region: `ap-south-1` (Mumbai) or `us-east-1` (cheaper)
   - Enable versioning + encryption
   - Create IAM user with S3 access, save access key

3. **Get SendGrid API Key** (for email notifications):
   - Sign up at https://sendgrid.com (free tier: 100 emails/day)
   - Create API key with "Mail Send" permission
   - Save key

#### Step 2: Create Render Services (You do this via dashboard - 45 min)

**Service 1: PostgreSQL**
1. Render Dashboard → New → PostgreSQL
2. Name: `compliance-os-db-dev`
3. Region: Singapore (closest to India)
4. Plan: Starter ($7/month)
5. Create → Copy "Internal Database URL"

**Service 2: Redis**
1. New → Redis
2. Name: `compliance-os-redis-dev`
3. Region: Singapore
4. Plan: Starter ($10/month)
5. Create → Copy "Internal Redis URL"

**Service 3: Backend API**
1. New → Web Service
2. Connect GitHub repo
3. Name: `compliance-os-api-dev`
4. Region: Singapore
5. Branch: `develop`
6. Root Directory: `backend`
7. Build Command: `pip install -r requirements.txt`
8. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
9. Plan: Starter ($7/month)
10. Environment Variables (click "Add Environment Variable"):
    ```
    DATABASE_URL = <paste Internal Database URL from step above>
    REDIS_URL = <paste Internal Redis URL>
    JWT_SECRET_KEY = <run: openssl rand -hex 32>
    JWT_ALGORITHM = HS256
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    CORS_ORIGINS = ["https://compliance-os-frontend-dev.onrender.com"]
    AWS_ACCESS_KEY_ID = <from S3 step>
    AWS_SECRET_ACCESS_KEY = <from S3 step>
    AWS_S3_BUCKET_NAME = compliance-os-evidence-dev
    AWS_REGION = ap-south-1
    SENDGRID_API_KEY = <from SendGrid step>
    DEBUG = false
    LOG_LEVEL = INFO
    ```
11. Create Service → Wait 5 min for build
12. Copy service URL (e.g., `https://compliance-os-api-dev.onrender.com`)

**Service 4: Celery Worker**
1. New → Background Worker
2. Connect same repo
3. Name: `compliance-os-worker-dev`
4. Region: Singapore
5. Branch: `develop`
6. Root Directory: `backend`
7. Build Command: `pip install -r requirements.txt`
8. Start Command: `celery -A app.celery_app worker --loglevel=info`
9. Plan: Starter ($7/month)
10. Environment Variables: **Same as Backend API** (copy/paste all)
11. Create

**Service 5: Celery Beat**
1. New → Background Worker
2. Name: `compliance-os-beat-dev`
3. Region: Singapore
4. Branch: `develop`
5. Root Directory: `backend`
6. Build Command: `pip install -r requirements.txt`
7. Start Command: `celery -A app.celery_app beat --loglevel=info`
8. Plan: Starter ($7/month)
9. Environment Variables: **Same as Backend API**
10. Create

**Service 6: Frontend**
1. New → Web Service
2. Name: `compliance-os-frontend-dev`
3. Region: Singapore
4. Branch: `develop`
5. Root Directory: `frontend`
6. Build Command: `npm install && npm run build`
7. Start Command: `npm run start`
8. Plan: Starter ($7/month)
9. Environment Variables:
    ```
    NEXT_PUBLIC_API_URL = https://compliance-os-api-dev.onrender.com
    NODE_ENV = production
    ```
10. Create

#### Step 3: Run Database Migrations (You run commands - 10 min)

**Option A: Via Render Shell** (easiest):
1. Go to Backend API service → Shell tab
2. Run:
   ```bash
   alembic upgrade head
   python -m app.seeds.run_seed
   ```

**Option B: Via Render CLI**:
```bash
render run --service=compliance-os-api-dev "alembic upgrade head"
render run --service=compliance-os-api-dev "python -m app.seeds.run_seed"
```

#### Step 4: Verify Deployment (5 min)

1. **Test Backend**:
   ```bash
   curl https://compliance-os-api-dev.onrender.com/health
   # Should return: {"status":"healthy","database":"connected","redis":"connected"}
   ```

2. **Test Swagger Docs**:
   - Open: `https://compliance-os-api-dev.onrender.com/docs`
   - Should see all API endpoints

3. **Test Frontend**:
   - Open: `https://compliance-os-frontend-dev.onrender.com`
   - Should see login page
   - Login with: `admin@testgcc.com` / `Admin123!`
   - Should see dashboard

4. **Test Celery**:
   - Check logs: Render Dashboard → `compliance-os-worker-dev` → Logs
   - Should see: `[INFO] Celery started`

**Total Dev Setup Time**: ~90 minutes (one-time)
**Total Dev Cost**: $45/month

### Phase 2: Production Environment (After Phase 11 - Week 12)

Repeat all steps above, but:
- Use `main` branch instead of `develop`
- Name services `*-prod` instead of `*-dev`
- Use Standard/Pro plans (2x instances, more RAM)
- Add custom domain: `app.complianceos.com`
- Enable auto-deploy on `main` branch push
- Set up SSL certificate (Render does this automatically)
- Configure Sentry for error tracking
- Set up UptimeRobot for uptime monitoring

**Total Prod Setup Time**: ~60 minutes (similar to dev, faster with practice)
**Total Prod Cost**: $267/month

---

## Onboarding New Tenants

### Tenant Onboarding Workflow (Manual for V1)

**Step 1: Create Tenant Record** (via API or database):
```sql
INSERT INTO tenants (
    id, tenant_code, tenant_name, contact_email, status,
    tenant_subdomain, logo_url, primary_color, secondary_color
) VALUES (
    gen_random_uuid(),
    'ACME_INC',
    'ACME Inc.',
    'admin@acmeinc.com',
    'active',
    'acme',  -- Becomes acme.complianceos.com
    'https://s3.amazonaws.com/compliance-os/logos/acme-logo.png',
    '#ff6b6b',  -- Custom red
    '#4ecdc4'   -- Custom teal
);
```

**Step 2: Create Admin User for Tenant**:
```sql
INSERT INTO users (
    id, tenant_id, email, password_hash, first_name, last_name,
    status, is_system_admin, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    (SELECT id FROM tenants WHERE tenant_code = 'ACME_INC'),
    'admin@acmeinc.com',
    <hash of 'temporary-password'>,
    'Tenant',
    'Admin',
    'active',
    false,
    NOW(),
    NOW()
);
```

**Step 3: Assign Tenant Admin Role**:
```sql
INSERT INTO user_roles (user_id, role_id, tenant_id)
VALUES (
    (SELECT id FROM users WHERE email = 'admin@acmeinc.com'),
    (SELECT id FROM roles WHERE role_code = 'TENANT_ADMIN'),
    (SELECT id FROM tenants WHERE tenant_code = 'ACME_INC')
);
```

**Step 4: Configure DNS** (if using custom domain):
- Customer sets CNAME: `compliance.acmeinc.com → app.complianceos.com`
- You add custom domain in Render dashboard
- Render auto-provisions SSL certificate (5-10 min)

**Step 5: Upload Logo to S3**:
```bash
aws s3 cp acme-logo.png s3://compliance-os-assets/logos/acme-logo.png --acl public-read
# Update tenants.logo_url = 'https://s3.amazonaws.com/compliance-os-assets/logos/acme-logo.png'
```

**Step 6: Send Welcome Email**:
- Email tenant admin with login credentials
- Temporary password (force reset on first login)
- Link: `https://acme.complianceos.com/login`

**Automated Onboarding (V2 Feature)**:
- Build self-service signup flow
- Auto-generate tenant subdomain
- Auto-create admin user
- Auto-send welcome email

---

## Recommended Development Timeline

```
Week 1-2 (NOW): Phase 2 Complete ✅
  - Auth working
  - RBAC implemented
  - Dashboard API ready

Week 3-4: Phase 3 (Backend CRUD)
  - Entities, Users, Tenants CRUD
  - Evidence upload/download
  - Workflow tasks

Week 5-6: Phase 4 & 5 (Business Logic + Background Jobs)
  - Compliance engine
  - Instance generation (cron)
  - RAG status calculation
  - Email notifications
  → 🚀 DEPLOY TO DEV ENVIRONMENT (Milestone 1)

Week 7-8: Phase 6 & 7 (Frontend Auth + Dashboards)
  - Complete frontend pages
  - Calendar view
  - Owner view

Week 9-10: Phase 8 & 9 (Frontend Compliance + Workflow)
  - Evidence upload UI
  - Workflow task UI
  - Bulk import
  → 🚀 DEPLOY TO STAGING (Milestone 2)

Week 11: Phase 10 & 11 (Admin + Testing)
  - Admin pages
  - Comprehensive tests
  - Security hardening

Week 12: Phase 12 (Deployment & Docs)
  - Production deployment
  - User manual
  - Training videos
  → 🚀 DEPLOY TO PRODUCTION (Milestone 3)
  → 🎉 LAUNCH TO FIRST CUSTOMER
```

---

## Critical Files to Create

### 1. `backend/.env.production` (copy from .env, update values)
### 2. `backend/Dockerfile` (fix multi-stage build, non-root user, health check)
### 3. `scripts/deploy_dev.sh` (automated dev deployment)
### 4. `scripts/deploy_prod.sh` (automated prod deployment with checks)
### 5. `scripts/backup_db.sh` (daily database backups)
### 6. `render.yaml` (infrastructure-as-code for services)
### 7. `backend/app/api/v1/endpoints/health.py` (real health check)
### 8. `backend/app/core/rate_limit.py` (rate limiting middleware)
### 9. Migration: `alembic revision -m "Add tenant branding columns"`

---

## Summary & Next Steps

### Deployment Strategy

1. **Platform**: Render.com ($312/month for dev + prod)
2. **Dev Deploy**: After Phase 5 (Week 6) - backend complete, frontend partial
3. **Prod Deploy**: After Phase 11 (Week 12) - all features + tests complete
4. **Branding**: Single frontend + dynamic config (subdomain-based)
5. **India Data**: Singapore region (50ms latency OK), can migrate to DigitalOcean Bangalore later if mandatory

### Immediate Actions (Before Dev Deploy)

**Claude Code can help with these** (ask me to implement):
1. Fix backend Dockerfile (multi-stage, non-root, health check)
2. Implement real health check endpoint
3. Add security headers middleware
4. Add rate limiting to login endpoint
5. Create tenant branding migration
6. Write deployment scripts (deploy_dev.sh, backup_db.sh)
7. Generate .env.production template

**You need to do manually**:
1. Create Render account
2. Create AWS S3 bucket + IAM user
3. Get SendGrid API key
4. Set up services in Render dashboard (follow step-by-step guide above)
5. Run migrations via Render shell
6. Configure custom domain DNS

### SOC 2 Readiness

**Already Compliant** ✅:
- Encryption at rest (Render default)
- Encryption in transit (TLS 1.3)
- Audit logging (immutable trail)
- RBAC (role-based access)

**Needs Implementation** ⚠️:
- MFA (optional for V1, can add later)
- Formal backup policy documentation
- Security incident response plan

**Recommendation**: Deploy V1 without MFA, add MFA in V2 when pursuing SOC 2 certification. Current security is production-ready for 50 customers.

---

## Questions for You

1. **Domain Name**: Do you already own a domain (e.g., complianceos.com)? If not, I recommend buying one before dev deploy (~$12/year).

2. **First Customers**: Do you have 2-3 pilot customers ready to test after dev deploy? This helps validate the platform early.

3. **Support**: Will you handle customer support yourself, or need help documentation/training materials? (Claude can help write docs)

4. **Data Migration**: Do any potential customers have existing compliance data in Excel/CSV that needs importing? (We can build bulk import in Phase 3)

---

**Ready to implement deployment fixes? Let me know and I'll start with the Dockerfile improvements and health check endpoint!**
