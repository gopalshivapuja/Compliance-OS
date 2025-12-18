/**
 * Executive Control Tower Dashboard
 * Displays RAG status, overdue items, upcoming items, and category breakdown
 */
'use client'

import { RAGStatusCard } from '@/components/dashboard/RAGStatusCard'
import { ComplianceTable } from '@/components/dashboard/ComplianceTable'
import { CategoryChart } from '@/components/dashboard/CategoryChart'
import { DashboardSkeleton } from '@/components/dashboard/DashboardSkeleton'
import {
  useDashboardOverview,
  useOverdueItems,
  useUpcomingItems,
} from '@/lib/hooks'

export default function DashboardPage() {
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useDashboardOverview()
  const { data: overdueItems, isLoading: overdueLoading } = useOverdueItems(0, 10)
  const { data: upcomingItems, isLoading: upcomingLoading } = useUpcomingItems(7, 0, 10)

  // Show loading skeleton while initial data is loading
  if (overviewLoading) {
    return <DashboardSkeleton />
  }

  // Show error state
  if (overviewError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-800 mb-2">
          Error Loading Dashboard
        </h3>
        <p className="text-sm text-red-600">
          {overviewError instanceof Error
            ? overviewError.message
            : 'Failed to load dashboard data. Please try again.'}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!overview) {
    return <DashboardSkeleton />
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Executive Control Tower
        </h1>
        <p className="mt-2 text-sm text-gray-600">
          Real-time compliance monitoring and risk assessment
        </p>
      </div>

      {/* RAG Status Card */}
      <RAGStatusCard
        ragCounts={overview.rag_counts}
        total={overview.total_compliances}
      />

      {/* Overdue and Upcoming Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Overdue Items */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Overdue Items
            </h2>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
              {overview.overdue_count}
            </span>
          </div>
          <ComplianceTable
            items={overdueItems || []}
            loading={overdueLoading}
            emptyMessage="No overdue items"
            showDaysOverdue={true}
          />
        </div>

        {/* Upcoming Items (Next 7 Days) */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Upcoming (Next 7 Days)
            </h2>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
              {overview.upcoming_count}
            </span>
          </div>
          <ComplianceTable
            items={upcomingItems || []}
            loading={upcomingLoading}
            emptyMessage="No upcoming items in next 7 days"
          />
        </div>
      </div>

      {/* Category Breakdown */}
      <CategoryChart breakdown={overview.category_breakdown} />
    </div>
  )
}

