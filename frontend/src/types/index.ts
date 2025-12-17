/**
 * TypeScript type definitions
 * TODO: Add types based on API responses
 */

export interface Tenant {
  tenant_id: string
  tenant_name: string
  tenant_code: string
  status: 'active' | 'suspended' | 'inactive'
}

export interface Entity {
  entity_id: string
  tenant_id: string
  entity_name: string
  entity_code: string
  entity_type?: string
  pan?: string
  gstin?: string
  cin?: string
  status: 'active' | 'inactive' | 'dissolved'
}

export interface ComplianceMaster {
  compliance_master_id: string
  tenant_id?: string
  compliance_code: string
  compliance_name: string
  category: 'GST' | 'Direct Tax' | 'Payroll' | 'MCA' | 'FEMA' | 'FP&A'
  frequency: 'Monthly' | 'Quarterly' | 'Annual' | 'Event-based' | 'Ad-hoc'
  severity: 'Low' | 'Medium' | 'High' | 'Critical'
}

export interface ComplianceInstance {
  compliance_instance_id: string
  compliance_master_id: string
  entity_id: string
  tenant_id: string
  period_start: string
  period_end: string
  period_label: string
  due_date: string
  status:
    | 'Not Started'
    | 'In Progress'
    | 'Filed'
    | 'Completed'
    | 'Blocked'
    | 'Overdue'
    | 'Cancelled'
  rag_status: 'Green' | 'Amber' | 'Red'
  actual_completion_date?: string
}

export interface WorkflowTask {
  task_id: string
  compliance_instance_id: string
  task_type: string
  task_name: string
  status: 'Pending' | 'In Progress' | 'Completed' | 'Rejected' | 'Cancelled'
  assigned_to_user_id?: string
  due_date?: string
}

export interface Evidence {
  evidence_id: string
  compliance_instance_id: string
  entity_id: string
  evidence_type: string
  file_name: string
  approval_status: 'Pending' | 'Approved' | 'Rejected'
  uploaded_by_user_id: string
  created_at: string
}

export interface AuditLog {
  audit_log_id: string
  tenant_id?: string
  user_id?: string
  action_type: string
  resource_type: string
  resource_id: string
  created_at: string
}

