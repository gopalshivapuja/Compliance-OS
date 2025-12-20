"""
Rate limiting middleware using slowapi

NOTE: Requires slowapi package in requirements.txt:
    slowapi==0.1.9
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, status
from starlette.responses import JSONResponse


# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Default limit for all endpoints
    storage_uri="memory://",  # In-memory storage (use Redis in production)
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors

    Args:
        request: The request that triggered the limit
        exc: The RateLimitExceeded exception

    Returns:
        JSONResponse with 429 status code
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.retry_after if hasattr(exc, "retry_after") else None,
        },
    )


# Rate limit configurations for different endpoints
RATE_LIMITS = {
    "login": "5/minute",  # 5 login attempts per minute per IP
    "signup": "3/hour",  # 3 signup attempts per hour per IP
    "password_reset": "3/hour",  # 3 password reset requests per hour per IP  # pragma: allowlist secret
    "evidence_upload": "20/hour",  # 20 evidence uploads per hour per user
    "api_general": "100/minute",  # 100 API calls per minute per user
}


def get_rate_limiter():
    """
    Get the limiter instance

    Returns:
        Limiter: The slowapi limiter instance
    """
    return limiter
