/**
 * Compliance Instances Page
 * Displays all compliance instances with filters and pagination
 */
'use client'

import { useState } from 'react'
import { useComplianceInstances } from '@/lib/hooks'
import { RAGBadge } from '@/components/ui/RAGBadge'
import { Spinner } from '@/components/ui/Spinner'
import type { RAGStatus } from '@/types'

export default function CompliancePage() {
  // Filter state
  const [filters, setFilters] = useState({
    entity_id: '',
    status: '',
    category: '',
    rag_status: '',
    owner_id: '',
  })

  // Pagination state
  const [skip, setSkip] = useState(0)
  const limit = 50

  // Fetch compliance instances
  const { data, isLoading, error } = useComplianceInstances(
    filters.entity_id || undefined,
    filters.status || undefined,
    filters.category || undefined,
    filters.rag_status || undefined,
    filters.owner_id || undefined,
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
          <h1 className="text-3xl font-bold text-gray-900">Compliance Instances</h1>
          <p className="mt-2 text-sm text-gray-600">
            Loading compliance data...
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-8 flex items-center justify-center">
          <div className="text-center">
            <Spinner size="lg" />
            <p className="mt-4 text-sm text-gray-500">Loading compliance instances...</p>
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
          <h1 className="text-3xl font-bold text-gray-900">Compliance Instances</h1>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-800 mb-2">
            Error Loading Compliance Instances
          </h3>
          <p className="text-sm text-red-600">
            {error instanceof Error
              ? error.message
              : 'Failed to load compliance data. Please try again.'}
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

  const instances = data?.items || []
  const total = data?.total || 0
  const currentPage = Math.floor(skip / limit) + 1
  const totalPages = Math.ceil(total / limit)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Compliance Instances</h1>
        <p className="mt-2 text-sm text-gray-600">
          View and manage all compliance obligations across entities
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {/* Status Filter */}
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              id="status"
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Statuses</option>
              <option value="Not Started">Not Started</option>
              <option value="In Progress">In Progress</option>
              <option value="Pending Review">Pending Review</option>
              <option value="Pending Approval">Pending Approval</option>
              <option value="Filed">Filed</option>
              <option value="Completed">Completed</option>
              <option value="Rejected">Rejected</option>
              <option value="Overdue">Overdue</option>
            </select>
          </div>

          {/* Category Filter */}
          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              id="category"
              value={filters.category}
              onChange={(e) => handleFilterChange('category', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Categories</option>
              <option value="GST">GST</option>
              <option value="Direct Tax">Direct Tax</option>
              <option value="Payroll">Payroll</option>
              <option value="MCA">MCA</option>
              <option value="FEMA">FEMA</option>
              <option value="FP&A">FP&A</option>
            </select>
          </div>

          {/* RAG Status Filter */}
          <div>
            <label htmlFor="rag_status" className="block text-sm font-medium text-gray-700 mb-1">
              RAG Status
            </label>
            <select
              id="rag_status"
              value={filters.rag_status}
              onChange={(e) => handleFilterChange('rag_status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All</option>
              <option value="Green">Green</option>
              <option value="Amber">Amber</option>
              <option value="Red">Red</option>
            </select>
          </div>

          {/* Clear Filters Button */}
          <div className="flex items-end">
            <button
              onClick={() => {
                setFilters({
                  entity_id: '',
                  status: '',
                  category: '',
                  rag_status: '',
                  owner_id: '',
                })
                setSkip(0)
              }}
              className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Clear Filters
            </button>
          </div>

          {/* Results Count */}
          <div className="flex items-end">
            <div className="text-sm text-gray-600">
              Showing <span className="font-semibold">{instances.length}</span> of{' '}
              <span className="font-semibold">{total}</span> results
            </div>
          </div>
        </div>
      </div>

      {/* Compliance Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {instances.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No compliance instances found matching your filters.
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Compliance
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Entity
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Period
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Due Date
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      RAG
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Owner
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {instances.map((instance) => (
                    <tr
                      key={instance.compliance_instance_id}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-gray-900">
                          {instance.compliance_name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {instance.compliance_code}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-900">
                          {instance.entity_name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {instance.entity_code}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {instance.category}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {new Date(instance.period_start).toLocaleDateString()} -{' '}
                        {new Date(instance.period_end).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {new Date(instance.due_date).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {instance.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <RAGBadge status={instance.rag_status as RAGStatus} />
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {instance.owner_name || (
                          <span className="text-gray-400">Unassigned</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
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
            )}
          </>
        )}
      </div>
    </div>
  )
}
