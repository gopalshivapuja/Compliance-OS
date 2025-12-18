/**
 * RAG Status Card - displays Red/Amber/Green compliance distribution
 */
import type { RAGCounts } from '@/types/dashboard'

interface RAGStatusCardProps {
  ragCounts: RAGCounts
  total: number
}

export function RAGStatusCard({ ragCounts, total }: RAGStatusCardProps) {
  const { green, amber, red } = ragCounts

  // Calculate percentages
  const greenPct = total > 0 ? Math.round((green / total) * 100) : 0
  const amberPct = total > 0 ? Math.round((amber / total) * 100) : 0
  const redPct = total > 0 ? Math.round((red / total) * 100) : 0

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Compliance Status Overview
      </h2>

      {/* Total Count */}
      <div className="mb-6">
        <div className="text-3xl font-bold text-gray-900">{total}</div>
        <div className="text-sm text-gray-600">Total Compliance Items</div>
      </div>

      {/* RAG Distribution Bars */}
      <div className="space-y-4">
        {/* Green */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-sm font-medium text-gray-700">On Track</span>
            </div>
            <div className="text-sm">
              <span className="font-semibold text-gray-900">{green}</span>
              <span className="text-gray-500 ml-1">({greenPct}%)</span>
            </div>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 transition-all duration-500"
              style={{ width: `${greenPct}%` }}
            />
          </div>
        </div>

        {/* Amber */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
              <span className="text-sm font-medium text-gray-700">At Risk</span>
            </div>
            <div className="text-sm">
              <span className="font-semibold text-gray-900">{amber}</span>
              <span className="text-gray-500 ml-1">({amberPct}%)</span>
            </div>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-yellow-500 transition-all duration-500"
              style={{ width: `${amberPct}%` }}
            />
          </div>
        </div>

        {/* Red */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-sm font-medium text-gray-700">Overdue</span>
            </div>
            <div className="text-sm">
              <span className="font-semibold text-gray-900">{red}</span>
              <span className="text-gray-500 ml-1">({redPct}%)</span>
            </div>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-red-500 transition-all duration-500"
              style={{ width: `${redPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-6 border-t grid grid-cols-2 gap-4">
        <div>
          <div className="text-2xl font-bold text-red-600">{red}</div>
          <div className="text-xs text-gray-600">Need Immediate Action</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-yellow-600">{amber}</div>
          <div className="text-xs text-gray-600">Require Attention</div>
        </div>
      </div>
    </div>
  )
}
