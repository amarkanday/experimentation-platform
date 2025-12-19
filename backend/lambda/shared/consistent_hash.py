"""
Consistent hashing implementation for experiment variant assignments.

Uses MurmurHash3 for deterministic, uniform distribution of users to variants.
Ensures that the same user always gets the same variant for an experiment.
"""

import hashlib
import struct
from typing import List, Dict, Optional


class ConsistentHasher:
    """
    Implements consistent hashing for experiment variant assignment.

    Uses MurmurHash3 algorithm to ensure:
    - Deterministic assignments (same user + experiment = same variant)
    - Uniform distribution across variants
    - Respect for traffic allocation percentages
    """

    MURMURHASH_SEED = 0x9747b28c
    MAX_HASH_VALUE = 0xFFFFFFFF  # 2^32 - 1

    def __init__(self):
        """Initialize the consistent hasher."""
        pass

    def assign_variant(
        self,
        user_id: str,
        experiment_key: str,
        variants: List[Dict[str, any]],
        traffic_allocation: float = 1.0,
        salt: Optional[str] = None
    ) -> Optional[str]:
        """
        Assign a user to a variant using consistent hashing.

        Args:
            user_id: Unique identifier for the user
            experiment_key: Unique key for the experiment
            variants: List of variant configurations with 'key' and 'allocation' percentage
            traffic_allocation: Overall traffic allocation for experiment (0.0-1.0)
            salt: Optional salt for hash calculation (default: experiment_key)

        Returns:
            Variant key if user is in experiment, None if excluded by traffic allocation

        Example:
            >>> hasher = ConsistentHasher()
            >>> variants = [
            ...     {"key": "control", "allocation": 0.5},
            ...     {"key": "treatment", "allocation": 0.5}
            ... ]
            >>> variant = hasher.assign_variant("user123", "exp_001", variants, 1.0)
            >>> variant in ["control", "treatment"]
            True
        """
        if not variants:
            raise ValueError("Variants list cannot be empty")

        if not 0.0 <= traffic_allocation <= 1.0:
            raise ValueError("Traffic allocation must be between 0.0 and 1.0")

        # Validate variant allocations sum to ~1.0
        total_allocation = sum(v.get("allocation", 0) for v in variants)
        if not (0.99 <= total_allocation <= 1.01):
            raise ValueError(f"Variant allocations must sum to 1.0, got {total_allocation}")

        # Use experiment_key as salt if none provided
        hash_salt = salt or experiment_key

        # Calculate hash for traffic allocation check
        traffic_hash = self._hash(user_id, f"{hash_salt}_traffic")
        traffic_value = traffic_hash / self.MAX_HASH_VALUE

        # Check if user is in traffic allocation
        if traffic_value >= traffic_allocation:
            return None  # User excluded from experiment

        # Calculate hash for variant assignment
        variant_hash = self._hash(user_id, f"{hash_salt}_variant")
        variant_value = variant_hash / self.MAX_HASH_VALUE

        # Assign to variant based on cumulative allocation
        cumulative = 0.0
        for variant in variants:
            cumulative += variant.get("allocation", 0)
            if variant_value < cumulative:
                return variant.get("key")

        # Fallback to last variant (should not happen if allocations sum to 1.0)
        return variants[-1].get("key")

    def _hash(self, user_id: str, salt: str) -> int:
        """
        Calculate MurmurHash3-like hash for consistent assignment.

        Uses Python's hashlib as a substitute for MurmurHash3.
        In production, consider using mmh3 library for better performance.

        Args:
            user_id: User identifier
            salt: Salt string (usually experiment key)

        Returns:
            32-bit unsigned integer hash value
        """
        # Combine user_id and salt
        combined = f"{user_id}:{salt}".encode('utf-8')

        # Use MD5 for deterministic hashing (first 4 bytes as uint32)
        hash_bytes = hashlib.md5(combined).digest()[:4]
        hash_value = struct.unpack('<I', hash_bytes)[0]

        return hash_value

    def get_bucket(
        self,
        user_id: str,
        experiment_key: str,
        num_buckets: int = 10000
    ) -> int:
        """
        Get the bucket number for a user in an experiment.

        Useful for percentage-based rollouts and A/A tests.

        Args:
            user_id: User identifier
            experiment_key: Experiment key
            num_buckets: Total number of buckets (default: 10000 for 0.01% precision)

        Returns:
            Bucket number (0 to num_buckets-1)
        """
        hash_value = self._hash(user_id, experiment_key)
        return hash_value % num_buckets


# Singleton instance for reuse
_hasher_instance = None


def get_hasher() -> ConsistentHasher:
    """
    Get singleton instance of ConsistentHasher.

    Returns:
        ConsistentHasher instance
    """
    global _hasher_instance
    if _hasher_instance is None:
        _hasher_instance = ConsistentHasher()
    return _hasher_instance
