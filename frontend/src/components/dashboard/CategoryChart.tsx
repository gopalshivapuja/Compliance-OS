/**
 * Category Chart - horizontal stacked bar chart showing RAG distribution by category
 */
import type { CategoryBreakdown } from '@/types/dashboard'

interface CategoryChartProps {
  breakdown: CategoryBreakdown[]
}

export function CategoryChart({ breakdown }: CategoryChartProps) {
  if (breakdown.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Category Breakdown
        </h3>
        <div className="text-center py-8 text-gray-500">
          No data available
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        Category Breakdown
      </h3>

      <div className="space-y-6">
        {breakdown.map((item) => {
          const greenPct = (item.green / item.total) * 100
          const amberPct = (item.amber / item.total) * 100
          const redPct = (item.red / item.total) * 100

          return (
            <div key={item.category}>
              {/* Category Name and Total */}
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  {item.category}
                </span>
                <span className="text-sm text-gray-500">
                  {item.total} items
                </span>
              </div>

              {/* Stacked Bar */}
              <div className="h-8 flex rounded-md overflow-hidden bg-gray-100">
                {/* Green segment */}
                {item.green > 0 && (
                  <div
                    className="bg-green-500 flex items-center justify-center transition-all duration-500"
                    style={{ width: `${greenPct}%` }}
                    title={`${item.green} Green (${Math.round(greenPct)}%)`}
                  >
                    {greenPct > 15 && (
                      <span className="text-xs font-medium text-white">
                        {item.green}
                      </span>
                    )}
                  </div>
                )}

                {/* Amber segment */}
                {item.amber > 0 && (
                  <div
                    className="bg-yellow-500 flex items-center justify-center transition-all duration-500"
                    style={{ width: `${amberPct}%` }}
                    title={`${item.amber} Amber (${Math.round(amberPct)}%)`}
                  >
                    {amberPct > 15 && (
                      <span className="text-xs font-medium text-white">
                        {item.amber}
                      </span>
                    )}
                  </div>
                )}

                {/* Red segment */}
                {item.red > 0 && (
                  <div
                    className="bg-red-500 flex items-center justify-center transition-all duration-500"
                    style={{ width: `${redPct}%` }}
                    title={`${item.red} Red (${Math.round(redPct)}%)`}
                  >
                    {redPct > 15 && (
                      <span className="text-xs font-medium text-white">
                        {item.red}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Detailed Counts */}
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  <span>{item.green} On Track</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                  <span>{item.amber} At Risk</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-red-500"></div>
                  <span>{item.red} Overdue</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="mt-6 pt-6 border-t flex items-center justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-500"></div>
          <span className="text-gray-600">On Track</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-yellow-500"></div>
          <span className="text-gray-600">At Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-500"></div>
          <span className="text-gray-600">Overdue</span>
        </div>
      </div>
    </div>
  )
}
