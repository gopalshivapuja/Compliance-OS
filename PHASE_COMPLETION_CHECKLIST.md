# Phase Completion Checklist

**Version**: 1.0
**Last Updated**: December 2024

This document provides a comprehensive checklist for completing each development phase. Use this to ensure consistent quality and documentation across all phases.

---

## Quick Reference

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| 1 | Database Foundation | Models, migrations, seed data |
| 2 | Auth & RBAC | JWT, roles, entity access |
| 3 | CRUD Operations | All entity endpoints |
| 4 | Business Logic | Compliance engine, workflow engine |
| 5 | Background Jobs | Celery tasks, reminders |
| 6 | Frontend Auth | Login, layout, navigation |
| 7 | Frontend Dashboard | Executive, calendar, owner views |
| 8 | Frontend Compliance | Masters, instances CRUD |
| 9 | Frontend Workflow | Tasks, evidence management |
| 10 | Frontend Admin | User, tenant, entity management |
| 11 | Testing & Quality | Unit, integration, E2E tests |
| 12 | Deployment | Production deployment |

---

## Universal Checklist (Every Phase)

### Code Quality

- [ ] All code formatted with Black (backend)
- [ ] All code formatted with Prettier (frontend)
- [ ] No Flake8 errors (`flake8 app/`)
- [ ] No ESLint errors (`npm run lint`)
- [ ] MyPy type checking passes (`mypy app/`)
- [ ] No unused imports (F401 errors)
- [ ] No line length violations (E501 errors)
- [ ] All TODO/FIXME items addressed or documented for future phase

### Documentation

- [ ] CLAUDE.md updated with new patterns/conventions
- [ ] PROGRESS.md updated with phase completion
- [ ] CHANGELOG.md updated with version entry
- [ ] IMPLEMENTATION_PLAN.md phase marked complete
- [ ] Phase verification checklist completed (in IMPLEMENTATION_PLAN.md)
- [ ] New API endpoints documented in Swagger
- [ ] README updated if major features added

### Testing

- [ ] Unit tests written for new code
- [ ] Integration tests written for new endpoints
- [ ] All tests passing (`pytest -v`)
- [ ] Test coverage meets threshold (target: 80%)
- [ ] Manual testing completed for key flows
- [ ] Edge cases tested and documented

### Security & Compliance

- [ ] Audit logging on all new mutation endpoints
- [ ] Multi-tenant isolation verified (all queries filter by tenant_id)
- [ ] RBAC permissions verified on protected endpoints
- [ ] No secrets in code or logs
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention verified (parameterized queries)

### Repository Maintenance

- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] CI/CD pipeline green
- [ ] No merge conflicts
- [ ] Feature branch merged to main
- [ ] Git tag created for version (e.g., `v0.3.0`)
- [ ] Archive any obsolete documents to `docs/archive/`

---

## Phase-Specific Checklists

### Phase 4: Backend Business Logic

**Compliance Engine**:
- [ ] Instance generation for all frequency types (monthly, quarterly, annual)
- [ ] Due date calculation accurate for all rules
- [ ] RAG status calculation correct (Green/Amber/Red thresholds)
- [ ] Dependency chain resolution working

**Workflow Engine**:
- [ ] Task generation from master templates
- [ ] State transitions validated (Pending → In Progress → Complete/Reject)
- [ ] Escalation logic triggers at correct thresholds
- [ ] Parent/child task dependencies enforced

**Notifications**:
- [ ] Email templates created and tested
- [ ] In-app notifications created correctly
- [ ] Reminder timing verified (T-3, T-0, T+3)

### Phase 5: Backend Background Jobs

**Celery Configuration**:
- [ ] Worker starts without errors
- [ ] Beat scheduler running
- [ ] Redis connection stable
- [ ] Task results stored correctly

**Scheduled Tasks**:
- [ ] Daily instance generation runs at 2 AM IST
- [ ] Hourly RAG recalculation runs
- [ ] Reminder tasks trigger correctly
- [ ] Email queue processes within SLA

### Phase 6: Frontend Auth & Layout

**Authentication**:
- [ ] Login page renders correctly
- [ ] Form validation works
- [ ] JWT tokens stored securely
- [ ] Token refresh seamless
- [ ] Logout clears all data

**Layout**:
- [ ] Header displays correctly
- [ ] Sidebar navigation works
- [ ] Responsive on mobile/tablet/desktop
- [ ] Dark mode toggle (if implemented)

### Phase 7: Frontend Dashboard

**Executive View**:
- [ ] RAG status cards show correct counts
- [ ] Trend charts render with real data
- [ ] Category breakdown accurate

**Calendar View**:
- [ ] Month/week toggle works
- [ ] Instances display on correct dates
- [ ] Filters work correctly

**Owner View**:
- [ ] Shows only user's assigned items
- [ ] Task list displays correctly
- [ ] Quick actions work

### Phase 8: Frontend Compliance Management

**Compliance Masters**:
- [ ] List displays with pagination
- [ ] Create form validates all fields
- [ ] Edit form pre-populates correctly
- [ ] Delete confirms and soft-deletes
- [ ] Bulk import handles CSV/Excel

**Compliance Instances**:
- [ ] List with filters works
- [ ] Detail view shows all tabs
- [ ] Status updates correctly
- [ ] Audit log displays history

### Phase 9: Frontend Workflow & Evidence

**Workflow Tasks**:
- [ ] Task list displays correctly
- [ ] Assignment modal works
- [ ] Status transitions validated
- [ ] Sequence order enforced

**Evidence**:
- [ ] Upload accepts valid file types
- [ ] Size limits enforced
- [ ] Drag-drop works
- [ ] Preview works for images/PDFs
- [ ] Download generates signed URLs
- [ ] Approval/rejection works
- [ ] Versioning displays correctly

### Phase 10: Frontend Admin

**User Management**:
- [ ] Create user works
- [ ] Edit user works
- [ ] Deactivate prevents login
- [ ] Role assignment works

**Entity Management**:
- [ ] CRUD operations work
- [ ] Access control toggles work
- [ ] Changes take effect immediately

**Tenant Management** (System Admin only):
- [ ] Restricted to System Admin role
- [ ] Create/edit/deactivate works

### Phase 11: Testing & Quality

**Backend Tests**:
- [ ] Unit test coverage > 80%
- [ ] All API endpoints have integration tests
- [ ] Service layer tests cover edge cases

**Frontend Tests**:
- [ ] Component tests for key components
- [ ] Hook tests for custom hooks
- [ ] Store tests for Zustand stores

**E2E Tests**:
- [ ] Login flow tested
- [ ] Compliance instance creation tested
- [ ] Evidence upload/approval tested
- [ ] Critical user journeys covered

**Performance**:
- [ ] Load tests pass (100 concurrent users)
- [ ] Response times < 500ms for dashboard
- [ ] No memory leaks identified

### Phase 12: Deployment

**Infrastructure**:
- [ ] All services deployed (backend, frontend, workers)
- [ ] Database migrations applied
- [ ] Seed data loaded
- [ ] SSL certificates configured
- [ ] Health checks responding

**Monitoring**:
- [ ] Sentry configured for error tracking
- [ ] UptimeRobot monitors active
- [ ] Slack alerts configured

**Verification**:
- [ ] Smoke tests pass in production
- [ ] User acceptance testing completed
- [ ] Rollback procedure tested
- [ ] Backup/restore verified

---

## Next Phase Readiness Assessment

Before starting the next phase, verify:

- [ ] All current phase items complete (no blockers)
- [ ] Documentation is current
- [ ] Team has reviewed and approved (if applicable)
- [ ] Dependencies for next phase are available
- [ ] Environment is ready (services, credentials, etc.)

---

## Archival Procedure

When a phase is complete:

1. **Create checkpoint file** (optional):
   ```bash
   touch docs/archive/checkpoints/phaseN/PHASE_N_COMPLETE.md
   # Document key achievements, metrics, lessons learned
   ```

2. **Update archive README**:
   ```bash
   # Add phase entry to docs/archive/README.md
   ```

3. **Move obsolete docs**:
   ```bash
   mv PHASE_X_SPECIFIC.md docs/archive/phase_guides/
   ```

4. **Create git tag**:
   ```bash
   git tag -a v0.N.0 -m "Phase N complete: [summary]"
   git push origin v0.N.0
   ```

---

## Metrics to Track

| Metric | Phase 3 | Phase 4 | Phase 5 | ... |
|--------|---------|---------|---------|-----|
| Test Count | 238 | | | |
| Pass Rate | 83.5% | | | |
| Coverage | 74% | | | |
| Endpoints | 31 | | | |
| LOC | ~15,000 | | | |

---

## Common Issues & Solutions

### Pre-commit Hanging
- Cause: Prettier processing large markdown files
- Solution: Ensure all large docs are in `.prettierignore`

### Test Database Cleanup
```bash
psql -U gopal -c "DROP DATABASE compliance_os_test; CREATE DATABASE compliance_os_test;"
cd backend && alembic upgrade head
```

### Flake8 Unused Imports
```bash
# Find all unused imports
flake8 app/ | grep F401
# Fix in each file
```

### MyPy Errors
```bash
# Check specific file
mypy app/services/your_service.py --ignore-missing-imports
```

---

**Remember**: Quality over speed. A complete, well-tested phase is better than a rushed one with technical debt.
