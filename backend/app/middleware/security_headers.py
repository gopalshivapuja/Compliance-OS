"""
Security headers middleware for enhanced application security
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses

    Security headers protect against:
    - XSS (Cross-Site Scripting) attacks
    - Clickjacking
    - MIME-type sniffing
    - Man-in-the-middle attacks
    - Content injection
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and add security headers to response

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response with security headers
        """
        # Process request
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), " "microphone=(), " "camera=(), " "payment=()"

        return response


# Helper function to add middleware to app
def security_headers_middleware(app):
    """
    Add security headers middleware to FastAPI app

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(SecurityHeadersMiddleware)
