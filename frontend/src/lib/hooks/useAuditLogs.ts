/**
 * React Query hooks for audit log data
 */
import { useQuery } from '@tanstack/react-query'
import { auditLogsApi } from '@/lib/api/endpoints'
import type {
  AuditLogResponse,
  AuditLogListResponse,
  ResourceAuditTrailResponse,
  ResourceType,
  ActionType,
} from '@/types/audit'

/**
 * Fetch list of audit logs with filters
 * @param resource_type - Filter by resource type (user, compliance_instance, etc.)
 * @param resource_id - Filter by specific resource ID
 * @param user_id - Filter by user ID
 * @param action_type - Filter by action type (CREATE, UPDATE, DELETE, etc.)
 * @param skip - Pagination offset
 * @param limit - Number of items to fetch
 */
export function useAuditLogs(
  resource_type?: ResourceType,
  resource_id?: string,
  user_id?: string,
  action_type?: ActionType,
  skip = 0,
  limit = 50
) {
  return useQuery<AuditLogListResponse>({
    queryKey: [
      'audit',
      'logs',
      resource_type,
      resource_id,
      user_id,
      action_type,
      skip,
      limit,
    ],
    queryFn: async () => {
      const response = await auditLogsApi.list({
        resource_type,
        resource_id,
        user_id,
        action_type,
        skip,
        limit,
      })
      return response.data
    },
    staleTime: 2 * 60 * 1000, // Consider stale after 2 minutes
  })
}

/**
 * Fetch complete audit trail for a specific resource
 * @param resource_type - Type of resource (compliance_instance, user, entity, etc.)
 * @param resource_id - ID of the resource
 */
export function useResourceAuditTrail(
  resource_type: ResourceType,
  resource_id: string
) {
  return useQuery<ResourceAuditTrailResponse>({
    queryKey: ['audit', 'trail', resource_type, resource_id],
    queryFn: async () => {
      const response = await auditLogsApi.getResourceTrail(resource_type, resource_id)
      return response.data
    },
    staleTime: 2 * 60 * 1000,
    enabled: !!(resource_type && resource_id), // Only fetch if both params provided
  })
}

/**
 * Fetch a single audit log by ID
 * @param id - Audit log ID
 */
export function useAuditLog(id: string) {
  return useQuery<AuditLogResponse>({
    queryKey: ['audit', 'log', id],
    queryFn: async () => {
      const response = await auditLogsApi.get(id)
      return response.data
    },
    staleTime: 5 * 60 * 1000, // Audit logs are immutable, can cache longer
    enabled: !!id, // Only fetch if ID is provided
  })
}
