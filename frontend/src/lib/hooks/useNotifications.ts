/**
 * React Query hooks for notifications data
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '@/lib/api/endpoints'
import type {
  NotificationResponse,
  NotificationListResponse,
  NotificationCountResponse,
  NotificationMarkReadResponse,
} from '@/types/notification'

/**
 * Fetch unread notification count
 * Refetches every 60 seconds to keep count fresh
 */
export function useNotificationCount() {
  return useQuery<NotificationCountResponse>({
    queryKey: ['notifications', 'count'],
    queryFn: async () => {
      const response = await notificationsApi.getCount()
      return response.data
    },
    refetchInterval: 60 * 1000, // Refresh every 60 seconds
    staleTime: 30 * 1000, // Consider stale after 30 seconds
  })
}

/**
 * Fetch list of notifications with optional filters
 * @param options - Filter options
 */
export function useNotifications(options?: {
  isRead?: boolean
  skip?: number
  limit?: number
}) {
  const { isRead, skip = 0, limit = 50 } = options || {}

  return useQuery<NotificationListResponse>({
    queryKey: ['notifications', 'list', { isRead, skip, limit }],
    queryFn: async () => {
      const response = await notificationsApi.list({
        is_read: isRead,
        skip,
        limit,
      })
      return response.data
    },
    staleTime: 30 * 1000,
  })
}

/**
 * Fetch recent unread notifications (for dropdown)
 * @param limit - Number of items to fetch (default 5)
 */
export function useRecentNotifications(limit = 5) {
  return useQuery<NotificationListResponse>({
    queryKey: ['notifications', 'recent', limit],
    queryFn: async () => {
      const response = await notificationsApi.list({
        is_read: false,
        skip: 0,
        limit,
      })
      return response.data
    },
    refetchInterval: 60 * 1000,
    staleTime: 30 * 1000,
  })
}

/**
 * Mark a single notification as read
 */
export function useMarkNotificationRead() {
  const queryClient = useQueryClient()

  return useMutation<NotificationResponse, Error, string>({
    mutationFn: async (notificationId: string) => {
      const response = await notificationsApi.markRead(notificationId)
      return response.data
    },
    onSuccess: () => {
      // Invalidate notification queries to refetch
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}

/**
 * Mark multiple notifications as read
 */
export function useMarkMultipleRead() {
  const queryClient = useQueryClient()

  return useMutation<NotificationMarkReadResponse, Error, string[]>({
    mutationFn: async (notificationIds: string[]) => {
      const response = await notificationsApi.markMultipleRead(notificationIds)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}

/**
 * Mark all notifications as read
 */
export function useMarkAllRead() {
  const queryClient = useQueryClient()

  return useMutation<NotificationMarkReadResponse, Error, void>({
    mutationFn: async () => {
      const response = await notificationsApi.markAllRead()
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}
