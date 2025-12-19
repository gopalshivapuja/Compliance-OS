"""
Middleware package for Compliance OS
"""

from .security_headers import security_headers_middleware

__all__ = ["security_headers_middleware"]
