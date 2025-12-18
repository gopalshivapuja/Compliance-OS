/**
 * Compliance Table - displays list of compliance items with RAG status
 */
import { RAGBadge } from '@/components/ui/RAGBadge'
import type { ComplianceInstanceSummary } from '@/types/dashboard'

interface ComplianceTableProps {
  items: ComplianceInstanceSummary[]
  loading?: boolean
  emptyMessage?: string
  showDaysOverdue?: boolean
}

export function ComplianceTable({
  items,
  loading = false,
  emptyMessage = 'No compliance items',
  showDaysOverdue = false,
}: ComplianceTableProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-sm text-gray-500">Loading...</p>
        </div>
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="p-8 text-center text-gray-500">{emptyMessage}</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
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
                Due Date
              </th>
              {showDaysOverdue && (
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Days Overdue
                </th>
              )}
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Owner
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {items.map((item) => {
              const dueDate = new Date(item.due_date)
              const isOverdue = item.days_overdue && item.days_overdue > 0

              return (
                <tr
                  key={item.compliance_instance_id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="text-sm font-medium text-gray-900">
                      {item.compliance_name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {item.compliance_code}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">{item.entity_name}</div>
                    <div className="text-xs text-gray-500">{item.entity_code}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">{item.category}</div>
                    {item.sub_category && (
                      <div className="text-xs text-gray-500">{item.sub_category}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div
                      className={`text-sm ${
                        isOverdue ? 'text-red-600 font-semibold' : 'text-gray-900'
                      }`}
                    >
                      {dueDate.toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </div>
                    <div className="text-xs text-gray-500 capitalize">
                      {item.frequency}
                    </div>
                  </td>
                  {showDaysOverdue && (
                    <td className="px-4 py-3">
                      {item.days_overdue && item.days_overdue > 0 ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          {item.days_overdue} days
                        </span>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>
                  )}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <RAGBadge status={item.rag_status} />
                      <span className="text-xs text-gray-600">{item.status}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">
                      {item.owner_name || (
                        <span className="text-gray-400">Unassigned</span>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
