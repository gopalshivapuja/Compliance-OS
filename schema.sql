-- ============================================================================
-- Compliance OS V1 - Normalized PostgreSQL Schema
-- ============================================================================
-- This schema implements a multi-tenant compliance management system
-- with full audit trail and evidence management capabilities.
-- ============================================================================

-- Enable UUID extension for generating unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_trgm extension for text search (useful for compliance name searches)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================================
-- CORE TENANT & USER MANAGEMENT
-- ============================================================================

-- Tenants represent organizations using the Compliance OS
-- Multi-tenancy is enforced at the application level with tenant_id filters
CREATE TABLE tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_name VARCHAR(255) NOT NULL,
    tenant_code VARCHAR(50) UNIQUE NOT NULL, -- Short code for URLs/references
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'inactive')),
    subscription_tier VARCHAR(50), -- e.g., 'basic', 'premium'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by UUID, -- User who created this tenant (from users table)
    updated_by UUID,
    metadata JSONB -- Flexible storage for tenant-specific configs
);

-- Users belong to tenants and can have multiple roles
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    UNIQUE(tenant_id, email) -- Email unique within tenant
);

-- Roles define what users can do (e.g., CFO, Tax Lead, Approver)
CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    role_name VARCHAR(100) NOT NULL, -- e.g., 'CFO', 'Tax Lead', 'Payroll Lead'
    role_code VARCHAR(50) NOT NULL, -- e.g., 'CFO', 'TAX_LEAD'
    description TEXT,
    permissions JSONB, -- Flexible permission structure
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(tenant_id, role_code)
);

-- Many-to-many relationship: Users can have multiple roles
CREATE TABLE user_roles (
    user_role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    assigned_by UUID REFERENCES users(user_id),
    UNIQUE(user_id, role_id)
);

-- ============================================================================
-- ENTITY MANAGEMENT
-- ============================================================================

-- Entities are legal entities (companies, branches) within a tenant
-- Each entity has its own compliance obligations
CREATE TABLE entities (
    entity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    entity_name VARCHAR(255) NOT NULL,
    entity_code VARCHAR(50) NOT NULL, -- Short code (e.g., 'IND001', 'BLR-BRANCH')
    entity_type VARCHAR(50), -- e.g., 'Company', 'Branch', 'LLP'
    pan VARCHAR(10), -- Permanent Account Number
    gstin VARCHAR(15), -- GST Identification Number
    cin VARCHAR(21), -- Corporate Identification Number (for companies)
    registration_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'dissolved')),
    address JSONB, -- Flexible address structure
    metadata JSONB, -- Additional entity-specific data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    UNIQUE(tenant_id, entity_code)
);

-- Entity access control: which users can access which entities
CREATE TABLE entity_access (
    entity_access_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    access_level VARCHAR(20) DEFAULT 'view' CHECK (access_level IN ('view', 'edit', 'admin')),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    granted_by UUID REFERENCES users(user_id),
    UNIQUE(entity_id, user_id)
);

-- ============================================================================
-- COMPLIANCE MASTER LIBRARY
-- ============================================================================

-- Compliance Master defines all possible compliance obligations
-- This is the "library" of compliance rules that can be applied
CREATE TABLE compliance_masters (
    compliance_master_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE CASCADE, -- NULL = system-wide template
    compliance_code VARCHAR(100) NOT NULL, -- e.g., 'GSTR-1', 'TDS-Q1', 'AOC-4'
    compliance_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('GST', 'Direct Tax', 'Payroll', 'MCA', 'FEMA', 'FP&A')),
    description TEXT,
    applicable_entity_types VARCHAR(50)[], -- Array of entity types this applies to
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('Monthly', 'Quarterly', 'Annual', 'Event-based', 'Ad-hoc')),
    due_date_rule JSONB NOT NULL, -- Flexible rule engine: e.g., {"type": "monthly", "day": 11, "offset_days": 0}
    owner_role_code VARCHAR(50), -- Default role that owns this compliance
    approver_role_code VARCHAR(50), -- Default role that approves this compliance
    evidence_required BOOLEAN DEFAULT true,
    evidence_types VARCHAR(50)[], -- e.g., ['PDF', 'Challan', 'Acknowledgement']
    severity VARCHAR(20) DEFAULT 'Medium' CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    automation_level VARCHAR(20) DEFAULT 'Manual' CHECK (automation_level IN ('Manual', 'Semi', 'API')),
    dependencies JSONB, -- Array of compliance codes this depends on
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    UNIQUE(tenant_id, compliance_code) -- NULL tenant_id handled separately
);

-- ============================================================================
-- COMPLIANCE INSTANCES
-- ============================================================================

-- Compliance Instances are time-bound occurrences of compliance obligations
-- Each compliance master generates instances based on frequency
CREATE TABLE compliance_instances (
    compliance_instance_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compliance_master_id UUID NOT NULL REFERENCES compliance_masters(compliance_master_id) ON DELETE RESTRICT,
    entity_id UUID NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE, -- Denormalized for performance
    period_start DATE NOT NULL, -- e.g., 2024-01-01 for January 2024
    period_end DATE NOT NULL, -- e.g., 2024-01-31
    period_label VARCHAR(50), -- e.g., 'Jan 2024', 'Q1 FY2024', 'FY2024'
    due_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Not Started' CHECK (status IN ('Not Started', 'In Progress', 'Filed', 'Completed', 'Blocked', 'Overdue', 'Cancelled')),
    actual_completion_date DATE,
    owner_user_id UUID REFERENCES users(user_id), -- Assigned owner (can override master default)
    approver_user_id UUID REFERENCES users(user_id), -- Assigned approver
    blocking_reason TEXT, -- Why status is 'Blocked'
    blocking_compliance_instance_id UUID REFERENCES compliance_instances(compliance_instance_id), -- Dependency blocker
    rag_status VARCHAR(10) DEFAULT 'Green' CHECK (rag_status IN ('Green', 'Amber', 'Red')), -- Calculated field
    notes TEXT,
    metadata JSONB, -- Flexible storage for instance-specific data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id),
    -- Ensure unique instance per compliance+entity+period
    UNIQUE(compliance_master_id, entity_id, period_start, period_end)
);

-- ============================================================================
-- WORKFLOW TASKS
-- ============================================================================

-- Workflow Tasks represent actionable items within a compliance instance
-- Tasks can be assigned to users and tracked through approval workflows
CREATE TABLE workflow_tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compliance_instance_id UUID NOT NULL REFERENCES compliance_instances(compliance_instance_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE, -- Denormalized
    task_type VARCHAR(50) NOT NULL, -- e.g., 'Prepare', 'Review', 'Approve', 'File'
    task_name VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to_user_id UUID REFERENCES users(user_id), -- NULL = unassigned
    assigned_to_role_id UUID REFERENCES roles(role_id), -- Can assign to role instead
    status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'In Progress', 'Completed', 'Rejected', 'Cancelled')),
    priority VARCHAR(20) DEFAULT 'Medium' CHECK (priority IN ('Low', 'Medium', 'High', 'Urgent')),
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    completed_by UUID REFERENCES users(user_id),
    rejection_reason TEXT,
    parent_task_id UUID REFERENCES workflow_tasks(task_id), -- For sub-tasks
    sequence_order INTEGER DEFAULT 0, -- Order of tasks in workflow
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by UUID REFERENCES users(user_id),
    updated_by UUID REFERENCES users(user_id)
);

-- Task comments for collaboration
CREATE TABLE task_comments (
    comment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES workflow_tasks(task_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id),
    comment_text TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT false, -- Internal notes vs. visible comments
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ============================================================================
-- EVIDENCE VAULT
-- ============================================================================

-- Evidence stores files/documents uploaded as proof of compliance
-- Immutable audit trail with versioning support
CREATE TABLE evidence (
    evidence_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    compliance_instance_id UUID NOT NULL REFERENCES compliance_instances(compliance_instance_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE, -- Denormalized
    entity_id UUID NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE, -- Denormalized
    evidence_type VARCHAR(50) NOT NULL, -- e.g., 'PDF', 'Challan', 'Acknowledgement', 'Invoice'
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL, -- Storage path (S3, local, etc.)
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    file_hash VARCHAR(64), -- SHA-256 hash for integrity verification
    version INTEGER DEFAULT 1, -- Version number for same evidence
    parent_evidence_id UUID REFERENCES evidence(evidence_id), -- Points to previous version
    description TEXT,
    uploaded_by_user_id UUID NOT NULL REFERENCES users(user_id),
    approval_status VARCHAR(20) DEFAULT 'Pending' CHECK (approval_status IN ('Pending', 'Approved', 'Rejected')),
    approved_by_user_id UUID REFERENCES users(user_id),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    metadata JSONB, -- Additional metadata (e.g., challan number, reference number)
    is_immutable BOOLEAN DEFAULT true, -- Once approved, cannot be deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
    -- Note: No updated_by to enforce immutability after creation
);

-- Evidence tags for flexible categorization
CREATE TABLE evidence_tags (
    tag_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL,
    tag_color VARCHAR(7), -- Hex color code
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(tenant_id, tag_name)
);

-- Many-to-many: Evidence can have multiple tags
CREATE TABLE evidence_tag_mappings (
    evidence_id UUID NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES evidence_tags(tag_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (evidence_id, tag_id)
);

-- ============================================================================
-- AUDIT LOG (Append-Only)
-- ============================================================================

-- Audit Log captures all significant actions in the system
-- Append-only: records are never updated or deleted
CREATE TABLE audit_logs (
    audit_log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(tenant_id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    entity_id UUID REFERENCES entities(entity_id) ON DELETE SET NULL,
    action_type VARCHAR(50) NOT NULL, -- e.g., 'CREATE', 'UPDATE', 'DELETE', 'APPROVE', 'REJECT'
    resource_type VARCHAR(50) NOT NULL, -- e.g., 'compliance_instance', 'evidence', 'workflow_task'
    resource_id UUID NOT NULL, -- ID of the affected resource
    old_values JSONB, -- Snapshot of values before change (for UPDATE)
    new_values JSONB, -- Snapshot of values after change
    change_summary TEXT, -- Human-readable summary
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Tenant lookups
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_entities_tenant_id ON entities(tenant_id);
CREATE INDEX idx_compliance_masters_tenant_id ON compliance_masters(tenant_id);
CREATE INDEX idx_compliance_instances_tenant_id ON compliance_instances(tenant_id);
CREATE INDEX idx_workflow_tasks_tenant_id ON workflow_tasks(tenant_id);
CREATE INDEX idx_evidence_tenant_id ON evidence(tenant_id);
CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);

-- User and role lookups
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX idx_entity_access_user_id ON entity_access(user_id);
CREATE INDEX idx_entity_access_entity_id ON entity_access(entity_id);

-- Compliance instance queries (most common dashboard queries)
CREATE INDEX idx_compliance_instances_entity_id ON compliance_instances(entity_id);
CREATE INDEX idx_compliance_instances_status ON compliance_instances(status);
CREATE INDEX idx_compliance_instances_due_date ON compliance_instances(due_date);
CREATE INDEX idx_compliance_instances_rag_status ON compliance_instances(rag_status);
CREATE INDEX idx_compliance_instances_owner ON compliance_instances(owner_user_id);
CREATE INDEX idx_compliance_instances_compliance_master ON compliance_instances(compliance_master_id);
-- Composite index for common filter combinations
CREATE INDEX idx_compliance_instances_entity_status_due ON compliance_instances(entity_id, status, due_date);

-- Compliance master lookups
CREATE INDEX idx_compliance_masters_category ON compliance_masters(category);
CREATE INDEX idx_compliance_masters_code ON compliance_masters(compliance_code);
CREATE INDEX idx_compliance_masters_active ON compliance_masters(is_active) WHERE is_active = true;

-- Workflow task queries
CREATE INDEX idx_workflow_tasks_compliance_instance ON workflow_tasks(compliance_instance_id);
CREATE INDEX idx_workflow_tasks_assigned_to ON workflow_tasks(assigned_to_user_id);
CREATE INDEX idx_workflow_tasks_status ON workflow_tasks(status);
CREATE INDEX idx_workflow_tasks_due_date ON workflow_tasks(due_date);
CREATE INDEX idx_task_comments_task_id ON task_comments(task_id);

-- Evidence queries
CREATE INDEX idx_evidence_compliance_instance ON evidence(compliance_instance_id);
CREATE INDEX idx_evidence_entity_id ON evidence(entity_id);
CREATE INDEX idx_evidence_uploaded_by ON evidence(uploaded_by_user_id);
CREATE INDEX idx_evidence_approval_status ON evidence(approval_status);
CREATE INDEX idx_evidence_type ON evidence(evidence_type);
CREATE INDEX idx_evidence_created_at ON evidence(created_at DESC); -- For recent uploads

-- Audit log queries (time-series queries are common)
CREATE INDEX idx_audit_logs_tenant_created ON audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Text search indexes (for compliance name searches)
CREATE INDEX idx_compliance_masters_name_trgm ON compliance_masters USING gin(compliance_name gin_trgm_ops);
CREATE INDEX idx_entities_name_trgm ON entities USING gin(entity_name gin_trgm_ops);

-- ============================================================================
-- FUNCTIONS & TRIGGERS FOR AUDIT TRAIL
-- ============================================================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables with updated_at column
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entities_updated_at BEFORE UPDATE ON entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compliance_masters_updated_at BEFORE UPDATE ON compliance_masters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compliance_instances_updated_at BEFORE UPDATE ON compliance_instances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_tasks_updated_at BEFORE UPDATE ON workflow_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_comments_updated_at BEFORE UPDATE ON task_comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_evidence_updated_at BEFORE UPDATE ON evidence
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically log changes to audit_logs
-- Note: This is a template function. Each table needs a custom trigger
-- that extracts the correct primary key column name.
-- For V1, application-level audit logging is recommended for flexibility.
CREATE OR REPLACE FUNCTION log_audit_event()
RETURNS TRIGGER AS $$
DECLARE
    v_tenant_id UUID;
    v_user_id UUID;
    v_entity_id UUID;
    v_resource_id UUID;
BEGIN
    -- Determine tenant_id, user_id, entity_id, and resource_id based on table
    IF TG_TABLE_NAME = 'compliance_instances' THEN
        v_tenant_id := NEW.tenant_id;
        v_user_id := COALESCE(NEW.updated_by, NEW.created_by);
        v_entity_id := NEW.entity_id;
        v_resource_id := NEW.compliance_instance_id;
    ELSIF TG_TABLE_NAME = 'entities' THEN
        v_tenant_id := NEW.tenant_id;
        v_user_id := COALESCE(NEW.updated_by, NEW.created_by);
        v_entity_id := NEW.entity_id;
        v_resource_id := NEW.entity_id;
    ELSIF TG_TABLE_NAME = 'evidence' THEN
        v_tenant_id := NEW.tenant_id;
        v_user_id := NEW.uploaded_by_user_id;
        v_entity_id := NEW.entity_id;
        v_resource_id := NEW.evidence_id;
    ELSIF TG_TABLE_NAME = 'workflow_tasks' THEN
        v_tenant_id := NEW.tenant_id;
        v_user_id := COALESCE(NEW.updated_by, NEW.created_by);
        v_entity_id := NULL; -- Tasks don't directly link to entities
        v_resource_id := NEW.task_id;
    ELSE
        -- Generic fallback: try to extract common fields
        v_tenant_id := COALESCE((NEW::jsonb)->>'tenant_id', NULL)::UUID;
        v_user_id := COALESCE((NEW::jsonb)->>'updated_by', (NEW::jsonb)->>'created_by', NULL)::UUID;
        v_entity_id := COALESCE((NEW::jsonb)->>'entity_id', NULL)::UUID;
        v_resource_id := NULL; -- Cannot determine without table-specific logic
    END IF;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (
            tenant_id, user_id, entity_id,
            action_type, resource_type, resource_id,
            new_values, change_summary
        ) VALUES (
            v_tenant_id, v_user_id, v_entity_id,
            'CREATE', TG_TABLE_NAME, v_resource_id,
            row_to_json(NEW), 'Created ' || TG_TABLE_NAME
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (
            tenant_id, user_id, entity_id,
            action_type, resource_type, resource_id,
            old_values, new_values, change_summary
        ) VALUES (
            v_tenant_id, v_user_id, v_entity_id,
            'UPDATE', TG_TABLE_NAME, v_resource_id,
            row_to_json(OLD), row_to_json(NEW), 'Updated ' || TG_TABLE_NAME
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        -- For DELETE, extract from OLD record
        IF TG_TABLE_NAME = 'compliance_instances' THEN
            v_tenant_id := OLD.tenant_id;
            v_entity_id := OLD.entity_id;
            v_resource_id := OLD.compliance_instance_id;
        ELSIF TG_TABLE_NAME = 'entities' THEN
            v_tenant_id := OLD.tenant_id;
            v_entity_id := OLD.entity_id;
            v_resource_id := OLD.entity_id;
        ELSIF TG_TABLE_NAME = 'evidence' THEN
            v_tenant_id := OLD.tenant_id;
            v_entity_id := OLD.entity_id;
            v_resource_id := OLD.evidence_id;
        ELSIF TG_TABLE_NAME = 'workflow_tasks' THEN
            v_tenant_id := OLD.tenant_id;
            v_resource_id := OLD.task_id;
        END IF;
        
        INSERT INTO audit_logs (
            tenant_id, user_id, entity_id,
            action_type, resource_type, resource_id,
            old_values, change_summary
        ) VALUES (
            v_tenant_id, NULL, v_entity_id,
            'DELETE', TG_TABLE_NAME, v_resource_id,
            row_to_json(OLD), 'Deleted ' || TG_TABLE_NAME
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Note: Audit triggers would be added selectively to critical tables
-- For V1, we'll rely on application-level audit logging for flexibility
-- Uncomment below to enable automatic audit logging:

-- CREATE TRIGGER audit_compliance_instances AFTER INSERT OR UPDATE OR DELETE ON compliance_instances
--     FOR EACH ROW EXECUTE FUNCTION log_audit_event();

-- CREATE TRIGGER audit_evidence AFTER INSERT OR UPDATE OR DELETE ON evidence
--     FOR EACH ROW EXECUTE FUNCTION log_audit_event();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View: Compliance Instance with Master Details
-- Makes it easy to query instances with their master compliance info
CREATE OR REPLACE VIEW v_compliance_instances_detail AS
SELECT 
    ci.compliance_instance_id,
    ci.entity_id,
    ci.tenant_id,
    ci.period_start,
    ci.period_end,
    ci.period_label,
    ci.due_date,
    ci.status,
    ci.rag_status,
    ci.actual_completion_date,
    cm.compliance_master_id,
    cm.compliance_code,
    cm.compliance_name,
    cm.category,
    cm.frequency,
    cm.severity,
    e.entity_name,
    e.entity_code,
    u_owner.email AS owner_email,
    u_owner.full_name AS owner_name,
    u_approver.email AS approver_email,
    u_approver.full_name AS approver_name
FROM compliance_instances ci
JOIN compliance_masters cm ON ci.compliance_master_id = cm.compliance_master_id
JOIN entities e ON ci.entity_id = e.entity_id
LEFT JOIN users u_owner ON ci.owner_user_id = u_owner.user_id
LEFT JOIN users u_approver ON ci.approver_user_id = u_approver.user_id;

-- View: Overdue Compliance Instances
-- Quick view of all overdue items
CREATE OR REPLACE VIEW v_overdue_compliance AS
SELECT 
    ci.*,
    cm.compliance_name,
    cm.category,
    e.entity_name,
    CURRENT_DATE - ci.due_date AS days_overdue
FROM compliance_instances ci
JOIN compliance_masters cm ON ci.compliance_master_id = cm.compliance_master_id
JOIN entities e ON ci.entity_id = e.entity_id
WHERE ci.status NOT IN ('Completed', 'Filed', 'Cancelled')
    AND ci.due_date < CURRENT_DATE;

-- View: Evidence Summary by Compliance Instance
-- Shows evidence count and approval status per instance
CREATE OR REPLACE VIEW v_evidence_summary AS
SELECT 
    compliance_instance_id,
    COUNT(*) AS total_evidence_count,
    COUNT(*) FILTER (WHERE approval_status = 'Approved') AS approved_count,
    COUNT(*) FILTER (WHERE approval_status = 'Pending') AS pending_count,
    COUNT(*) FILTER (WHERE approval_status = 'Rejected') AS rejected_count,
    MAX(created_at) AS latest_upload_date
FROM evidence
GROUP BY compliance_instance_id;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE tenants IS 'Multi-tenant isolation: Each organization using Compliance OS';
COMMENT ON TABLE entities IS 'Legal entities (companies, branches) within a tenant that have compliance obligations';
COMMENT ON TABLE compliance_masters IS 'Library of all compliance obligations (templates)';
COMMENT ON TABLE compliance_instances IS 'Time-bound occurrences of compliance obligations for specific entities';
COMMENT ON TABLE workflow_tasks IS 'Actionable tasks within compliance instances for workflow management';
COMMENT ON TABLE evidence IS 'Immutable evidence vault for audit-ready compliance proof';
COMMENT ON TABLE audit_logs IS 'Append-only audit trail of all system actions';

COMMENT ON COLUMN compliance_instances.tenant_id IS 'Denormalized for performance: avoids joins in tenant-scoped queries';
COMMENT ON COLUMN workflow_tasks.tenant_id IS 'Denormalized for performance: avoids joins in tenant-scoped queries';
COMMENT ON COLUMN evidence.tenant_id IS 'Denormalized for performance: avoids joins in tenant-scoped queries';
COMMENT ON COLUMN evidence.is_immutable IS 'Once approved, evidence cannot be deleted to maintain audit integrity';

