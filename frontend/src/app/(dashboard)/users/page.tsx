/**
 * Users Management Page
 * Admin-only page for managing tenant users
 */
export default function UsersPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage users and their role assignments
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
            d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Coming in Phase 7
        </h3>
        <p className="text-gray-500 max-w-md mx-auto">
          This page will allow administrators to create, edit, and deactivate users,
          assign roles, and manage entity access permissions.
        </p>
      </div>
    </div>
  )
}
