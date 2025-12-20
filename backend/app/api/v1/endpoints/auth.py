"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.core.redis import (
    store_refresh_token,
    validate_refresh_token,
    invalidate_refresh_token,
)
from app.schemas import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    LogoutRequest,
)
from app.models import User
from app.services import log_action

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request."""
    return request.headers.get("User-Agent", "unknown")


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    User login endpoint.

    Validates credentials, generates JWT access token and refresh token,
    logs the login action, and returns tokens with user information.

    Args:
        login_data: Login credentials (email, password)
        request: FastAPI request object (for IP and user agent)
        db: Database session

    Returns:
        TokenResponse: Access token, refresh token, and user information

    Raises:
        HTTPException 401: Invalid credentials
        HTTPException 403: User account inactive
    """
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if user is active
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status}. Please contact administrator.",
        )

    # Get user roles
    role_codes = [role.role_code for role in user.roles]

    # Create JWT access token (30min TTL)
    access_token_data = {
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "roles": role_codes,
    }
    access_token = create_access_token(data=access_token_data)

    # Generate and store refresh token (7-day TTL)
    refresh_token = await store_refresh_token(user_id=str(user.id))

    # Update last login timestamp
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Log LOGIN action to audit trail
    await log_action(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.id),
        action_type="LOGIN",
        resource_type="user",
        resource_id=str(user.id),
        change_summary=f"User {user.email} logged in",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    # Build user response
    user_response = UserResponse(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        roles=role_codes,
        is_system_admin=user.is_system_admin,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_response,
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Validates the refresh token, generates a new access token,
    rotates the refresh token for security.

    Args:
        refresh_data: Refresh token request
        db: Database session

    Returns:
        TokenResponse: New access token, new refresh token, and user information

    Raises:
        HTTPException 401: Invalid or expired refresh token
    """
    # Validate refresh token
    user_id = await validate_refresh_token(refresh_data.refresh_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Check if user is still active
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status}. Please contact administrator.",
        )

    # Get user roles
    role_codes = [role.role_code for role in user.roles]

    # Create new JWT access token
    access_token_data = {
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "roles": role_codes,
    }
    access_token = create_access_token(data=access_token_data)

    # Rotate refresh token (invalidate old, create new)
    await invalidate_refresh_token(refresh_data.refresh_token)
    new_refresh_token = await store_refresh_token(user_id=str(user.id))

    # Build user response
    user_response = UserResponse(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        roles=role_codes,
        is_system_admin=user.is_system_admin,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=user_response,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    logout_data: Optional[LogoutRequest] = None,
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """
    User logout endpoint.

    Invalidates the refresh token in Redis and logs the logout action.

    Args:
        logout_data: Optional logout request with refresh token
        current_user: Current authenticated user from JWT
        request: FastAPI request object (for IP and user agent)
        db: Database session

    Returns:
        dict: Success message
    """
    # Invalidate refresh token if provided
    if logout_data and logout_data.refresh_token:
        await invalidate_refresh_token(logout_data.refresh_token)

    # Log LOGOUT action to audit trail
    await log_action(
        db=db,
        tenant_id=current_user.get("tenant_id"),
        user_id=current_user.get("user_id"),
        action_type="LOGOUT",
        resource_type="user",
        resource_id=current_user.get("user_id"),
        change_summary=f"User {current_user.get('email')} logged out",
        ip_address=get_client_ip(request) if request else None,
        user_agent=get_user_agent(request) if request else None,
    )

    return {"message": "Logout successful"}


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user from JWT
        db: Database session

    Returns:
        UserResponse: Complete user information with roles

    Raises:
        HTTPException 404: User not found
    """
    # Get fresh user data from database
    user = db.query(User).filter(User.id == current_user.get("user_id")).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get user roles
    role_codes = [role.role_code for role in user.roles]

    return UserResponse(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        roles=role_codes,
        is_system_admin=user.is_system_admin,
    )
