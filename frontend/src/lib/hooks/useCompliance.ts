/**
 * React Query hooks for compliance instance data
 */
import { useQuery } from '@tanstack/react-query'
import { complianceInstancesApi } from '@/lib/api/endpoints'
import type {
  ComplianceInstanceResponse,
  ComplianceInstanceListResponse,
} from '@/types/compliance'

/**
 * Fetch list of compliance instances with filters
 * @param entity_id - Filter by entity ID
 * @param status - Filter by status
 * @param category - Filter by category
 * @param rag_status - Filter by RAG status (Green/Amber/Red)
 * @param owner_id - Filter by owner user ID
 * @param skip - Pagination offset
 * @param limit - Number of items to fetch
 */
export function useComplianceInstances(
  entity_id?: string,
  status?: string,
  category?: string,
  rag_status?: string,
  owner_id?: string,
  skip = 0,
  limit = 50
) {
  return useQuery<ComplianceInstanceListResponse>({
    queryKey: [
      'compliance',
      'instances',
      entity_id,
      status,
      category,
      rag_status,
      owner_id,
      skip,
      limit,
    ],
    queryFn: async () => {
      const response = await complianceInstancesApi.list({
        entity_id,
        status,
        category,
        rag_status,
        owner_id,
        skip,
        limit,
      })
      return response.data
    },
    staleTime: 2 * 60 * 1000, // Consider stale after 2 minutes
  })
}

/**
 * Fetch a single compliance instance by ID
 * @param id - Compliance instance ID
 */
export function useComplianceInstance(id: string) {
  return useQuery<ComplianceInstanceResponse>({
    queryKey: ['compliance', 'instance', id],
    queryFn: async () => {
      const response = await complianceInstancesApi.get(id)
      return response.data
    },
    staleTime: 2 * 60 * 1000,
    enabled: !!id, // Only fetch if ID is provided
  })
}
