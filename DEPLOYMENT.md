# Compliance OS V1 - Deployment Guide

**Version**: 1.0
**Last Updated**: December 2024
**Status**: Phases 1-3 Complete, Pre-Phase 4 Review

---

## Executive Summary

| Aspect | Decision |
|--------|----------|
| **Platform** | Render.com |
| **Monthly Cost** | $312-500 (dev + prod) |
| **Architecture** | Modular Monolith (FastAPI + Next.js) |
| **Primary Region** | Singapore (50-80ms from India) |
| **Backup Region** | US-East (failover) |
| **Uptime SLA** | 99.99% |
| **RTO** | 1 hour |
| **RPO** | 5 minutes |

---

## Platform Selection: Render.com

### Why Render.com?

| Criteria | Render | Railway | DigitalOcean | AWS/GCP |
|----------|--------|---------|--------------|---------|
| **Managed Postgres** | $7/mo | $5/mo | $15/mo | $20+/mo |
| **Managed Redis** | $10/mo | Free | $15/mo | $15+/mo |
| **Auto-deploy GitHub** | ✅ | ✅ | Manual | Manual |
| **Free SSL** | ✅ | ✅ | ✅ | ✅ |
| **SOC 2 Certified** | ✅ | Limited | ✅ | ✅ |
| **Beginner Friendly** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Zero-downtime Deploy** | ✅ | ✅ | Manual | Manual |
| **India Region** | Singapore | US/EU | Bangalore | Mumbai |

**Winner**: Render - Best balance of cost, features, and ease of use. SOC 2 compliant, HIPAA eligible.

**Trade-off**: Singapore region adds ~50ms latency vs Mumbai. Acceptable for V1; migrate to DigitalOcean Bangalore later if India data residency required.

---

## Cost Breakdown

### Development Environment - $45/month

| Service | Plan | Cost/Month |
|---------|------|------------|
| Backend API (FastAPI) | Starter (512MB RAM) | $7 |
| Frontend (Next.js) | Starter (512MB RAM) | $7 |
| PostgreSQL | Starter (1GB storage) | $7 |
| Redis | Starter (256MB) | $10 |
| Celery Worker | Starter (512MB RAM) | $7 |
| Celery Beat | Starter (512MB RAM) | $7 |
| **Total Dev** | | **$45/month** |

### Production Environment - $267/month

| Service | Plan | Cost/Month |
|---------|------|------------|
| Backend API | Standard (2GB RAM, 2 instances) | $50 |
| Frontend | Standard (2GB RAM, 2 instances) | $50 |
| PostgreSQL Pro | 25GB, auto-backups | $50 |
| Redis Standard | 2GB | $60 |
| Celery Workers (2) | Standard (2GB each) | $50 |
| Celery Beat | Starter | $7 |
| **Total Prod** | | **$267/month** |

**Grand Total**: $312/month (dev + prod)

### Scaling (50+ Tenants)
- Upgrade to Standard plans: ~$550/month
- Handles 1000+ concurrent users, 50K+ compliance instances

---

## Deployment Timeline

```
Phase 3 (NOW) ────> Phase 5 ────> Phase 11 ────> Production
     │                  │              │              │
  Dec 2024          Feb 2025       Apr 2025      May 2025
                        │              │              │
                    DEV DEPLOY    STAGING      PROD DEPLOY
```

### Milestone 1: Dev Environment (After Phase 5)
- Backend APIs complete
- Celery workers running
- Frontend partially complete
- Test multi-tenant isolation in cloud

### Milestone 2: Staging (After Phase 9)
- Full frontend complete
- UAT with pilot customers
- Load and security testing

### Milestone 3: Production (After Phase 11)
- All features complete
- Tests passing (>80% coverage)
- Monitoring configured

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Load Balancer (Render)                    │
│               SSL Termination + Rate Limiting                │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │  Backend x2  │ │  Backend x2  │ │  Frontend x2 │
    │  (FastAPI)   │ │  (FastAPI)   │ │  (Next.js)   │
    └──────────────┘ └──────────────┘ └──────────────┘
              │               │               │
              └───────┬───────┘               │
                      │                       │
              ┌───────┴───────┐               │
              ▼               ▼               │
    ┌──────────────┐ ┌──────────────┐         │
    │  PostgreSQL  │ │    Redis     │◄────────┘
    │   Primary    │ │   Sessions   │
    └──────────────┘ └──────────────┘

    ┌──────────────────────────────────────────┐
    │         Background Jobs (Celery)         │
    ├──────────────────────────────────────────┤
    │  Worker 1  │  Worker 2  │  Beat (Cron)  │
    └──────────────────────────────────────────┘
                        │
                        ▼
              ┌──────────────┐
              │    AWS S3    │
              │  (Evidence)  │
              └──────────────┘
```

---

## Step-by-Step Deployment

### Prerequisites (Manual - 30 min)

1. **Create Render Account**: https://render.com (connect GitHub)
2. **Create AWS S3 Bucket**: `compliance-os-evidence-dev` in ap-south-1
3. **Get SendGrid API Key**: https://sendgrid.com (free tier: 100 emails/day)

### Create Services (Render Dashboard - 45 min)

**Service 1: PostgreSQL**
- Name: `compliance-os-db-dev`
- Region: Singapore
- Plan: Starter ($7/month)
- Copy: Internal Database URL

**Service 2: Redis**
- Name: `compliance-os-redis-dev`
- Region: Singapore
- Plan: Starter ($10/month)
- Copy: Internal Redis URL

**Service 3: Backend API**
- Name: `compliance-os-api-dev`
- Region: Singapore
- Branch: `develop`
- Root: `backend`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Plan: Starter ($7/month)
- Environment Variables:
  ```
  DATABASE_URL=<Internal Database URL>
  REDIS_URL=<Internal Redis URL>
  JWT_SECRET_KEY=<openssl rand -hex 32>
  JWT_ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=30
  REFRESH_TOKEN_EXPIRE_DAYS=7
  AWS_S3_BUCKET_NAME=compliance-os-evidence-dev
  AWS_ACCESS_KEY_ID=<from AWS>
  AWS_SECRET_ACCESS_KEY=<from AWS>
  AWS_REGION=ap-south-1
  DEBUG=false
  ```

**Service 4: Celery Worker**
- Name: `compliance-os-worker-dev`
- Type: Background Worker
- Start: `celery -A app.celery_app worker --loglevel=info`
- Environment: Same as Backend

**Service 5: Celery Beat**
- Name: `compliance-os-beat-dev`
- Type: Background Worker
- Start: `celery -A app.celery_app beat --loglevel=info`
- Environment: Same as Backend

**Service 6: Frontend**
- Name: `compliance-os-frontend-dev`
- Root: `frontend`
- Build: `npm install && npm run build`
- Start: `npm run start`
- Environment:
  ```
  NEXT_PUBLIC_API_URL=https://compliance-os-api-dev.onrender.com
  NODE_ENV=production
  ```

### Run Migrations (10 min)

Via Render Shell or CLI:
```bash
alembic upgrade head
python -m app.seeds.run_seed
```

### Verify Deployment

```bash
# Health check
curl https://compliance-os-api-dev.onrender.com/health
# Expected: {"status":"healthy","database":"connected","redis":"connected"}

# Swagger docs
open https://compliance-os-api-dev.onrender.com/docs

# Frontend
open https://compliance-os-frontend-dev.onrender.com
# Login: admin@testgcc.com / Admin123!
```

---

## Security Hardening

### 1. Docker Security (Multi-Stage Build)

```dockerfile
# Stage 1: Build
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime (Non-Root)
FROM python:3.11-slim
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Security Headers

```python
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

### 3. Rate Limiting

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(...): ...
```

### 4. JWT Token Security
- Access tokens: 30 minutes
- Refresh tokens: 7 days
- Rotate JWT_SECRET_KEY quarterly

---

## Monitoring & Alerting

### Free Tier Stack

| Service | Purpose | Cost |
|---------|---------|------|
| Sentry | Error tracking | $0 (5K errors/month) |
| UptimeRobot | Health checks | $0 (50 monitors) |
| Render Metrics | CPU/Memory/Latency | Built-in |
| Slack Webhooks | Alerts | $0 |

### Health Check Endpoint

```python
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db.execute("SELECT 1") else "error",
        "redis": "connected" if redis.ping() else "error"
    }
```

---

## Backup & Recovery

### Automated Backups
- **Render PostgreSQL Pro**: Daily backups, 7-day retention
- **Additional**: Daily S3 backup (30 days), Monthly (7 years for compliance)

### Backup Script

```bash
#!/bin/bash
# scripts/backup_db.sh
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > /tmp/backup_$TIMESTAMP.sql
gzip /tmp/backup_$TIMESTAMP.sql
aws s3 cp /tmp/backup_$TIMESTAMP.sql.gz s3://compliance-os-backups/daily/
```

### Disaster Recovery (RTO: 1 hour)

```bash
#!/bin/bash
# scripts/disaster_recovery.sh
# 1. Promote read replica
render run --service=postgres-backup "pg_ctl promote"
# 2. Update DNS
render domains update app.complianceos.com --region us-east
# 3. Scale backup services
render services scale backend-backup --plan standard --instances 2
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: CI/CD
on:
  push:
    branches: [develop, main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Backend Tests
        run: cd backend && pytest --cov=app
      - name: Frontend Tests
        run: cd frontend && npm test

  deploy-dev:
    needs: test
    if: github.ref == 'refs/heads/develop'
    steps:
      - run: curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK_DEV }}

  deploy-prod:
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - run: curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK_PROD }}
```

---

## Pre-Launch Checklist

### Security
- [ ] Security headers middleware active
- [ ] Rate limiting on login endpoint
- [ ] HTTPS enforced (SSL certificates)
- [ ] JWT tokens expiring in 30 minutes
- [ ] Docker containers running as non-root

### Infrastructure
- [ ] Multi-region deployment configured
- [ ] Database backups automated
- [ ] Health check endpoint working
- [ ] Monitoring and alerts configured

### Application
- [ ] All migrations applied
- [ ] Seed data loaded
- [ ] CORS configured correctly
- [ ] Email notifications working
- [ ] Evidence upload/download tested

### CI/CD
- [ ] GitHub Actions workflow working
- [ ] Automated tests passing
- [ ] Rollback procedure tested

---

## Quick Reference

### URLs (Development)
- **Frontend**: https://compliance-os-frontend-dev.onrender.com
- **Backend API**: https://compliance-os-api-dev.onrender.com
- **Swagger Docs**: https://compliance-os-api-dev.onrender.com/docs

### Common Commands

```bash
# Run migrations
render run --service=backend-dev "alembic upgrade head"

# Seed data
render run --service=backend-dev "python -m app.seeds.run_seed"

# View logs
render logs --service=backend-dev --tail=100

# Rollback deployment
render deploys rollback --service=backend-dev --deploy=<deploy-id>
```

### Troubleshooting

**Database connection failed**:
```bash
render services restart compliance-os-db-dev
```

**High error rate**:
```bash
render logs --service=backend-dev | grep ERROR
```

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2024 | Initial consolidated deployment guide |

---

**Note**: This document consolidates content from DEPLOYMENT_PLAN.md and DEPLOYMENT_STRATEGY.md. Originals archived in `docs/archive/`.
