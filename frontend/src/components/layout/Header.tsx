/**
 * Header component for the application
 * TODO: Implement navigation and user menu
 */
export function Header() {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">Compliance OS</h1>
          <nav className="flex items-center gap-4">
            {/* TODO: Add navigation items */}
            <span className="text-sm text-gray-600">Navigation - TODO</span>
          </nav>
        </div>
      </div>
    </header>
  )
}

