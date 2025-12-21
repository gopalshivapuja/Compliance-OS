/**
 * Workflow Tasks Page
 * Lists tasks assigned to the current user
 */
export default function WorkflowTasksPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Workflow Tasks</h1>
        <p className="mt-1 text-sm text-gray-500">
          Your assigned tasks for compliance workflows
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
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Coming in Phase 7
        </h3>
        <p className="text-gray-500 max-w-md mx-auto">
          This page will display your workflow tasks with status filtering,
          due date sorting, and quick actions for task completion.
        </p>
      </div>
    </div>
  )
}
