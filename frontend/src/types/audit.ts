/**
 * TypeScript types for Audit Log data structures
 * Matches backend Pydantic schemas in backend/app/schemas/audit.py
 */

export interface AuditLogResponse {
  audit_log_id: string
  tenant_id: string
  user_id: string
  user_name: string | null
  user_email: string | null
  action_type: ActionType
  resource_type: ResourceType
  resource_id: string
  old_values: Record<string, any> | null
  new_values: Record<string, any> | null
  change_summary: string
  ip_address: string | null
  user_agent: string | null
  created_at: string // ISO datetime string
}

export interface AuditLogListResponse {
  items: AuditLogResponse[]
  total: number
  skip: number
  limit: number
}

export interface ResourceAuditTrailResponse {
  resource_type: ResourceType
  resource_id: string
  audit_logs: AuditLogResponse[]
  total_changes: number
}

// Helper types for action types
export type ActionType =
  | 'CREATE'
  | 'UPDATE'
  | 'DELETE'
  | 'LOGIN'
  | 'LOGOUT'
  | 'APPROVE'
  | 'REJECT'
  | 'VIEW'
  | 'DOWNLOAD'
  | 'UPLOAD'

// Helper types for resource types
export type ResourceType =
  | 'user'
  | 'tenant'
  | 'entity'
  | 'compliance_master'
  | 'compliance_instance'
  | 'workflow_task'
  | 'evidence'
  | 'notification'
  | 'role'
  | 'entity_access'

// Helper interface for audit log filters
export interface AuditLogFilters {
  resource_type?: ResourceType
  resource_id?: string
  user_id?: string
  action_type?: ActionType
  skip?: number
  limit?: number
}

// Helper type for action color coding
export const ActionTypeColors: Record<ActionType, string> = {
  CREATE: 'text-green-700 bg-green-100',
  UPDATE: 'text-blue-700 bg-blue-100',
  DELETE: 'text-red-700 bg-red-100',
  LOGIN: 'text-gray-700 bg-gray-100',
  LOGOUT: 'text-gray-700 bg-gray-100',
  APPROVE: 'text-green-700 bg-green-100',
  REJECT: 'text-red-700 bg-red-100',
  VIEW: 'text-gray-700 bg-gray-100',
  DOWNLOAD: 'text-blue-700 bg-blue-100',
  UPLOAD: 'text-purple-700 bg-purple-100',
}
