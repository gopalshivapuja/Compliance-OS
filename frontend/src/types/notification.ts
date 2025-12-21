/**
 * TypeScript types for Notification data structures
 * Matches backend Pydantic schemas in backend/app/schemas/notification.py
 */

export interface NotificationResponse {
  id: string
  user_id: string
  tenant_id: string
  notification_type: NotificationType
  title: string
  message: string
  link: string | null
  is_read: boolean
  read_at: string | null // ISO datetime string
  created_at: string // ISO datetime string
}

export interface NotificationListResponse {
  items: NotificationResponse[]
  total: number
  unread_count: number
  skip: number
  limit: number
}

export interface NotificationCountResponse {
  unread_count: number
}

export interface NotificationMarkReadResponse {
  marked_count: number
}

// Notification types
export type NotificationType =
  | 'task_assigned'
  | 'reminder_t3'
  | 'reminder_due'
  | 'overdue'
  | 'approval_required'
  | 'evidence_approved'
  | 'evidence_rejected'
  | 'system'

// Notification type styling config
export const notificationTypeConfig: Record<
  NotificationType,
  { icon: string; color: string; bgColor: string }
> = {
  task_assigned: {
    icon: 'UserPlus',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  reminder_t3: {
    icon: 'Clock',
    color: 'text-amber-600',
    bgColor: 'bg-amber-100',
  },
  reminder_due: {
    icon: 'AlertTriangle',
    color: 'text-amber-600',
    bgColor: 'bg-amber-100',
  },
  overdue: {
    icon: 'XCircle',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
  },
  approval_required: {
    icon: 'CheckSquare',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
  },
  evidence_approved: {
    icon: 'CheckCircle',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  evidence_rejected: {
    icon: 'XCircle',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
  },
  system: {
    icon: 'Info',
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
  },
}
