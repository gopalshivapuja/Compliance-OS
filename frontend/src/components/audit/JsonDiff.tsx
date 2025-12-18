/**
 * JsonDiff Component
 * Displays old and new JSON values side-by-side with highlighting
 */
'use client'

import { useMemo } from 'react'

interface JsonDiffProps {
  oldValues: Record<string, any> | null
  newValues: Record<string, any> | null
}

export function JsonDiff({ oldValues, newValues }: JsonDiffProps) {
  // Get all unique keys from both objects
  const allKeys = useMemo(() => {
    const keys = new Set<string>()
    if (oldValues) Object.keys(oldValues).forEach((k) => keys.add(k))
    if (newValues) Object.keys(newValues).forEach((k) => keys.add(k))
    return Array.from(keys).sort()
  }, [oldValues, newValues])

  // Check if a value has changed
  const hasChanged = (key: string): boolean => {
    const oldVal = oldValues?.[key]
    const newVal = newValues?.[key]
    return JSON.stringify(oldVal) !== JSON.stringify(newVal)
  }

  // Format value for display
  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return 'null'
    if (typeof value === 'object') return JSON.stringify(value, null, 2)
    if (typeof value === 'string') return `"${value}"`
    return String(value)
  }

  // Handle case where both are null/empty
  if (!oldValues && !newValues) {
    return (
      <div className="text-sm text-gray-500 py-2">
        No change data available
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {allKeys.length === 0 ? (
        <div className="text-sm text-gray-500 py-2">No changes</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/4">
                  Field
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-3/8">
                  Old Value
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-3/8">
                  New Value
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {allKeys.map((key) => {
                const changed = hasChanged(key)
                const oldVal = oldValues?.[key]
                const newVal = newValues?.[key]
                const oldExists = oldValues && key in oldValues
                const newExists = newValues && key in newValues

                return (
                  <tr
                    key={key}
                    className={changed ? 'bg-yellow-50' : ''}
                  >
                    <td className="px-4 py-2 text-sm font-medium text-gray-900">
                      {key}
                      {changed && (
                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                          Changed
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-sm font-mono text-gray-600">
                      {oldExists ? (
                        <pre className="whitespace-pre-wrap break-words">
                          {formatValue(oldVal)}
                        </pre>
                      ) : (
                        <span className="text-gray-400 italic">N/A</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-sm font-mono text-gray-600">
                      {newExists ? (
                        <pre className="whitespace-pre-wrap break-words">
                          {formatValue(newVal)}
                        </pre>
                      ) : (
                        <span className="text-gray-400 italic">N/A</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
