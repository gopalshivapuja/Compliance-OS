/**
 * TypeScript types for Compliance Instance data structures
 * Matches backend Pydantic schemas in backend/app/schemas/compliance_instance.py
 */

export interface ComplianceInstanceResponse {
  compliance_instance_id: string
  compliance_master_id: string
  compliance_code: string
  compliance_name: string
  entity_id: string
  entity_name: string
  entity_code: string
  category: string
  sub_category: string | null
  frequency: string
  due_date: string // ISO date string
  status: string
  rag_status: 'Green' | 'Amber' | 'Red'
  period_start: string // ISO date string
  period_end: string // ISO date string
  owner_id: string | null
  owner_name: string | null
  approver_id: string | null
  approver_name: string | null
  filed_date: string | null // ISO date string
  completion_date: string | null // ISO date string
  completion_remarks: string | null
  remarks: string | null
  meta_data: Record<string, any> | null
  created_at: string // ISO datetime string
  updated_at: string // ISO datetime string
  created_by: string | null
  updated_by: string | null
}

export interface ComplianceInstanceListResponse {
  items: ComplianceInstanceResponse[]
  total: number
  skip: number
  limit: number
}

export interface ComplianceInstanceUpdate {
  status?: string
  rag_status?: 'Green' | 'Amber' | 'Red'
  owner_user_id?: string
  approver_user_id?: string
  filed_date?: string // ISO date string
  completion_date?: string // ISO date string
  completion_remarks?: string
  remarks?: string
}

// Helper type for compliance statuses
export type ComplianceStatus =
  | 'Not Started'
  | 'In Progress'
  | 'Pending Review'
  | 'Pending Approval'
  | 'Filed'
  | 'Completed'
  | 'Rejected'
  | 'Overdue'

// Helper type for categories
export type ComplianceCategory = 'GST' | 'Direct Tax' | 'Payroll' | 'MCA' | 'FEMA' | 'FP&A'

// Helper type for frequency
export type ComplianceFrequency = 'Monthly' | 'Quarterly' | 'Annual' | 'Event-based'
