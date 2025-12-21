/**
 * Next.js Middleware for server-side authentication
 *
 * Provides defense-in-depth by checking auth at the edge before
 * rendering protected pages. Works alongside client-side ProtectedRoute.
 */
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Public paths that don't require authentication
const publicPaths = ['/login', '/forgot-password', '/reset-password']

// Static assets and API routes to exclude from auth check
const excludedPrefixes = ['/_next', '/api', '/favicon.ico', '/images', '/fonts']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Skip excluded paths (static assets, API routes)
  if (excludedPrefixes.some((prefix) => pathname.startsWith(prefix))) {
    return NextResponse.next()
  }

  // Allow public paths without auth
  if (publicPaths.some((path) => pathname === path || pathname.startsWith(path + '/'))) {
    return NextResponse.next()
  }

  // Check for auth token in cookies
  const token = request.cookies.get('accessToken')?.value

  // Redirect to login if no token
  if (!token) {
    const loginUrl = new URL('/login', request.url)
    // Preserve the intended destination for redirect after login
    if (pathname !== '/') {
      loginUrl.searchParams.set('redirect', pathname)
    }
    return NextResponse.redirect(loginUrl)
  }

  // Token exists - allow request to proceed
  // Note: Token validation happens on the API side
  return NextResponse.next()
}

export const config = {
  // Match all paths except static files
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
