/**
 * Custom React Hooks - Barrel Export
 *
 * Re-exports all custom hooks from specialized modules.
 */

// Dashboard hooks
export {
  useDashboardOverview,
  useOverdueItems,
  useUpcomingItems,
  useCategoryBreakdown,
} from './useDashboard'

// Compliance hooks
export { useComplianceInstances, useComplianceInstance } from './useCompliance'

// Audit log hooks
export {
  useAuditLogs,
  useResourceAuditTrail,
  useAuditLog,
} from './useAuditLogs'

// Notification hooks
export {
  useNotificationCount,
  useNotifications,
  useRecentNotifications,
  useMarkNotificationRead,
  useMarkMultipleRead,
  useMarkAllRead,
} from './useNotifications'
