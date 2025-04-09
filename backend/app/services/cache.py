"""
Cache service for the experimentation platform.

This module provides caching functionality using Redis.
"""

import logging
from typing import Any, Dict, Optional, Union
from redis import Redis

logger = logging.getLogger(__name__)


class CacheService:
    """Service for handling caching operations."""

    def __init__(self, redis_client: Optional[Redis] = None):
        """Initialize the cache service with an optional Redis client."""
        self.redis = redis_client
        self.enabled = bool(redis_client)

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        if not self.enabled:
            return None

        try:
            value = self.redis.get(key)
            return value.decode() if value else None
        except Exception as e:
            logger.error(f"Error getting value from cache: {e}")
            return None

    def set(
        self,
        key: str,
        value: Union[str, bytes, int, float],
        expire: Optional[int] = None,
    ) -> bool:
        """Set a value in the cache with optional expiration."""
        if not self.enabled:
            return False

        try:
            return bool(self.redis.set(key, value, ex=expire))
        except Exception as e:
            logger.error(f"Error setting value in cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        if not self.enabled:
            return False

        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Error deleting value from cache: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        if not self.enabled:
            return False

        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking key existence in cache: {e}")
            return False

    def clear(self, pattern: str = "*") -> bool:
        """Clear all keys matching the pattern from the cache."""
        if not self.enabled:
            return False

        try:
            keys = self.redis.keys(pattern)
            if keys:
                return bool(self.redis.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
