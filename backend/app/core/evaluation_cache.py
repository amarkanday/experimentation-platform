"""
Evaluation result caching for rule evaluation.

This module provides LRU caching of rule evaluation results with TTL support.
"""

import hashlib
import json
import time
import threading
import logging
from typing import Dict, Any, Optional
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with TTL and metadata."""
    result: bool
    created_at: float
    expires_at: float
    rule_id: str
    user_id: Optional[str] = None


class CacheKey:
    """Cache key for rule evaluation."""

    def __init__(self, rule_id: str, user_context: Dict[str, Any]):
        self.rule_id = rule_id
        self.user_context = user_context
        self._hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute deterministic hash of rule and context."""
        # Sort context keys for deterministic hashing
        context_str = json.dumps(self.user_context, sort_keys=True)
        key_str = f"{self.rule_id}:{context_str}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def __str__(self) -> str:
        return self._hash

    def __hash__(self) -> int:
        return hash(self._hash)

    def __eq__(self, other) -> bool:
        if not isinstance(other, CacheKey):
            return False
        return self._hash == other._hash


class EvaluationCache:
    """
    LRU cache for rule evaluation results.

    Provides:
    - TTL-based expiration
    - LRU eviction when size limit reached
    - Thread-safe operations
    - Cache invalidation by rule or user
    - Statistics tracking
    """

    def __init__(
        self,
        max_size: int = 10000,
        default_ttl: float = 300.0  # 5 minutes default
    ):
        """
        Initialize evaluation cache.

        Args:
            max_size: Maximum number of entries to cache
            default_ttl: Default TTL in seconds for cache entries
        """
        self.max_size = max_size
        self.default_ttl = default_ttl

        # Thread-safe LRU cache
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    @property
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)

    def generate_key(self, rule_id: str, user_context: Dict[str, Any]) -> str:
        """
        Generate cache key for rule and user context.

        Args:
            rule_id: Rule identifier
            user_context: User context dictionary

        Returns:
            Cache key string
        """
        cache_key = CacheKey(rule_id, user_context)
        return str(cache_key)

    def get(self, rule_id: str, user_context: Dict[str, Any]) -> Optional[bool]:
        """
        Get cached evaluation result.

        Args:
            rule_id: Rule identifier
            user_context: User context dictionary

        Returns:
            Cached result or None if not found/expired
        """
        key = self.generate_key(rule_id, user_context)

        with self._lock:
            if key in self._cache:
                entry = self._cache[key]

                # Check if expired
                if time.time() > entry.expires_at:
                    # Remove expired entry
                    del self._cache[key]
                    self._misses += 1
                    return None

                # Mark as recently used
                self._cache.move_to_end(key)
                self._hits += 1
                return entry.result
            else:
                self._misses += 1
                return None

    def set(
        self,
        rule_id: str,
        user_context: Dict[str, Any],
        result: bool,
        ttl: Optional[float] = None
    ):
        """
        Store evaluation result in cache.

        Args:
            rule_id: Rule identifier
            user_context: User context dictionary
            result: Evaluation result to cache
            ttl: Optional custom TTL (defaults to default_ttl)
        """
        key = self.generate_key(rule_id, user_context)
        ttl = ttl if ttl is not None else self.default_ttl

        current_time = time.time()
        user_id = user_context.get("user_id")

        entry = CacheEntry(
            result=result,
            created_at=current_time,
            expires_at=current_time + ttl,
            rule_id=rule_id,
            user_id=user_id
        )

        with self._lock:
            # Add/update entry
            if key in self._cache:
                # Update existing entry
                del self._cache[key]

            self._cache[key] = entry
            self._cache.move_to_end(key)

            # Evict oldest if over size limit
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
                self._evictions += 1

    def invalidate_rule(self, rule_id: str):
        """
        Invalidate all cache entries for a specific rule.

        Args:
            rule_id: Rule identifier
        """
        with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.rule_id == rule_id
            ]

            for key in keys_to_remove:
                del self._cache[key]

            logger.info(f"Invalidated {len(keys_to_remove)} cache entries for rule {rule_id}")

    def invalidate_user(self, user_id: str):
        """
        Invalidate all cache entries for a specific user.

        Args:
            user_id: User identifier
        """
        with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.user_id == user_id
            ]

            for key in keys_to_remove:
                del self._cache[key]

            logger.info(f"Invalidated {len(keys_to_remove)} cache entries for user {user_id}")

    def clear(self):
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            # Reset statistics
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "total_requests": total_requests
            }

    def cleanup_expired(self):
        """Remove all expired entries from cache."""
        current_time = time.time()

        with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if current_time > entry.expires_at
            ]

            for key in keys_to_remove:
                del self._cache[key]

            if keys_to_remove:
                logger.debug(f"Cleaned up {len(keys_to_remove)} expired cache entries")

            return len(keys_to_remove)
