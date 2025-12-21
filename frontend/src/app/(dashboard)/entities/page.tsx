/**
 * Entities Management Page
 * Admin-only page for managing legal entities
 */
export default function EntitiesPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Entity Management</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage legal entities and their compliance configurations
        </p>
      </div>

      <div className="bg-white rounded-lg border p-8 text-center">
        <svg
          className="w-12 h-12 mx-auto text-gray-300 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Coming in Phase 7
        </h3>
        <p className="text-gray-500 max-w-md mx-auto">
          This page will allow administrators to create and edit legal entities,
          configure entity-specific compliance requirements, and manage entity access.
        </p>
      </div>
    </div>
  )
}
