# Compliance OS V1 - Database Schema Design Document

## 🎯 Overview

This document explains the normalized PostgreSQL schema design for Compliance OS V1. The schema implements a multi-tenant compliance management system with full audit trail capabilities, designed to handle GCC (Global Capability Center) compliance operations in India.

---

## 🏗️ Design Principles

### 1. **Normalization**
- **3NF (Third Normal Form)**: Eliminated redundant data across tables
- **Separation of Concerns**: Master data (templates) separated from instance data (actual occurrences)
- **Referential Integrity**: Foreign keys ensure data consistency

### 2. **Multi-Tenancy**
- Every table includes `tenant_id` for data isolation
- Application-level filtering ensures tenants can only access their own data
- Some tables denormalize `tenant_id` for performance (avoids expensive joins)

### 3. **Audit Trail**
- **Append-only** `audit_logs` table (never updated/deleted)
- `created_at`, `updated_at`, `created_by`, `updated_by` on all mutable tables
- Evidence immutability: once approved, evidence cannot be deleted

### 4. **Performance Optimization**
- Strategic indexes on frequently queried columns
- Composite indexes for common filter combinations
- Denormalization where joins would be expensive (dashboard queries)

---

## 📊 Core Tables Explained

### 1. **Tenants** 🏢
**Purpose**: Multi-tenant isolation - each organization using Compliance OS

**Key Fields**:
- `tenant_id`: Primary key (UUID)
- `tenant_code`: Short code for URLs/references (e.g., "ACME-CORP")
- `status`: Active/suspended/inactive
- `metadata`: JSONB for flexible tenant-specific configs

**Why UUID?** UUIDs prevent tenant ID enumeration attacks and work well in distributed systems.

---

### 2. **Entities** 🏛️
**Purpose**: Legal entities (companies, branches) within a tenant that have compliance obligations

**Key Fields**:
- `entity_id`: Primary key
- `tenant_id`: Foreign key to tenants
- `entity_code`: Short code (e.g., "IND001", "BLR-BRANCH")
- `pan`, `gstin`, `cin`: Indian tax/company identifiers
- `entity_type`: Company, Branch, LLP, etc.

**Design Decision**: Storing Indian identifiers (`pan`, `gstin`, `cin`) directly in the table because they're frequently queried and indexed. Could be in `metadata` JSONB, but direct columns are faster.

---

### 3. **Compliance Masters** 📚
**Purpose**: The "library" of all compliance obligations (templates)

**Key Fields**:
- `compliance_master_id`: Primary key
- `compliance_code`: Unique code (e.g., "GSTR-1", "TDS-Q1")
- `compliance_name`: Human-readable name
- `category`: GST, Direct Tax, Payroll, MCA, FEMA, FP&A
- `frequency`: Monthly, Quarterly, Annual, Event-based
- `due_date_rule`: JSONB for flexible rule engine
  ```json
  {
    "type": "monthly",
    "day": 11,
    "offset_days": 0
  }
  ```
- `owner_role_code`, `approver_role_code`: Default roles
- `dependencies`: JSONB array of compliance codes this depends on

**Why JSONB for `due_date_rule`?** Compliance due dates vary wildly:
- Monthly: "11th of next month"
- Quarterly: "Last day of month following quarter end"
- Annual: "30th September"
- Event-based: "Within 30 days of event"

JSONB allows flexible rules without schema changes.

**Design Decision**: `tenant_id` can be NULL for system-wide templates (shared across all tenants) or set for tenant-specific customizations.

---

### 4. **Compliance Instances** ⚡
**Purpose**: Time-bound occurrences of compliance obligations for specific entities

**Key Fields**:
- `compliance_instance_id`: Primary key
- `compliance_master_id`: Links to the master template
- `entity_id`: Which entity this applies to
- `period_start`, `period_end`: Time period (e.g., Jan 1-31, 2024)
- `due_date`: Calculated from master's `due_date_rule`
- `status`: Not Started, In Progress, Filed, Completed, Blocked, Overdue
- `rag_status`: Green, Amber, Red (calculated)
- `blocking_compliance_instance_id`: Self-referential FK for dependencies

**Why Denormalize `tenant_id`?** Dashboard queries filter by tenant first, then show instances. Without denormalization:
```sql
SELECT ci.* FROM compliance_instances ci
JOIN entities e ON ci.entity_id = e.entity_id
WHERE e.tenant_id = 'xxx'
```
With denormalization:
```sql
SELECT * FROM compliance_instances WHERE tenant_id = 'xxx'
```
Much faster! The small storage cost is worth the query performance gain.

**Unique Constraint**: `(compliance_master_id, entity_id, period_start, period_end)` ensures no duplicate instances.

---

### 5. **Workflow Tasks** ✅
**Purpose**: Actionable tasks within compliance instances (maker-checker workflows)

**Key Fields**:
- `task_id`: Primary key
- `compliance_instance_id`: Which compliance this task belongs to
- `task_type`: Prepare, Review, Approve, File
- `assigned_to_user_id` OR `assigned_to_role_id`: Can assign to user or role
- `status`: Pending, In Progress, Completed, Rejected
- `parent_task_id`: Self-referential FK for sub-tasks
- `sequence_order`: Order in workflow

**Design Decision**: Tasks can be assigned to either a user OR a role. If assigned to a role, the application resolves which users have that role at runtime. This supports dynamic assignment.

---

### 6. **Evidence** 📎
**Purpose**: Immutable evidence vault for audit-ready compliance proof

**Key Fields**:
- `evidence_id`: Primary key
- `compliance_instance_id`: Which compliance this proves
- `file_path`: Storage path (S3, local filesystem, etc.)
- `file_hash`: SHA-256 hash for integrity verification
- `version`: Version number (for updates)
- `parent_evidence_id`: Points to previous version
- `approval_status`: Pending, Approved, Rejected
- `is_immutable`: Once approved, cannot be deleted

**Why Immutability?** Auditors need to see what was approved at a point in time. If evidence can be deleted, audit trail breaks.

**Versioning**: When evidence is updated, a new row is created with `version = old_version + 1` and `parent_evidence_id` pointing to the old row. Old versions remain in the database.

**Design Decision**: No `updated_by` field - once created, evidence is immutable (except metadata updates before approval).

---

### 7. **Audit Logs** 📝
**Purpose**: Append-only audit trail of all system actions

**Key Fields**:
- `audit_log_id`: Primary key
- `action_type`: CREATE, UPDATE, DELETE, APPROVE, REJECT
- `resource_type`: Which table (e.g., "compliance_instance")
- `resource_id`: ID of affected record
- `old_values`, `new_values`: JSONB snapshots (before/after)
- `change_summary`: Human-readable summary

**Why Append-Only?** Audit logs must be tamper-proof. Once written, never updated or deleted. This ensures auditors can trust the trail.

**Storage Consideration**: `old_values` and `new_values` store full row snapshots as JSONB. This can be large, but provides complete auditability. Consider archiving old logs to cold storage.

---

## 🔗 Relationships & Foreign Keys

### One-to-Many Relationships:
- `Tenant` → `Users` (one tenant has many users)
- `Tenant` → `Entities` (one tenant has many entities)
- `Tenant` → `Compliance Masters` (one tenant has many compliance templates)
- `Entity` → `Compliance Instances` (one entity has many compliance instances)
- `Compliance Master` → `Compliance Instances` (one master generates many instances)
- `Compliance Instance` → `Workflow Tasks` (one instance has many tasks)
- `Compliance Instance` → `Evidence` (one instance has many evidence files)

### Many-to-Many Relationships:
- `Users` ↔ `Roles` (via `user_roles` junction table)
- `Users` ↔ `Entities` (via `entity_access` for access control)
- `Evidence` ↔ `Tags` (via `evidence_tag_mappings`)

### Self-Referential Relationships:
- `Compliance Instances` → `Compliance Instances` (blocking dependencies)
- `Workflow Tasks` → `Workflow Tasks` (sub-tasks)
- `Evidence` → `Evidence` (versioning)

---

## 📈 Indexes Strategy

### Performance Indexes:
1. **Tenant-scoped queries**: Every table has `idx_*_tenant_id` for fast tenant filtering
2. **Status filters**: `idx_compliance_instances_status` for dashboard RAG queries
3. **Due date queries**: `idx_compliance_instances_due_date` for calendar views
4. **Composite indexes**: `idx_compliance_instances_entity_status_due` for common filter combinations

### Text Search:
- **Trigram indexes** (`pg_trgm`) on `compliance_name` and `entity_name` for fuzzy search
- Enables queries like: "Find compliance with name containing 'GST'"

### Time-Series Queries:
- **Descending indexes** on `created_at` for recent-first queries (audit logs, evidence)

---

## 🔒 Security Considerations

### 1. **Row-Level Security (RLS)**
PostgreSQL RLS can be enabled for additional security:
```sql
ALTER TABLE compliance_instances ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON compliance_instances
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

### 2. **Access Control**
- `entity_access` table controls which users can access which entities
- Application enforces access checks before queries

### 3. **Evidence Immutability**
- `is_immutable` flag prevents deletion after approval
- Application logic should enforce: "Cannot delete if `is_immutable = true`"

---

## 🚀 Query Patterns & Performance

### Common Queries:

#### 1. **Dashboard: Overdue Items**
```sql
SELECT * FROM v_overdue_compliance
WHERE tenant_id = 'xxx'
ORDER BY days_overdue DESC;
```
Uses: `idx_compliance_instances_tenant_id`, `idx_compliance_instances_due_date`

#### 2. **Compliance Calendar**
```sql
SELECT * FROM compliance_instances
WHERE tenant_id = 'xxx'
  AND due_date BETWEEN '2024-01-01' AND '2024-01-31'
ORDER BY due_date;
```
Uses: Composite index `idx_compliance_instances_entity_status_due`

#### 3. **Evidence by Compliance**
```sql
SELECT * FROM evidence
WHERE compliance_instance_id = 'xxx'
  AND approval_status = 'Approved'
ORDER BY created_at DESC;
```
Uses: `idx_evidence_compliance_instance`, `idx_evidence_approval_status`

---

## 🎓 Learning Notes

### Why UUIDs Instead of Auto-Increment Integers?
- **Security**: Can't enumerate tenant IDs (prevents attacks)
- **Distributed Systems**: No coordination needed for ID generation
- **Privacy**: Harder to guess/scan IDs
- **Trade-off**: Slightly larger storage (16 bytes vs 4-8 bytes), but worth it for security

### Why JSONB Instead of Separate Tables?
For flexible fields like `due_date_rule` and `dependencies`:
- **Flexibility**: Different compliance types have different rule structures
- **No Schema Changes**: Add new rule types without migrations
- **Queryable**: Can still query JSONB fields (`WHERE due_date_rule->>'type' = 'monthly'`)
- **Trade-off**: Less type safety, but acceptable for configuration data

### Denormalization Trade-offs:
**Denormalized `tenant_id` in `compliance_instances`**:
- ✅ Faster queries (no join needed)
- ✅ Simpler application code
- ❌ Storage overhead (duplicate data)
- ❌ Must keep in sync (application responsibility)

**Decision**: Worth it! Dashboard queries are the most common, and they filter by tenant first.

---

## 🔮 Future Enhancements

### V2 Considerations:
1. **Partitioning**: Partition `audit_logs` by `created_at` (monthly partitions) for better performance
2. **Materialized Views**: Pre-compute dashboard aggregations
3. **Full-Text Search**: Add `tsvector` columns for advanced search
4. **Soft Deletes**: Add `deleted_at` columns instead of hard deletes
5. **Event Sourcing**: Consider event store for compliance state changes

---

## 📋 Checklist for Implementation

- [x] All core tables defined
- [x] Primary keys on all tables
- [x] Foreign keys for referential integrity
- [x] Indexes for performance
- [x] Audit fields (`created_at`, `updated_at`, etc.)
- [x] Multi-tenant isolation (`tenant_id` everywhere)
- [x] Evidence immutability design
- [x] Append-only audit log
- [x] Views for common queries
- [x] Triggers for `updated_at` automation
- [x] Documentation

---

## 🎉 Summary

This schema provides:
- ✅ **Normalized structure** (3NF) for data integrity
- ✅ **Multi-tenant isolation** for security
- ✅ **Performance optimization** via indexes and denormalization
- ✅ **Audit trail** for compliance readiness
- ✅ **Flexibility** via JSONB for varying compliance rules
- ✅ **Scalability** via UUIDs and proper indexing

The design balances normalization (data integrity) with denormalization (performance), ensuring Compliance OS can handle GCC operations efficiently while maintaining audit-ready data structures.

---

**Remember**: "If it cannot stand up to an auditor, it does not ship." This schema is designed with that principle in mind! 🎯


