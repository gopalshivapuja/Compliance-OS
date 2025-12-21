/**
 * AuditLogTable Component
 * Displays audit logs with expandable rows showing JSON diff
 */
'use client'

import { useState } from 'react'
import { JsonDiff } from './JsonDiff'
import type { AuditLogResponse, ActionType } from '@/types/audit'

interface AuditLogTableProps {
  logs: AuditLogResponse[]
  isLoading?: boolean
}

// Action type color mapping
const actionTypeColors: Record<ActionType, string> = {
  CREATE: 'bg-green-100 text-green-800',
  UPDATE: 'bg-blue-100 text-blue-800',
  DELETE: 'bg-red-100 text-red-800',
  LOGIN: 'bg-gray-100 text-gray-800',
  LOGOUT: 'bg-gray-100 text-gray-800',
  APPROVE: 'bg-green-100 text-green-800',
  REJECT: 'bg-red-100 text-red-800',
  VIEW: 'bg-gray-100 text-gray-800',
  DOWNLOAD: 'bg-blue-100 text-blue-800',
  UPLOAD: 'bg-purple-100 text-purple-800',
}

export function AuditLogTable({ logs, isLoading }: AuditLogTableProps) {
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null)

  const toggleRow = (logId: string) => {
    setExpandedRowId(expandedRowId === logId ? null : logId)
  }

  // Format date for display
  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString)
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    } catch {
      return dateString
    }
  }

  // Get action type badge color
  const getActionTypeColor = (actionType: ActionType): string => {
    return actionTypeColors[actionType] || 'bg-gray-100 text-gray-800'
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary-600 border-r-transparent"></div>
        <p className="mt-2 text-sm text-gray-500">Loading audit logs...</p>
      </div>
    )
  }

  // Empty state
  if (logs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No audit logs found matching your filters.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Timestamp
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              User
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Action
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Resource
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Change Summary
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Details
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {logs.map((log) => {
            const isExpanded = expandedRowId === log.audit_log_id
            const hasChanges = log.old_values || log.new_values

            return (
              <>
                <tr
                  key={log.audit_log_id}
                  className="hover:bg-gray-50 transition-colors"
                >
                  <td className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap">
                    {formatDate(log.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm font-medium text-gray-900">
                      {log.user_name || 'Unknown'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {log.user_email}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionTypeColor(
                        log.action_type as ActionType
                      )}`}
                    >
                      {log.action_type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">
                      {log.resource_type}
                    </div>
                    <div className="text-xs text-gray-500 truncate max-w-xs">
                      {log.resource_id}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {log.change_summary}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {hasChanges ? (
                      <button
                        onClick={() => toggleRow(log.audit_log_id)}
                        className="text-primary-600 hover:text-primary-700 font-medium"
                      >
                        {isExpanded ? 'Hide' : 'Show'} Changes
                      </button>
                    ) : (
                      <span className="text-gray-400">No changes</span>
                    )}
                  </td>
                </tr>
                {isExpanded && hasChanges && (
                  <tr key={`${log.audit_log_id}-expanded`}>
                    <td colSpan={6} className="px-4 py-4 bg-gray-50">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-semibold text-gray-900">
                            Change Details
                          </h4>
                          {log.ip_address && (
                            <div className="text-xs text-gray-500">
                              IP: {log.ip_address}
                            </div>
                          )}
                        </div>
                        <JsonDiff
                          oldValues={log.old_values}
                          newValues={log.new_values}
                        />
                        {log.user_agent && (
                          <div className="text-xs text-gray-500 pt-2 border-t border-gray-200">
                            <span className="font-medium">User Agent:</span>{' '}
                            {log.user_agent}
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
