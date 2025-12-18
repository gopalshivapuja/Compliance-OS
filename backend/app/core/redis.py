"""
Redis connection for caching and sessions
"""
import redis
from typing import Optional
from uuid import uuid4
from app.core.config import settings

# Create Redis client
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)


def get_redis():
    """
    Dependency for getting Redis client.
    Use this in FastAPI route dependencies.
    """
    return redis_client


# Refresh token management functions


async def store_refresh_token(user_id: str, token: Optional[str] = None, ttl: int = 604800) -> str:
    """
    Store refresh token in Redis with 7-day TTL.

    Args:
        user_id: User UUID
        token: Optional refresh token (generates if not provided)
        ttl: Time-to-live in seconds (default: 7 days = 604800s)

    Returns:
        str: The refresh token

    Example:
        >>> token = await store_refresh_token(user_id="user-123")
    """
    if token is None:
        token = str(uuid4())

    # Store token with user_id as value
    key = f"refresh_token:{token}"
    redis_client.setex(key, ttl, user_id)

    # Also store user's current token for quick lookup
    user_key = f"user_refresh:{user_id}"
    redis_client.setex(user_key, ttl, token)

    return token


async def validate_refresh_token(token: str) -> Optional[str]:
    """
    Validate refresh token and return user_id if valid.

    Args:
        token: Refresh token to validate

    Returns:
        str | None: User ID if valid, None otherwise

    Example:
        >>> user_id = await validate_refresh_token(token="abc-123")
        >>> if user_id:
        ...     print(f"Valid token for user {user_id}")
    """
    key = f"refresh_token:{token}"
    user_id = redis_client.get(key)
    return user_id


async def invalidate_refresh_token(token: str) -> bool:
    """
    Invalidate (delete) refresh token from Redis.
    Used during logout.

    Args:
        token: Refresh token to invalidate

    Returns:
        bool: True if token was deleted, False if not found

    Example:
        >>> success = await invalidate_refresh_token(token="abc-123")
        >>> if success:
        ...     print("Token invalidated")
    """
    key = f"refresh_token:{token}"

    # Get user_id before deleting to also clean up user_key
    user_id = redis_client.get(key)

    # Delete the token
    deleted = redis_client.delete(key)

    # Also delete user's current token reference
    if user_id:
        user_key = f"user_refresh:{user_id}"
        redis_client.delete(user_key)

    return deleted > 0


async def invalidate_user_refresh_tokens(user_id: str) -> bool:
    """
    Invalidate all refresh tokens for a user.
    Used when forcing logout across all devices.

    Args:
        user_id: User UUID

    Returns:
        bool: True if tokens were deleted

    Example:
        >>> success = await invalidate_user_refresh_tokens(user_id="user-123")
    """
    user_key = f"user_refresh:{user_id}"
    token = redis_client.get(user_key)

    if token:
        token_key = f"refresh_token:{token}"
        redis_client.delete(token_key)
        redis_client.delete(user_key)
        return True

    return False
