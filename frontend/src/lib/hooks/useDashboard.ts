/**
 * React Query hooks for dashboard data
 */
import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/lib/api/endpoints'
import type {
  DashboardOverview,
  ComplianceInstanceSummary,
  CategoryBreakdown,
} from '@/types/dashboard'

/**
 * Fetch dashboard overview with RAG counts and metrics
 * Refetches every 5 minutes to keep data fresh
 */
export function useDashboardOverview() {
  return useQuery<DashboardOverview>({
    queryKey: ['dashboard', 'overview'],
    queryFn: async () => {
      const response = await dashboardApi.getOverview()
      return response.data
    },
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    staleTime: 2 * 60 * 1000, // Consider stale after 2 minutes
  })
}

/**
 * Fetch overdue compliance items
 * @param skip - Pagination offset
 * @param limit - Number of items to fetch
 */
export function useOverdueItems(skip = 0, limit = 10) {
  return useQuery<ComplianceInstanceSummary[]>({
    queryKey: ['dashboard', 'overdue', skip, limit],
    queryFn: async () => {
      const response = await dashboardApi.getOverdue({ skip, limit })
      return response.data
    },
    staleTime: 2 * 60 * 1000,
  })
}

/**
 * Fetch upcoming compliance items due in next N days
 * @param days - Number of days to look ahead (default 7)
 * @param skip - Pagination offset
 * @param limit - Number of items to fetch
 */
export function useUpcomingItems(days = 7, skip = 0, limit = 10) {
  return useQuery<ComplianceInstanceSummary[]>({
    queryKey: ['dashboard', 'upcoming', days, skip, limit],
    queryFn: async () => {
      const response = await dashboardApi.getUpcoming({ days, skip, limit })
      return response.data
    },
    staleTime: 2 * 60 * 1000,
  })
}

/**
 * Fetch category breakdown with RAG distribution
 */
export function useCategoryBreakdown() {
  return useQuery<CategoryBreakdown[]>({
    queryKey: ['dashboard', 'category-breakdown'],
    queryFn: async () => {
      const response = await dashboardApi.getCategoryBreakdown()
      return response.data
    },
    staleTime: 5 * 60 * 1000, // Stale after 5 minutes
  })
}
