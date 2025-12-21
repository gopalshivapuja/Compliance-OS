/**
 * Compliance Masters Page
 * Lists all compliance master definitions
 */
export default function ComplianceMastersPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Compliance Masters</h1>
        <p className="mt-1 text-sm text-gray-500">
          Master definitions for compliance obligations across GST, Direct Tax, Payroll, MCA, FEMA, and FP&A
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
            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
          />
        </svg>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Coming in Phase 7
        </h3>
        <p className="text-gray-500 max-w-md mx-auto">
          This page will display all compliance master templates with category filtering,
          search, and the ability to create/edit master definitions.
        </p>
      </div>
    </div>
  )
}
