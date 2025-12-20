"""
FastAPI dependencies for authentication and authorization
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.core.database import get_db
from app.core.redis import get_redis
from sqlalchemy.orm import Session
import redis

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency to get current authenticated user from JWT token.

    Returns:
        Dictionary with user_id, tenant_id, roles, etc.

    Raises:
        HTTPException: If token is invalid or missing
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def get_current_tenant_id(current_user: dict = Depends(get_current_user)) -> str:
    """
    Dependency to extract tenant_id from current user.

    Returns:
        Tenant ID as string
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID not found in token",
        )
    return tenant_id


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.

    Usage:
        @app.get("/admin")
        async def admin_route(user: dict = Depends(require_role("admin"))):
            ...
    """

    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_roles = current_user.get("roles", [])
        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}",
            )
        return current_user

    return role_checker
