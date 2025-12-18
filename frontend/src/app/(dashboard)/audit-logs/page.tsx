/**
 * Audit Logs Page
 * Displays all audit logs with filters and pagination (CFO/System Admin only)
 */
'use client'

import { useState } from 'react'
import { useAuditLogs } from '@/lib/hooks'
import { AuditLogTable } from '@/components/audit/AuditLogTable'
import { Spinner } from '@/components/ui/Spinner'
import type { ResourceType, ActionType } from '@/types/audit'

export default function AuditLogsPage() {
  // Filter state
  const [filters, setFilters] = useState({
    resource_type: '',
    resource_id: '',
    user_id: '',
    action_type: '',
  })

  // Pagination state
  const [skip, setSkip] = useState(0)
  const limit = 50

  // Fetch audit logs
  const { data, isLoading, error } = useAuditLogs(
    filters.resource_type as ResourceType | undefined,
    filters.resource_id || undefined,
    filters.user_id || undefined,
    filters.action_type as ActionType | undefined,
    skip,
    limit
  )

  // Handle filter changes
  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setSkip(0) // Reset to first page when filters change
  }

  // Handle pagination
  const handlePrevPage = () => {
    setSkip((prev) => Math.max(0, prev - limit))
  }

  const handleNextPage = () => {
    if (data && skip + limit < data.total) {
      setSkip((prev) => prev + limit)
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
          <p className="mt-2 text-sm text-gray-600">
            Loading audit trail data...
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-8 flex items-center justify-center">
          <div className="text-center">
            <Spinner size="lg" />
            <p className="mt-4 text-sm text-gray-500">Loading audit logs...</p>
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-800 mb-2">
            Error Loading Audit Logs
          </h3>
          <p className="text-sm text-red-600">
            {error instanceof Error
              ? error.message
              : 'Failed to load audit logs. Please try again or contact support if the issue persists.'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const logs = data?.items || []
  const total = data?.total || 0
  const currentPage = Math.floor(skip / limit) + 1
  const totalPages = Math.ceil(total / limit)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
        <p className="mt-2 text-sm text-gray-600">
          Complete audit trail of all system actions and changes
        </p>
        <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-sm text-blue-800">
            <span className="font-semibold">Note:</span> This page is accessible
            only to CFO and System Admin roles. All actions are logged for
            compliance and security purposes.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {/* Resource Type Filter */}
          <div>
            <label
              htmlFor="resource_type"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Resource Type
            </label>
            <select
              id="resource_type"
              value={filters.resource_type}
              onChange={(e) => handleFilterChange('resource_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Resources</option>
              <option value="user">User</option>
              <option value="compliance_instance">Compliance Instance</option>
              <option value="compliance_master">Compliance Master</option>
              <option value="entity">Entity</option>
              <option value="evidence">Evidence</option>
              <option value="workflow_task">Workflow Task</option>
              <option value="tenant">Tenant</option>
              <option value="notification">Notification</option>
            </select>
          </div>

          {/* Action Type Filter */}
          <div>
            <label
              htmlFor="action_type"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Action Type
            </label>
            <select
              id="action_type"
              value={filters.action_type}
              onChange={(e) => handleFilterChange('action_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Actions</option>
              <option value="CREATE">Create</option>
              <option value="UPDATE">Update</option>
              <option value="DELETE">Delete</option>
              <option value="LOGIN">Login</option>
              <option value="LOGOUT">Logout</option>
              <option value="APPROVE">Approve</option>
              <option value="REJECT">Reject</option>
            </select>
          </div>

          {/* User Filter */}
          <div>
            <label
              htmlFor="user_id"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              User ID
            </label>
            <input
              type="text"
              id="user_id"
              value={filters.user_id}
              onChange={(e) => handleFilterChange('user_id', e.target.value)}
              placeholder="Filter by user ID"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Resource ID Filter */}
          <div>
            <label
              htmlFor="resource_id"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Resource ID
            </label>
            <input
              type="text"
              id="resource_id"
              value={filters.resource_id}
              onChange={(e) => handleFilterChange('resource_id', e.target.value)}
              placeholder="Filter by resource ID"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Clear Filters Button */}
          <div className="flex items-end">
            <button
              onClick={() => {
                setFilters({
                  resource_type: '',
                  resource_id: '',
                  user_id: '',
                  action_type: '',
                })
                setSkip(0)
              }}
              className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Clear Filters
            </button>
          </div>
        </div>

        {/* Results Count */}
        <div className="mt-4 text-sm text-gray-600">
          Showing <span className="font-semibold">{logs.length}</span> of{' '}
          <span className="font-semibold">{total}</span> audit logs
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <AuditLogTable logs={logs} isLoading={isLoading} />
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-white rounded-lg shadow">
          <div className="bg-gray-50 px-4 py-3 flex items-center justify-between border-t border-gray-200">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={handlePrevPage}
                disabled={skip === 0}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={handleNextPage}
                disabled={skip + limit >= total}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing page <span className="font-medium">{currentPage}</span> of{' '}
                  <span className="font-medium">{totalPages}</span>
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={handlePrevPage}
                    disabled={skip === 0}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={handleNextPage}
                    disabled={skip + limit >= total}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </nav>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
