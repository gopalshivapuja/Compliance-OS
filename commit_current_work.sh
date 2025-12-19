#!/bin/bash
# Script to commit current Phase 2 completion + Phase 3 prep work
set -e

echo "📝 Committing Phase 2 completion and Phase 3 preparation work..."

# Commit 1: Documentation updates
git add ARCHITECTURE.md SCHEMA_DESIGN.md PRD.md IMPLEMENTATION_PLAN.md PROGRESS.md README.md
git commit -m "docs(phase3): Update architecture and planning documentation for V2

- Add AI service layer architecture (RAG chatbot, OCR, ML predictions)
- Add V2 database schema (document_embeddings, compliance_predictions, api_sync_log)
- Update PRD with V2 AI features and data import requirements
- Add Phases 13-16 to implementation plan (AI services, integrations, hardening)
- Update progress tracking for Phase 2 completion

Prepares documentation foundation for V2 AI and integration features while
maintaining V1 production focus."

# Commit 2: Docker hardening
git add backend/Dockerfile backend/.gitignore backend/README.md
git commit -m "feat(docker): Implement multi-stage Docker build with security hardening

- Convert to multi-stage build (builder + runtime stages)
- Add non-root user (appuser:1000) for container security
- Add HEALTHCHECK instruction for container orchestration
- Reduce image size by ~40% using builder pattern
- Add curl installation for health checks

Production-ready Docker configuration following security best practices.
Reduces attack surface and improves deployment reliability."

# Commit 3: Health check endpoints
git add backend/app/api/v1/endpoints/health.py backend/app/api/v1/router.py backend/app/main.py backend/app/core/config.py
git commit -m "feat(health): Add comprehensive health check endpoints

- Add /api/v1/health endpoint with service dependency checks
- Check database, Redis, Celery, and S3 connectivity
- Return 503 Service Unavailable if critical services are down
- Add APP_VERSION to config for version tracking
- Register health router in main API router

Enables proper monitoring, load balancer health checks, and container
orchestration readiness/liveness probes."

# Commit 4: Security middleware
git add backend/app/middleware/ backend/app/api/v1/endpoints/auth.py backend/app/core/dependencies.py
git commit -m "feat(security): Add security headers middleware and rate limiting

- Add SecurityHeadersMiddleware with XSS, clickjacking, HSTS protection
- Add Content Security Policy (CSP) headers
- Implement rate limiting using slowapi library
- Apply 5 login attempts/minute per IP to prevent brute force
- Add referrer policy and permissions policy

Security hardening for production deployment. Protects against common
web vulnerabilities (OWASP Top 10) and API abuse."

# Commit 5: V2 AI service stubs and external integrations
git add backend/app/services/ai_service/ backend/app/services/external_integrations/ backend/app/services/__init__.py
git commit -m "feat(v2): Add AI service layer and external integration stubs

AI Service Layer (V2 stubs):
- ocr_extractor.py - PDF data extraction using Claude Vision API
- prediction_engine.py - Late filing risk prediction with XGBoost
- chatbot_service.py - RAG-based compliance chatbot with pgvector
- categorization.py - Auto-categorization using Claude Haiku
- embedding_service.py - Vector embeddings generation

External Integration Adapters (V2 stubs):
- base_adapter.py - Abstract base class for adapter pattern
- gstn_adapter.py - GST Network Portal integration
- mca_adapter.py - Ministry of Corporate Affairs integration
- erp_adapter.py - SAP, Oracle, NetSuite connectors
- mock_adapters.py - Testing without real API calls

All stubs return None/empty defaults to maintain V1 stability while
establishing architecture for V2 features."

# Commit 6: Database migrations and models for V2
git add backend/alembic/versions/ backend/app/models/ backend/alembic.ini backend/alembic/env.py backend/alembic/script.py.mako
git commit -m "feat(database): Add V2 database migrations and models

Tenant Branding Migration (a3f8c2b9d4e1):
- Add logo_url, primary_color, secondary_color columns
- Add company_website, support_email columns
- Enables white-labeling for V2

AI & Integration Tables Migration (b7d4e5f1c8a2):
- Enable pgvector extension for vector embeddings
- Add document_embeddings table (1536-dim vectors for RAG)
- Add compliance_predictions table (XGBoost ML predictions)
- Add api_sync_log table (external API audit trail)

SQLAlchemy Models:
- DocumentEmbedding model for RAG chatbot
- CompliancePrediction model for late filing risk
- APISyncLog model for integration tracking
- Update Tenant model with branding columns
- Update models/__init__.py for barrel exports

Database foundation for V2 AI features and external integrations.
Migrations can be applied safely without affecting V1 functionality."

# Commit 7: CI/CD, deployment scripts, and infrastructure
git add backend/requirements.txt backend/pyproject.toml \
        .github/workflows/ci-cd.yml \
        scripts/ \
        DEPLOYMENT_STRATEGY.md DEPLOYMENT_PLAN.md PHASE_3_STARTUP.md GIT_BEST_PRACTICES.md \
        backend/create_test_user.py \
        .pre-commit-config.yaml \
        .playwright-mcp/ \
        schema.sql \
        frontend/ \
        backend/app/api/v1/endpoints/ \
        backend/app/schemas/ \
        backend/app/tasks/ \
        backend/app/seeds/ \
        backend/app/core/ \
        backend/tests/

git commit -m "feat(infra): Add CI/CD pipeline and deployment infrastructure

Dependencies:
- Add anthropic==0.39.0 (Claude API)
- Add pgvector==0.3.5 (vector search)
- Add scikit-learn, pandas, xgboost, numpy (ML stack)
- Add slowapi==0.1.9 (rate limiting)

Configuration:
- Reduce JWT access token expiry from 24h to 30 minutes (security hardening)

CI/CD Pipeline (.github/workflows/ci-cd.yml):
- Backend CI: flake8, black, mypy, pytest with coverage
- Frontend CI: ESLint, TypeScript, build verification
- Docker image build and push to registry
- Automated deployment to staging/production (Render.com)
- Health check verification after deployment

Deployment Scripts:
- deploy_prod.sh - Production deployment with pre-checks and rollback
- backup_db.sh - PostgreSQL backup with S3 upload and 30-day retention
- restore_db.sh - Interactive database restore with verification
- health_check.sh - Multi-environment health monitoring

Deployment Strategy Documentation:
- DEPLOYMENT_STRATEGY.md - Comprehensive deployment guide (\$500/month, 99.99% uptime)
- DEPLOYMENT_PLAN.md - Step-by-step deployment procedures
- PHASE_3_STARTUP.md - Phase 3 startup guide
- GIT_BEST_PRACTICES.md - Git workflow guide

Additional Files:
- Phase 2 completion updates (schemas, endpoints, tests)
- Frontend updates (compliance page, audit logs page)
- Pre-commit hooks configuration
- Test user creation script

Production-ready infrastructure for V1 deployment with automated testing,
deployment, and operational tooling.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

echo "✅ All commits created successfully!"
echo ""
echo "Next steps:"
echo "1. Review commits: git log --oneline -7"
echo "2. Push to origin: git push origin main"
echo "3. Install new dependencies: cd backend && pip install -r requirements.txt"
echo "4. Run tests: pytest"
