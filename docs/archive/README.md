# Documentation Archive

This directory contains archived documentation from completed phases of the Compliance OS V1 project.

## Structure

```
docs/archive/
├── checkpoints/          # Milestone checkpoint files
│   ├── phase1/          # Phase 1 milestone checkpoints (if any)
│   └── phase2/          # Phase 2 milestone checkpoints (M1-M5)
├── phase_guides/        # Phase-specific setup and execution guides
└── README.md            # This file
```

## Archive Policy

### When to Archive

Files are archived when:
1. A phase is completed and marked as ✅ COMPLETE in IMPLEMENTATION_PLAN.md
2. The phase completion has been documented in PROGRESS.md and CHANGELOG.md
3. All deliverables have been verified and tested

### What Gets Archived

**Checkpoint Files** (`checkpoints/phase{N}/`):
- `CHECKPOINT_M{X}_COMPLETE.md` - Milestone completion summaries
- Phase-specific test documentation (e.g., AUDIT_LOG_API_TEST.md)
- Milestone-specific technical notes

**Phase Guides** (`phase_guides/`):
- `PHASE{N}_SETUP_GUIDE.md` - Phase setup and execution guides
- Phase-specific runbooks
- Environment setup documentation (if phase-specific)

### What Stays in Root

The following files always remain in the project root:
- `README.md` - Project overview and quick start
- `IMPLEMENTATION_PLAN.md` - Overall project roadmap
- `PROGRESS.md` - Development progress tracking
- `CHANGELOG.md` - Version history
- `ARCHITECTURE.md` - System architecture
- `SCHEMA_DESIGN.md` - Database design
- `CONTRIBUTING.md` - Contribution guidelines
- `CLAUDE.md` - AI assistant guidelines
- `PRD.md` - Product requirements

## Archived Phases

### Phase 1: Database Foundation ✅
**Completed**: December 17, 2024
- Location: `phase_guides/PHASE1_SETUP_GUIDE.md`
- Status: All database models, migrations, and seed data complete

### Phase 2: Auth & RBAC ✅
**Completed**: December 18, 2025
- Location: `checkpoints/phase2/`
- Files Archived:
  - `CHECKPOINT_M1_COMPLETE.md` - Authentication Endpoints
  - `CHECKPOINT_M2_COMPLETE.md` - Dashboard API
  - `CHECKPOINT_M3_COMPLETE.md` - RBAC Enforcement
  - `CHECKPOINT_M4_COMPLETE.md` - Compliance Instance CRUD with Entity Access
  - `CHECKPOINT_M5_COMPLETE.md` - Audit Logging Service & API
  - `AUDIT_LOG_API_TEST.md` - Comprehensive API testing documentation
- Summary: JWT authentication, RBAC, entity access control, audit logging, dashboard API

## Accessing Archived Documentation

Archived documentation is preserved for:
- Historical reference
- Onboarding new team members
- Understanding implementation decisions
- Audit and compliance requirements

To view archived documentation:
```bash
# List all archived checkpoints
ls -la docs/archive/checkpoints/

# View a specific checkpoint
cat docs/archive/checkpoints/phase2/CHECKPOINT_M5_COMPLETE.md

# Search across archived docs
grep -r "audit logging" docs/archive/
```

## Archive Maintenance

- Archives are kept indefinitely for audit trail purposes
- Files are never deleted, only moved to archive
- Archives are included in version control (git)
- Archives are included in project backups

---

**Last Updated**: December 18, 2025
**Total Phases Archived**: 2 of 12
