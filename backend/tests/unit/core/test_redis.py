"""
Unit tests for Redis refresh token management.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

from app.core.redis import (
    store_refresh_token,
    validate_refresh_token,
    invalidate_refresh_token,
    invalidate_user_refresh_tokens,
)


@pytest.mark.asyncio
async def test_store_refresh_token_generates_token():
    """Test that store_refresh_token generates a token if not provided."""
    with patch("app.core.redis.redis_client") as mock_redis:
        user_id = str(uuid4())

        token = await store_refresh_token(user_id=user_id)

        assert token is not None
        assert isinstance(token, str)
        # Verify setex was called twice (for token and user_key)
        assert mock_redis.setex.call_count == 2


@pytest.mark.asyncio
async def test_store_refresh_token_with_custom_token():
    """Test storing a custom refresh token."""
    with patch("app.core.redis.redis_client") as mock_redis:
        user_id = str(uuid4())
        custom_token = "custom-token-123"

        token = await store_refresh_token(user_id=user_id, token=custom_token)

        assert token == custom_token
        # Verify correct keys were set
        mock_redis.setex.assert_any_call(f"refresh_token:{custom_token}", 604800, user_id)
        mock_redis.setex.assert_any_call(f"user_refresh:{user_id}", 604800, custom_token)


@pytest.mark.asyncio
async def test_store_refresh_token_with_custom_ttl():
    """Test storing refresh token with custom TTL."""
    with patch("app.core.redis.redis_client") as mock_redis:
        user_id = str(uuid4())
        custom_ttl = 3600  # 1 hour

        token = await store_refresh_token(user_id=user_id, ttl=custom_ttl)

        # Verify TTL was used
        calls = mock_redis.setex.call_args_list
        for call in calls:
            assert call[0][1] == custom_ttl  # TTL is second argument


@pytest.mark.asyncio
async def test_validate_refresh_token_valid():
    """Test validating a valid refresh token."""
    with patch("app.core.redis.redis_client") as mock_redis:
        token = "valid-token-123"
        user_id = str(uuid4())

        mock_redis.get.return_value = user_id

        result = await validate_refresh_token(token=token)

        assert result == user_id
        mock_redis.get.assert_called_once_with(f"refresh_token:{token}")


@pytest.mark.asyncio
async def test_validate_refresh_token_invalid():
    """Test validating an invalid refresh token."""
    with patch("app.core.redis.redis_client") as mock_redis:
        token = "invalid-token-123"

        mock_redis.get.return_value = None

        result = await validate_refresh_token(token=token)

        assert result is None


@pytest.mark.asyncio
async def test_invalidate_refresh_token_success():
    """Test invalidating a valid refresh token."""
    with patch("app.core.redis.redis_client") as mock_redis:
        token = "token-to-invalidate"
        user_id = str(uuid4())

        # Mock get to return user_id first
        mock_redis.get.return_value = user_id
        # Mock delete to return 1 (success)
        mock_redis.delete.return_value = 1

        result = await invalidate_refresh_token(token=token)

        assert result is True
        # Verify both token and user_key were deleted
        assert mock_redis.delete.call_count == 2
        mock_redis.delete.assert_any_call(f"refresh_token:{token}")
        mock_redis.delete.assert_any_call(f"user_refresh:{user_id}")


@pytest.mark.asyncio
async def test_invalidate_refresh_token_not_found():
    """Test invalidating a non-existent refresh token."""
    with patch("app.core.redis.redis_client") as mock_redis:
        token = "non-existent-token"

        # Mock get to return None (token not found)
        mock_redis.get.return_value = None
        # Mock delete to return 0 (not found)
        mock_redis.delete.return_value = 0

        result = await invalidate_refresh_token(token=token)

        assert result is False


@pytest.mark.asyncio
async def test_invalidate_user_refresh_tokens_success():
    """Test invalidating all refresh tokens for a user."""
    with patch("app.core.redis.redis_client") as mock_redis:
        user_id = str(uuid4())
        token = "user-token-123"

        # Mock get to return the token
        mock_redis.get.return_value = token

        result = await invalidate_user_refresh_tokens(user_id=user_id)

        assert result is True
        # Verify both keys were deleted
        assert mock_redis.delete.call_count == 2
        mock_redis.delete.assert_any_call(f"refresh_token:{token}")
        mock_redis.delete.assert_any_call(f"user_refresh:{user_id}")


@pytest.mark.asyncio
async def test_invalidate_user_refresh_tokens_no_tokens():
    """Test invalidating tokens for user with no active tokens."""
    with patch("app.core.redis.redis_client") as mock_redis:
        user_id = str(uuid4())

        # Mock get to return None (no token found)
        mock_redis.get.return_value = None

        result = await invalidate_user_refresh_tokens(user_id=user_id)

        assert result is False
        # Verify delete was not called
        mock_redis.delete.assert_not_called()
