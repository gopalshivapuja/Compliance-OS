/**
 * TypeScript types for Dashboard data structures
 */

export interface RAGCounts {
  green: number
  amber: number
  red: number
}

export interface CategoryBreakdown {
  category: string
  green: number
  amber: number
  red: number
  total: number
}

export interface DashboardOverview {
  total_compliances: number
  rag_counts: RAGCounts
  overdue_count: number
  upcoming_count: number
  category_breakdown: CategoryBreakdown[]
}

export interface ComplianceInstanceSummary {
  compliance_instance_id: string
  compliance_name: string
  compliance_code: string
  entity_name: string
  entity_code: string
  category: string
  sub_category: string | null
  due_date: string
  rag_status: 'Green' | 'Amber' | 'Red'
  status: string
  owner_name: string | null
  frequency: string
  period_start: string
  period_end: string
  days_overdue: number | null
}

export type RAGStatus = 'Green' | 'Amber' | 'Red'
