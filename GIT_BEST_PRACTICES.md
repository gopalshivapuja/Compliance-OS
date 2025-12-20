# Git Best Practices for Compliance OS

**Version**: 1.1
**Last Updated**: December 2024

## Executive Summary

This guide provides a comprehensive Git workflow strategy for the Compliance OS project, covering atomic commits, feature branch workflow, and phase-based development patterns.

---

## Table of Contents

1. [Example: Handling Large Changes (Historical)](#part-1-example-handling-large-changes-historical)
2. [Git Workflow Best Practices](#part-2-git-workflow-best-practices-going-forward)
3. [Advanced Git Techniques](#part-3-advanced-git-techniques)
4. [Workflow for Specific Project Phases](#part-4-workflow-for-specific-project-phases)
5. [Git Best Practices Checklist](#part-5-git-best-practices-checklist)
6. [Compliance OS-Specific Git Practices](#part-6-compliance-os-specific-git-practices)
7. [Troubleshooting Common Git Issues](#part-7-troubleshooting-common-git-issues)
8. [Summary: Custom Git Workflow](#summary-your-custom-git-workflow)
9. [Quick Reference Commands](#appendix-quick-reference-commands)

---

## Part 1: Example: Handling Large Changes (Historical)

> **Note**: This section documents a real-world example from Phase 3 development (December 2024).
> Use it as a reference for breaking down large changesets into atomic commits.

### Current Status
- **Modified files**: 14 files (1,691 insertions, 147 deletions)
- **Untracked files**: 19 new files (migrations, services, scripts, workflows)
- **Scope**: Phase 3 deployment plan implementation + V2 foundation

### Recommended Commit Strategy: 7 Atomic Commits

Break down the changes into logical, atomic commits that can be understood and reverted independently:

#### Commit 1: Documentation Updates (Phase 3)
**Type**: `docs(phase3): Update architecture and planning documentation for V2`

**Files to commit**:
- `ARCHITECTURE.md` (+304 lines)
- `SCHEMA_DESIGN.md` (+159 lines)
- `PRD.md` (+281 lines)
- `IMPLEMENTATION_PLAN.md` (+772 lines)
- `PROGRESS.md` (updated)

**Commit message**:
```
docs(phase3): Update architecture and planning documentation for V2

- Add AI service layer architecture (RAG chatbot, OCR, ML predictions)
- Add V2 database schema (document_embeddings, compliance_predictions, api_sync_log)
- Update PRD with V2 AI features and data import requirements
- Add Phases 13-16 to implementation plan (AI services, integrations, hardening)
- Update progress tracking for Phase 3 completion

Prepares documentation foundation for V2 AI and integration features while
maintaining V1 production focus.
```

**Rationale**: Documentation changes are logically separate from code changes and should be committed first to provide context.

---

#### Commit 2: Production Docker Hardening
**Type**: `feat(docker): Implement multi-stage Docker build with security hardening`

**Files to commit**:
- `backend/Dockerfile` (+53 lines)

**Commit message**:
```
feat(docker): Implement multi-stage Docker build with security hardening

- Convert to multi-stage build (builder + runtime stages)
- Add non-root user (appuser:1000) for container security
- Add HEALTHCHECK instruction for container orchestration
- Reduce image size by ~40% using builder pattern
- Add curl installation for health checks

Production-ready Docker configuration following security best practices.
Reduces attack surface and improves deployment reliability.
```

**Rationale**: Docker changes are isolated and represent a complete, testable improvement.

---

#### Commit 3: Health Check and Monitoring Endpoints
**Type**: `feat(health): Add comprehensive health check endpoints`

**Files to commit**:
- `backend/app/api/v1/endpoints/health.py` (new file)
- `backend/app/api/v1/router.py` (+2 lines)
- `backend/app/main.py` (+4 lines via middleware)

**Commit message**:
```
feat(health): Add comprehensive health check endpoints

- Add /api/v1/health endpoint with service dependency checks
- Add /api/v1/health/live endpoint (liveness probe for K8s)
- Add /api/v1/health/ready endpoint (readiness probe for K8s)
- Check database, Redis, Celery, and S3 connectivity
- Return 503 Service Unavailable if critical services are down
- Add APP_VERSION to config for version tracking

Enables proper monitoring, load balancer health checks, and container
orchestration readiness/liveness probes.
```

**Rationale**: Health checks are a complete feature that can be tested independently.

---

#### Commit 4: Security Middleware (Headers and Rate Limiting)
**Type**: `feat(security): Add security headers middleware and rate limiting`

**Files to commit**:
- `backend/app/middleware/` (entire new directory)
  - `__init__.py`
  - `security_headers.py`
  - `rate_limiter.py`
- `backend/app/main.py` (middleware registration)
- `backend/app/api/v1/endpoints/auth.py` (+6 lines for rate limiting)

**Commit message**:
```
feat(security): Add security headers middleware and rate limiting

- Add SecurityHeadersMiddleware with XSS, clickjacking, HSTS protection
- Add Content Security Policy (CSP) headers
- Implement rate limiting using slowapi library
- Apply 5 login attempts/minute per IP to prevent brute force
- Add referrer policy and permissions policy

Security hardening for production deployment. Protects against common
web vulnerabilities (OWASP Top 10) and API abuse.
```

**Rationale**: Security changes are a cohesive unit focused on hardening the application.

---

#### Commit 5: V2 AI Service Stubs and External Integration Adapters
**Type**: `feat(v2): Add AI service layer and external integration stubs`

**Files to commit**:
- `backend/app/services/ai_service/` (entire directory, 6 files)
- `backend/app/services/external_integrations/` (entire directory, 6 files)

**Commit message**:
```
feat(v2): Add AI service layer and external integration stubs

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
establishing architecture for V2 features.
```

**Rationale**: V2 stubs are forward-looking additions that don't affect V1 functionality.

---

#### Commit 6: Database Migrations and Models for V2 Features
**Type**: `feat(database): Add V2 database migrations and models`

**Files to commit**:
- `backend/alembic/versions/a3f8c2b9d4e1_add_tenant_branding_columns.py`
- `backend/alembic/versions/b7d4e5f1c8a2_add_ai_and_integration_tables.py`
- `backend/app/models/tenant.py` (+7 lines - branding columns)
- `backend/app/models/document_embedding.py` (new)
- `backend/app/models/compliance_prediction.py` (new)
- `backend/app/models/api_sync_log.py` (new)
- `backend/app/models/__init__.py` (+9 lines)

**Commit message**:
```
feat(database): Add V2 database migrations and models

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
Migrations can be applied safely without affecting V1 functionality.
```

**Rationale**: Database changes are infrastructure and should be grouped together.

---

#### Commit 7: Dependencies, Configuration, CI/CD, and Deployment Scripts
**Type**: `feat(infra): Add CI/CD pipeline and deployment infrastructure`

**Files to commit**:
- `backend/requirements.txt` (+10 lines)
- `backend/app/core/config.py` (JWT expiry change)
- `.github/workflows/ci-cd.yml` (new)
- `scripts/deploy_prod.sh` (new)
- `scripts/backup_db.sh` (new)
- `scripts/restore_db.sh` (new)
- `scripts/health_check.sh` (new)
- `scripts/README.md` (+108 lines)
- `DEPLOYMENT_STRATEGY.md` (new)
- `DEPLOYMENT_PLAN.md` (new)
- `PHASE_3_STARTUP.md` (new)
- `backend/create_test_user.py` (new)

**Commit message**:
```
feat(infra): Add CI/CD pipeline and deployment infrastructure

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
- DEPLOYMENT_STRATEGY.md - Comprehensive deployment guide ($500/month, 99.99% uptime)
- DEPLOYMENT_PLAN.md - Step-by-step deployment procedures
- PHASE_3_STARTUP.md - Phase 3 startup guide

Production-ready infrastructure for V1 deployment with automated testing,
deployment, and operational tooling.
```

**Rationale**: Infrastructure and deployment tooling are a cohesive unit that enables production deployment.

---

### Command Sequence for Committing Current Changes

```bash
# 1. Documentation updates
git add ARCHITECTURE.md SCHEMA_DESIGN.md PRD.md IMPLEMENTATION_PLAN.md PROGRESS.md
git commit -m "docs(phase3): Update architecture and planning documentation for V2

- Add AI service layer architecture (RAG chatbot, OCR, ML predictions)
- Add V2 database schema (document_embeddings, compliance_predictions, api_sync_log)
- Update PRD with V2 AI features and data import requirements
- Add Phases 13-16 to implementation plan (AI services, integrations, hardening)
- Update progress tracking for Phase 3 completion

Prepares documentation foundation for V2 AI and integration features while
maintaining V1 production focus."

# 2. Docker hardening
git add backend/Dockerfile
git commit -m "feat(docker): Implement multi-stage Docker build with security hardening

- Convert to multi-stage build (builder + runtime stages)
- Add non-root user (appuser:1000) for container security
- Add HEALTHCHECK instruction for container orchestration
- Reduce image size by ~40% using builder pattern
- Add curl installation for health checks

Production-ready Docker configuration following security best practices.
Reduces attack surface and improves deployment reliability."

# 3. Health check endpoints
git add backend/app/api/v1/endpoints/health.py backend/app/api/v1/router.py backend/app/main.py
git commit -m "feat(health): Add comprehensive health check endpoints

- Add /api/v1/health endpoint with service dependency checks
- Add /api/v1/health/live endpoint (liveness probe for K8s)
- Add /api/v1/health/ready endpoint (readiness probe for K8s)
- Check database, Redis, Celery, and S3 connectivity
- Return 503 Service Unavailable if critical services are down
- Add APP_VERSION to config for version tracking

Enables proper monitoring, load balancer health checks, and container
orchestration readiness/liveness probes."

# 4. Security middleware
git add backend/app/middleware/ backend/app/api/v1/endpoints/auth.py
git commit -m "feat(security): Add security headers middleware and rate limiting

- Add SecurityHeadersMiddleware with XSS, clickjacking, HSTS protection
- Add Content Security Policy (CSP) headers
- Implement rate limiting using slowapi library
- Apply 5 login attempts/minute per IP to prevent brute force
- Add referrer policy and permissions policy

Security hardening for production deployment. Protects against common
web vulnerabilities (OWASP Top 10) and API abuse."

# 5. V2 AI service stubs
git add backend/app/services/ai_service/ backend/app/services/external_integrations/
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

# 6. Database migrations and models
git add backend/alembic/versions/ backend/app/models/
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

# 7. CI/CD, deployment scripts, and infrastructure
git add backend/requirements.txt backend/app/core/config.py .github/workflows/ scripts/ DEPLOYMENT_STRATEGY.md DEPLOYMENT_PLAN.MD PHASE_3_STARTUP.md backend/create_test_user.py .playwright-mcp/
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

Production-ready infrastructure for V1 deployment with automated testing,
deployment, and operational tooling."

# 8. Push all commits
git push origin main
```

---

## Part 2: Git Workflow Best Practices Going Forward

### 1. Feature Branch Workflow (Recommended for Solo Developer)

#### Branch Naming Convention
Use descriptive, kebab-case branch names with type prefix:

- `feature/<short-description>` - New features
- `fix/<issue-description>` - Bug fixes
- `refactor/<component-name>` - Code refactoring
- `docs/<topic>` - Documentation updates
- `test/<feature-name>` - Test additions
- `chore/<task>` - Maintenance tasks

**Examples**:
```bash
feature/evidence-approval-workflow
feature/gst-filing-automation
fix/rag-status-calculation-edge-case
refactor/compliance-engine-performance
docs/api-endpoint-documentation
test/workflow-task-completion
chore/upgrade-fastapi-0.105
```

#### Typical Workflow

```bash
# 1. Start new feature
git checkout main
git pull origin main
git checkout -b feature/gst-filing-automation

# 2. Make changes and commit atomically
# (See "Atomic Commit Guidelines" below)

# 3. Push feature branch
git push -u origin feature/gst-filing-automation

# 4. Create Pull Request (even for solo work - good practice)
gh pr create --title "feat(gst): Add automated GST filing status sync" \
  --body "Implements GSTN API integration for automatic filing status updates."

# 5. Review and merge (can merge locally for solo work)
git checkout main
git merge --no-ff feature/gst-filing-automation
git push origin main

# 6. Delete feature branch
git branch -d feature/gst-filing-automation
git push origin --delete feature/gst-filing-automation
```

**Why this works for solo development**:
- Isolates work-in-progress from stable main
- Easy to switch context between features
- Clear history of what was worked on when
- Can abandon branches without polluting main
- Practice same workflow you'd use in team settings

---

### 2. Atomic Commit Guidelines

#### What Makes a Good Atomic Commit?

1. **Single Logical Change**: Each commit addresses one thing (one bug fix, one feature, one refactor)
2. **Complete**: The commit includes all necessary changes (code + tests + docs)
3. **Buildable**: The codebase builds and runs after the commit
4. **Testable**: Tests pass after the commit
5. **Reversible**: The commit can be reverted without breaking other functionality

#### Atomic Commit Examples

**❌ BAD - Too Large (Multiple Concerns)**
```bash
git commit -m "Add user authentication and fix dashboard bug and update docs"
# Problem: 3 unrelated changes in one commit
```

**✅ GOOD - Atomic Commits**
```bash
git commit -m "feat(auth): Add JWT token authentication"
git commit -m "fix(dashboard): Correct RAG status calculation for blocking instances"
git commit -m "docs(api): Update authentication endpoint documentation"
```

**❌ BAD - Too Small (Incomplete)**
```bash
git commit -m "Add User model"
git commit -m "Add user migration"
git commit -m "Add user tests"
# Problem: Incomplete - model without migration/tests doesn't work
```

**✅ GOOD - Complete Feature**
```bash
git commit -m "feat(user): Add User model with authentication fields

- Add User SQLAlchemy model with password_hash, email, status
- Add Alembic migration for users table
- Add unit tests for User model validation
- Update models/__init__.py for barrel export"
```

#### When to Split Commits

Split when changes address different concerns:

```bash
# Scenario: Adding evidence approval + fixing a bug

# Commit 1: New feature
git add backend/app/api/v1/endpoints/evidence.py backend/tests/test_evidence.py
git commit -m "feat(evidence): Add approval workflow endpoint"

# Commit 2: Bug fix (separate concern)
git add backend/app/services/rag_calculator.py backend/tests/test_rag.py
git commit -m "fix(rag): Correct status calculation when dependency is blocking"
```

#### When to Group Commits

Group when changes are tightly coupled:

```bash
# Scenario: Refactoring compliance engine (model + service + tests all need updating)

git add backend/app/models/compliance_instance.py \
        backend/app/services/compliance_engine.py \
        backend/tests/test_compliance_engine.py

git commit -m "refactor(compliance): Extract instance generation logic to service layer

- Move instance generation from model to ComplianceEngine service
- Update ComplianceInstance model to use service
- Update tests to reflect new architecture
- Improves testability and separation of concerns"
```

---

### 3. Commit Message Template

Use this template for all commits (already in your CONTRIBUTING.md):

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Formatting, no code change
- `refactor` - Code change that neither fixes bug nor adds feature
- `perf` - Performance improvement
- `test` - Adding/updating tests
- `chore` - Build, dependencies, tooling

#### Scope
Component/module affected (examples from your codebase):
- `auth` - Authentication
- `compliance` - Compliance management
- `workflow` - Workflow engine
- `evidence` - Evidence vault
- `api` - API endpoints
- `database` - Database/migrations
- `docker` - Docker configuration
- `ci` - CI/CD pipeline
- `security` - Security features

#### Subject
- Imperative mood ("Add feature" not "Added feature")
- No period at end
- Max 50 characters
- Capitalize first letter

#### Body (Optional but Recommended)
- Wrap at 72 characters
- Explain WHAT and WHY, not HOW
- Use bullet points for multiple changes
- Reference related issues/tickets

#### Footer (Optional)
- Breaking changes: `BREAKING CHANGE: <description>`
- Issue references: `Closes #123`, `Fixes #456`, `Relates to #789`

#### Real Examples from Your Project

**Simple feature**:
```
feat(health): Add liveness probe endpoint

Add /api/v1/health/live endpoint for Kubernetes liveness checks.
Returns 200 OK if the application process is running.

Enables container orchestration platforms to detect and restart
unhealthy containers automatically.
```

**Complex feature with multiple changes**:
```
feat(ai): Implement RAG-based compliance chatbot

- Add ChatbotService with query embedding generation
- Implement vector similarity search using pgvector
- Add context retrieval from document_embeddings table
- Integrate Claude 3.5 Haiku for answer generation
- Add chatbot endpoint at /api/v1/ai/chat
- Add unit tests for embedding search and response generation
- Update API documentation

Enables users to ask natural language questions about compliance
requirements and get context-aware answers from their document library.

Closes #42
```

**Bug fix**:
```
fix(rag): Correct status calculation when dependency is blocking

When a compliance instance is blocked by a dependency, RAG status was
incorrectly showing Green instead of Amber. Fixed calculation logic to
check blocking_compliance_instance_id before evaluating due date.

Added test case for blocking dependency scenario.

Fixes #156
```

**Refactoring**:
```
refactor(compliance): Extract instance generation to service layer

- Move generate_instances logic from ComplianceMaster model to ComplianceEngine
- Add generate_instances_for_period method to service
- Update scheduled task to use service instead of model method
- Update tests to mock service instead of model

Improves separation of concerns and testability. No functional changes.
```

**Documentation**:
```
docs(deployment): Add production deployment guide

- Add DEPLOYMENT_STRATEGY.md with platform selection rationale
- Document cost breakdown ($500/month for dev + prod)
- Add step-by-step deployment procedures
- Document rollback procedures and disaster recovery
- Add monitoring and alerting setup guide
```

---

### 4. When to Commit?

#### Commit Frequency Guidelines

**✅ Commit when**:
- You complete a logical unit of work (one feature, one fix, one refactor)
- All tests pass for your changes
- Code is formatted and linted
- You're about to switch tasks/context
- You're done for the day (commit work-in-progress on feature branch)

**❌ Don't commit when**:
- Code doesn't compile/run
- Tests are failing (unless explicitly testing in WIP branch)
- You're in the middle of a change (halfway through renaming, etc.)
- You haven't tested your changes locally

#### Work-in-Progress Commits (Feature Branches Only)

It's OK to commit WIP on feature branches:

```bash
# On feature branch
git commit -m "wip: Partial implementation of evidence approval logic"

# Later, squash before merging to main
git checkout main
git merge --squash feature/evidence-approval
git commit -m "feat(evidence): Add approval workflow endpoint"
```

---

### 5. Git Workflow for Different Task Sizes

#### Small Task (< 1 hour, < 50 lines)
**Example**: Fix a typo, update a config value, add a validation

```bash
# Work directly on feature branch, single commit
git checkout -b fix/validation-error-message
# Make changes
git add backend/app/schemas/compliance.py
git commit -m "fix(validation): Improve error message for invalid due_date format"
git checkout main
git merge fix/validation-error-message
git push
```

#### Medium Task (1-4 hours, 50-300 lines)
**Example**: Add a new API endpoint with tests

```bash
git checkout -b feature/evidence-download-endpoint

# Commit 1: Add endpoint logic
git add backend/app/api/v1/endpoints/evidence.py
git commit -m "feat(evidence): Add download endpoint with S3 signed URLs"

# Commit 2: Add tests
git add backend/tests/test_evidence_api.py
git commit -m "test(evidence): Add tests for download endpoint"

# Commit 3: Update docs
git add docs/api/evidence.md
git commit -m "docs(api): Document evidence download endpoint"

git checkout main
git merge --no-ff feature/evidence-download-endpoint
git push
```

#### Large Task (> 4 hours, > 300 lines, multiple files)
**Example**: Implement workflow task approval system

```bash
git checkout -b feature/workflow-task-approval

# Commit 1: Database changes
git add backend/alembic/versions/xxx_add_approval_fields.py \
        backend/app/models/workflow_task.py
git commit -m "feat(workflow): Add approval fields to workflow_task model"

# Commit 2: Service layer
git add backend/app/services/workflow_engine.py
git commit -m "feat(workflow): Implement task approval logic in workflow engine"

# Commit 3: API endpoint
git add backend/app/api/v1/endpoints/workflow_tasks.py
git commit -m "feat(workflow): Add approve/reject endpoints for workflow tasks"

# Commit 4: Tests
git add backend/tests/test_workflow_approval.py
git commit -m "test(workflow): Add comprehensive tests for approval workflow"

# Commit 5: Documentation
git add docs/workflows/approval-process.md
git commit -m "docs(workflow): Document task approval process"

git checkout main
git merge --no-ff feature/workflow-task-approval
git push
```

---

### 6. Handling Mistakes and Corrections

#### Uncommitted Changes - Made a Mistake

```bash
# Undo all uncommitted changes
git restore .

# Undo changes to specific file
git restore backend/app/main.py

# Unstage file but keep changes
git restore --staged backend/app/main.py
```

#### Last Commit - Made a Mistake (Not Pushed)

```bash
# Amend last commit (add forgotten file)
git add backend/tests/test_new_feature.py
git commit --amend --no-edit

# Amend last commit (fix message)
git commit --amend -m "feat(auth): Add JWT refresh endpoint (fixed typo)"

# Undo last commit but keep changes
git reset --soft HEAD~1

# Undo last commit and discard changes
git reset --hard HEAD~1
```

#### Already Pushed - Need to Revert

```bash
# NEVER force push on main branch (solo or team)
# Instead, create a revert commit

# Revert last commit
git revert HEAD

# Revert specific commit
git revert abc1234

# Revert multiple commits
git revert abc1234..def5678
```

---

### 7. Branch Management Best Practices

#### Keep Main Branch Clean

**Rules**:
1. Main should always be deployable
2. All tests must pass on main
3. No WIP commits on main
4. Use `--no-ff` for feature merges to preserve history

```bash
# Good - preserves feature branch history
git merge --no-ff feature/new-endpoint

# Avoid on main - loses context
git merge --squash feature/new-endpoint  # OK for very messy feature branches
```

#### Branch Cleanup

```bash
# List merged branches
git branch --merged

# Delete local merged branches
git branch -d feature/old-feature

# Delete remote branch
git push origin --delete feature/old-feature

# Prune remote-tracking branches
git fetch --prune
```

#### Long-Running Feature Branches

If a feature takes > 1 week, regularly sync with main:

```bash
# On feature branch
git checkout feature/long-running-feature

# Rebase on main to stay up-to-date
git fetch origin
git rebase origin/main

# Or merge main into feature (creates merge commit)
git merge origin/main

# Push (force push if you rebased)
git push --force-with-lease
```

---

### 8. Special Scenarios

#### Scenario: Emergency Hotfix

```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-security-patch

# Make minimal fix
git add backend/app/core/security.py
git commit -m "fix(security): Patch SQL injection vulnerability in search endpoint

Sanitize user input in compliance search query to prevent SQL injection.
All search parameters now use parameterized queries.

SECURITY: CVE-2024-XXXXX
Severity: High"

# Merge immediately
git checkout main
git merge --no-ff hotfix/critical-security-patch
git push origin main

# Deploy immediately
./scripts/deploy_prod.sh

# Delete hotfix branch
git branch -d hotfix/critical-security-patch
```

#### Scenario: Experimental Work (Might Discard)

```bash
# Create experiment branch
git checkout -b experiment/alternative-rag-algorithm

# Commit as you go (WIP commits OK)
git commit -m "wip: Try cosine similarity for RAG matching"
git commit -m "wip: Add benchmarking tests"

# Decision: Keep it
git checkout main
git merge --squash experiment/alternative-rag-algorithm
git commit -m "perf(rag): Implement cosine similarity for improved matching accuracy"

# Decision: Discard it
git checkout main
git branch -D experiment/alternative-rag-algorithm  # Force delete unmerged
```

#### Scenario: Dependency Updates

```bash
# Create update branch
git checkout -b chore/upgrade-dependencies

# Update dependencies
pip-compile --upgrade backend/requirements.in

# Test thoroughly
pytest

# Commit with changelog
git add backend/requirements.txt
git commit -m "chore(deps): Upgrade backend dependencies

- Upgrade FastAPI 0.104.1 -> 0.109.0 (security patches)
- Upgrade SQLAlchemy 2.0.23 -> 2.0.25 (performance improvements)
- Upgrade pydantic 2.5.0 -> 2.6.1 (bug fixes)

All tests passing. No breaking changes detected.
Addresses 3 dependabot security alerts."

git checkout main
git merge --no-ff chore/upgrade-dependencies
git push
```

---

## Part 3: Advanced Git Techniques

### Interactive Staging

Stage parts of a file selectively:

```bash
# Stage file interactively (choose hunks)
git add -p backend/app/main.py

# Commands in interactive mode:
# y - stage this hunk
# n - don't stage this hunk
# s - split hunk into smaller hunks
# e - manually edit hunk
# q - quit
```

Use case: You made two unrelated changes in one file and want to commit them separately.

---

### Stashing Work

Save uncommitted changes temporarily:

```bash
# Save current work
git stash

# Save with message
git stash save "WIP: Evidence approval halfway done"

# List stashes
git stash list

# Apply most recent stash (keep in stash list)
git stash apply

# Apply and remove from stash list
git stash pop

# Apply specific stash
git stash apply stash@{1}

# Delete stash
git stash drop stash@{0}
```

Use case: Need to switch branches but have uncommitted work.

---

### Cherry-Picking Commits

Apply a commit from one branch to another:

```bash
# On feature-branch-A, you made a useful utility function
# Want to use it in feature-branch-B

git checkout feature-branch-B
git cherry-pick abc1234  # Commit hash from feature-branch-A
```

Use case: Made a commit in wrong branch, or need a fix from another branch.

---

### Viewing History

```bash
# Graphical history
git log --oneline --graph --all --decorate

# Search commits by message
git log --grep="authentication"

# Show commits affecting a file
git log --follow backend/app/main.py

# Show changes in last 3 commits
git log -p -3

# Show commits by author
git log --author="Gopal"

# Show commits in date range
git log --since="2024-12-01" --until="2024-12-19"
```

---

### Git Aliases (Productivity Boost)

Add to `~/.gitconfig`:

```ini
[alias]
    st = status -s
    co = checkout
    br = branch
    ci = commit
    unstage = restore --staged
    last = log -1 HEAD
    visual = log --oneline --graph --all --decorate
    amend = commit --amend --no-edit
    undo = reset --soft HEAD~1

    # Show files changed in last commit
    changed = show --name-only

    # Interactive add
    add-i = add -p

    # Show commits not pushed
    unpushed = log @{u}..

    # Show branches sorted by last commit
    branches = branch --sort=-committerdate
```

Usage:
```bash
git st          # Instead of git status -s
git visual      # Instead of git log --oneline --graph...
git amend       # Instead of git commit --amend --no-edit
```

---

## Part 4: Workflow for Specific Project Phases

### Phase Implementation Workflow

For Compliance OS, each phase has multiple tasks. Here's the recommended workflow:

#### Example: Phase 4 - Authentication & RBAC

**Phase 4 Tasks**:
1. Implement login endpoint
2. Implement token refresh endpoint
3. Implement RBAC middleware
4. Add permission checks to endpoints
5. Add authentication tests

**Workflow**:

```bash
# Create phase branch
git checkout -b feature/phase-4-authentication

# Task 1: Login endpoint (atomic)
git add backend/app/api/v1/endpoints/auth.py \
        backend/app/schemas/auth.py
git commit -m "feat(auth): Implement login endpoint with JWT token generation

- Add POST /api/v1/auth/login endpoint
- Accept email and password in request body
- Validate credentials against database
- Generate access token (30 min expiry) and refresh token (7 days)
- Return tokens in response
- Add LoginRequest and TokenResponse schemas"

# Task 2: Token refresh (atomic)
git add backend/app/api/v1/endpoints/auth.py \
        backend/app/core/security.py
git commit -m "feat(auth): Implement token refresh endpoint

- Add POST /api/v1/auth/refresh endpoint
- Accept refresh token in request body
- Validate refresh token signature and expiry
- Generate new access token
- Add refresh token to Redis with 7-day expiry
- Add token blacklisting on logout"

# Task 3: RBAC middleware (atomic)
git add backend/app/middleware/rbac.py \
        backend/app/core/permissions.py
git commit -m "feat(rbac): Add role-based access control middleware

- Add RBACMiddleware to check user permissions
- Define permission decorators (@require_role, @require_permission)
- Load user roles from database on authentication
- Add permission definitions in permissions.py
- Cache user permissions in Redis for performance"

# Task 4: Apply RBAC to endpoints (atomic)
git add backend/app/api/v1/endpoints/compliance_instances.py \
        backend/app/api/v1/endpoints/evidence.py \
        backend/app/api/v1/endpoints/workflow_tasks.py
git commit -m "feat(rbac): Apply permission checks to compliance and evidence endpoints

- Add @require_permission decorators to all endpoints
- ComplianceInstance: create=ComplianceManager, update=Owner or ComplianceManager
- Evidence: upload=Owner, approve=Approver, delete=Owner (only if not immutable)
- WorkflowTask: update=AssignedUser, complete=AssignedUser
- Return 403 Forbidden if user lacks permission"

# Task 5: Tests (atomic)
git add backend/tests/test_auth.py \
        backend/tests/test_rbac.py
git commit -m "test(auth): Add comprehensive authentication and RBAC tests

- Add login endpoint tests (valid/invalid credentials, token format)
- Add token refresh tests (valid/expired/invalid tokens)
- Add RBAC middleware tests (permission checks, role validation)
- Add endpoint permission tests (403 for unauthorized, 200 for authorized)
- Achieve >90% code coverage for auth module"

# Merge phase to main
git checkout main
git merge --no-ff feature/phase-4-authentication
git tag v1.0.0-phase4  # Optional: Tag phase completion
git push origin main --tags
```

**Result**: Clean, atomic commits that can be reviewed independently, but grouped under phase branch for context.

---

### Documentation Update Workflow

```bash
# Create docs branch
git checkout -b docs/phase-4-authentication

# Update API documentation
git add docs/api/authentication.md
git commit -m "docs(api): Document authentication endpoints

- Document POST /api/v1/auth/login
- Document POST /api/v1/auth/refresh
- Document POST /api/v1/auth/logout
- Add request/response examples with curl
- Document error codes (401, 403, 422)"

# Update architecture docs
git add ARCHITECTURE.md
git commit -m "docs(arch): Update architecture with authentication flow

- Add authentication sequence diagram
- Document JWT token flow (access + refresh)
- Document RBAC permission checking flow
- Add Redis caching strategy for permissions"

# Update README
git add README.md
git commit -m "docs(readme): Update authentication setup instructions

- Add JWT_SECRET_KEY to environment variables
- Document token expiry configuration
- Add authentication testing instructions"

git checkout main
git merge docs/phase-4-authentication
git push
```

---

## Part 5: Git Best Practices Checklist

### Before Every Commit

- [ ] Run code formatter (`black`, `prettier`)
- [ ] Run linter (`flake8`, `eslint`)
- [ ] Run type checker (`mypy`, `tsc`)
- [ ] Run tests (`pytest`, `npm test`)
- [ ] Review changes (`git diff`)
- [ ] Write descriptive commit message
- [ ] Commit only related changes (atomic)

### Before Every Push

- [ ] All commits are properly formatted and tested
- [ ] No sensitive data in commits (`.env`, secrets, API keys)
- [ ] Commit messages follow conventional commits format
- [ ] Feature branch is up-to-date with main (if applicable)
- [ ] No merge conflicts

### Before Every Merge to Main

- [ ] All tests pass on feature branch
- [ ] Code is reviewed (self-review for solo, PR review for team)
- [ ] Documentation is updated
- [ ] CHANGELOG is updated (if applicable)
- [ ] No breaking changes (or properly documented with BREAKING CHANGE footer)

### Periodically

- [ ] Clean up merged branches (`git branch -d`)
- [ ] Prune remote branches (`git fetch --prune`)
- [ ] Review `.gitignore` for new patterns
- [ ] Update dependencies and commit separately
- [ ] Tag releases (`git tag -a v1.0.0 -m "Release v1.0.0"`)

---

## Part 6: Compliance OS-Specific Git Practices

### Phase-Based Tagging

After completing each phase, create an annotated tag:

```bash
# After Phase 1 (Foundation)
git tag -a v1.0.0-phase1 -m "Phase 1 Complete: Foundation
- Database schema and migrations
- SQLAlchemy models
- Basic API structure
- Authentication utilities"

# After Phase 2 (Frontend)
git tag -a v1.0.0-phase2 -m "Phase 2 Complete: Frontend & Auth
- Login page and dashboard
- JWT authentication flow
- Frontend API client
- Basic RBAC implementation"

# After Phase 3 (Deployment)
git tag -a v1.0.0-phase3 -m "Phase 3 Complete: Production Hardening
- Docker multi-stage build
- CI/CD pipeline
- Deployment scripts
- V2 feature stubs"

# Push tags
git push origin --tags
```

### Audit-Ready Commit History

Since Compliance OS is audit-focused, maintain high-quality commit history:

1. **Never force-push to main** (destroys audit trail)
2. **Use signed commits for security changes**:
   ```bash
   git commit -S -m "fix(security): Patch authentication bypass vulnerability"
   ```
3. **Reference issues in commit footers**:
   ```
   feat(audit): Add audit log retention policy

   Closes #123
   Security requirement: SOC2-AU-003
   ```
4. **Document breaking changes clearly**:
   ```
   feat(api): Change evidence upload response format

   BREAKING CHANGE: Evidence upload endpoint now returns evidence_id
   instead of file_path in response. Update frontend to use new format.

   Migration guide in docs/migrations/v1-to-v2.md
   ```

### Multi-Tenant Considerations

When making changes that affect multi-tenancy, use specific commit message patterns:

```bash
# Security change affecting tenant isolation
git commit -m "fix(security): Enforce tenant_id filtering in compliance instances query

Prevent cross-tenant data leakage by adding tenant_id check to all
compliance instance queries. Addresses security audit finding SA-2024-003.

Security impact: High
Affected endpoints: GET /api/v1/compliance-instances/*"

# Performance change with tenant implications
git commit -m "perf(database): Add composite index for tenant_id + status queries

Add index on (tenant_id, status, due_date) to compliance_instances table.
Improves dashboard query performance by 85% for tenants with 10k+ instances.

Migration: Auto-applied via Alembic
Downtime: None (index built concurrently)"
```

---

## Part 7: Troubleshooting Common Git Issues

### Issue: Accidentally Committed Secrets

```bash
# 1. Remove from last commit (not pushed)
git reset --soft HEAD~1
# Remove secrets from files
git add .
git commit

# 2. Already pushed (nuclear option)
# Contact security team first!
# Rotate all exposed credentials
# Then use BFG Repo-Cleaner or git-filter-repo
# (Complex - prefer prevention with .gitignore and pre-commit hooks)
```

**Prevention**: Use pre-commit hooks to scan for secrets:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
EOF

# Install hooks
pre-commit install
```

### Issue: Merge Conflicts

```bash
# 1. Abort merge and start over
git merge --abort

# 2. Or resolve conflicts manually
# Edit conflicted files (look for <<<<<<< markers)
git add <resolved-files>
git commit

# 3. Use merge tool
git mergetool
```

### Issue: Wrong Branch

```bash
# Made commits on main instead of feature branch
# Create branch at current position
git branch feature/accidental-work

# Reset main to previous position
git reset --hard origin/main

# Switch to new branch (commits are preserved)
git checkout feature/accidental-work
```

### Issue: Lost Commits

```bash
# Use reflog to find lost commits
git reflog

# Recover lost commit
git checkout abc1234  # Commit hash from reflog
git checkout -b recovery/lost-commits
```

---

## Summary: Your Custom Git Workflow

Based on your preferences (solo developer, atomic commits, feature branches), here's your streamlined workflow:

### Daily Workflow

```bash
# Morning: Start new feature
git checkout main
git pull
git checkout -b feature/new-task

# Throughout day: Atomic commits
# (make changes, test, commit)
git add specific-files
git commit -m "feat(scope): Description"

# End of day: Push feature branch
git push -u origin feature/new-task

# When feature complete: Merge to main
git checkout main
git merge --no-ff feature/new-task
git push
git branch -d feature/new-task
```

### Phase Completion Workflow

```bash
# After completing all phase tasks
git tag -a v1.0.0-phase<N> -m "Phase <N> Complete: <Title>"
git push origin --tags

# Update PROGRESS.md
git add PROGRESS.md
git commit -m "docs(progress): Mark Phase <N> as complete"
git push
```

### Emergency Hotfix Workflow

```bash
git checkout main
git pull
git checkout -b hotfix/urgent-fix
# Fix, test, commit
git checkout main
git merge --no-ff hotfix/urgent-fix
git push
./scripts/deploy_prod.sh
```

---

## Appendix: Quick Reference Commands

```bash
# Most common commands you'll use:

# Start feature
git checkout -b feature/name

# Atomic commit
git add specific-files
git commit -m "type(scope): description"

# Check status
git status -s

# See uncommitted changes
git diff

# See last commit
git log -1 --stat

# Merge to main
git checkout main
git merge --no-ff feature/name
git push

# Tag release
git tag -a v1.0.0 -m "Release v1.0.0"
git push --tags

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Amend last commit
git commit --amend --no-edit

# Stash changes temporarily
git stash
git stash pop

# Clean up branches
git branch --merged | grep -v main | xargs git branch -d
git fetch --prune
```

---

## Recommended Next Steps

1. **Commit current Phase 3 changes** using the 7 atomic commits outlined in Part 1
2. **Set up Git aliases** from Part 3 for productivity
3. **Install pre-commit hooks** to prevent secrets and enforce linting
4. **Create Phase 4 feature branch** for next phase of work
5. **Practice atomic commits** on Phase 4 tasks
6. **Review commit history** monthly to ensure quality

---

This guide provides a comprehensive Git workflow tailored to your solo development style with atomic commits and feature branches. The key is consistency - following this workflow will make your Git history clean, professional, and audit-ready.
