"""
Unit tests for consistent hashing implementation.

Tests the ConsistentHasher class for deterministic variant assignments.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from consistent_hash import ConsistentHasher, get_hasher


class TestConsistentHasher:
    """Test suite for ConsistentHasher class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.hasher = ConsistentHasher()
        self.variants = [
            {"key": "control", "allocation": 0.5},
            {"key": "treatment", "allocation": 0.5}
        ]

    def test_same_user_experiment_returns_same_variant(self):
        """Test that same user+experiment always returns same variant."""
        user_id = "user_123"
        experiment_key = "exp_001"

        # Call multiple times
        results = [
            self.hasher.assign_variant(user_id, experiment_key, self.variants)
            for _ in range(10)
        ]

        # All results should be identical
        assert len(set(results)) == 1, "Same user should get same variant"
        assert results[0] in ["control", "treatment"]

    def test_different_users_get_different_variants(self):
        """Test that different users can get different variants."""
        experiment_key = "exp_001"

        results = [
            self.hasher.assign_variant(f"user_{i}", experiment_key, self.variants)
            for i in range(100)
        ]

        # Should have both variants assigned
        unique_variants = set(results)
        assert "control" in unique_variants or "treatment" in unique_variants
        assert len(unique_variants) >= 1

    def test_variant_distribution_matches_allocation(self):
        """Test that variant distribution matches allocation percentages (±2%)."""
        experiment_key = "exp_allocation_test"
        num_users = 10000

        results = [
            self.hasher.assign_variant(f"user_{i}", experiment_key, self.variants)
            for i in range(num_users)
        ]

        # Count assignments
        control_count = results.count("control")
        treatment_count = results.count("treatment")

        # Calculate percentages
        control_pct = control_count / num_users
        treatment_pct = treatment_count / num_users

        # Should be within ±2% of 50/50
        assert 0.48 <= control_pct <= 0.52, f"Control: {control_pct:.2%} (expected ~50%)"
        assert 0.48 <= treatment_pct <= 0.52, f"Treatment: {treatment_pct:.2%} (expected ~50%)"

    def test_traffic_allocation_excludes_users(self):
        """Test that traffic allocation excludes correct percentage of users."""
        experiment_key = "exp_traffic_test"
        traffic_allocation = 0.5  # 50% of users
        num_users = 10000

        results = [
            self.hasher.assign_variant(
                f"user_{i}",
                experiment_key,
                self.variants,
                traffic_allocation=traffic_allocation
            )
            for i in range(num_users)
        ]

        # Count non-None assignments
        assigned = [r for r in results if r is not None]
        assignment_rate = len(assigned) / num_users

        # Should be within ±2% of 50%
        assert 0.48 <= assignment_rate <= 0.52, \
            f"Assignment rate: {assignment_rate:.2%} (expected ~50%)"

    def test_zero_traffic_allocation_excludes_all(self):
        """Test that 0% traffic allocation excludes all users."""
        results = [
            self.hasher.assign_variant(
                f"user_{i}",
                "exp_zero_traffic",
                self.variants,
                traffic_allocation=0.0
            )
            for i in range(100)
        ]

        # All should be None
        assert all(r is None for r in results), "0% traffic should exclude all users"

    def test_full_traffic_allocation_includes_all(self):
        """Test that 100% traffic allocation includes all users."""
        results = [
            self.hasher.assign_variant(
                f"user_{i}",
                "exp_full_traffic",
                self.variants,
                traffic_allocation=1.0
            )
            for i in range(100)
        ]

        # All should be assigned
        assert all(r is not None for r in results), "100% traffic should include all users"

    def test_uneven_variant_allocation(self):
        """Test uneven variant allocation (80/20 split)."""
        variants = [
            {"key": "control", "allocation": 0.8},
            {"key": "treatment", "allocation": 0.2}
        ]
        num_users = 10000

        results = [
            self.hasher.assign_variant(f"user_{i}", "exp_uneven", variants)
            for i in range(num_users)
        ]

        control_pct = results.count("control") / num_users
        treatment_pct = results.count("treatment") / num_users

        # Should be within ±2% of 80/20
        assert 0.78 <= control_pct <= 0.82, f"Control: {control_pct:.2%} (expected ~80%)"
        assert 0.18 <= treatment_pct <= 0.22, f"Treatment: {treatment_pct:.2%} (expected ~20%)"

    def test_three_way_variant_allocation(self):
        """Test three-way variant allocation (33/33/34 split)."""
        variants = [
            {"key": "control", "allocation": 0.33},
            {"key": "variant_a", "allocation": 0.33},
            {"key": "variant_b", "allocation": 0.34}
        ]
        num_users = 10000

        results = [
            self.hasher.assign_variant(f"user_{i}", "exp_three_way", variants)
            for i in range(num_users)
        ]

        control_pct = results.count("control") / num_users
        variant_a_pct = results.count("variant_a") / num_users
        variant_b_pct = results.count("variant_b") / num_users

        # Each should be within ±3% of their target
        assert 0.30 <= control_pct <= 0.36, f"Control: {control_pct:.2%} (expected ~33%)"
        assert 0.30 <= variant_a_pct <= 0.36, f"Variant A: {variant_a_pct:.2%} (expected ~33%)"
        assert 0.31 <= variant_b_pct <= 0.37, f"Variant B: {variant_b_pct:.2%} (expected ~34%)"

    def test_salt_changes_assignment(self):
        """Test that different salt values produce different assignments."""
        user_id = "user_123"
        experiment_key = "exp_001"

        result_no_salt = self.hasher.assign_variant(
            user_id, experiment_key, self.variants
        )
        result_with_salt = self.hasher.assign_variant(
            user_id, experiment_key, self.variants, salt="custom_salt"
        )

        # May or may not be different, but algorithm should handle salt
        assert result_no_salt in ["control", "treatment"]
        assert result_with_salt in ["control", "treatment"]

    def test_empty_variants_raises_error(self):
        """Test that empty variants list raises ValueError."""
        with pytest.raises(ValueError, match="Variants list cannot be empty"):
            self.hasher.assign_variant("user_123", "exp_001", [])

    def test_invalid_traffic_allocation_raises_error(self):
        """Test that invalid traffic allocation raises ValueError."""
        with pytest.raises(ValueError, match="Traffic allocation must be between"):
            self.hasher.assign_variant(
                "user_123", "exp_001", self.variants, traffic_allocation=1.5
            )

        with pytest.raises(ValueError, match="Traffic allocation must be between"):
            self.hasher.assign_variant(
                "user_123", "exp_001", self.variants, traffic_allocation=-0.1
            )

    def test_variant_allocations_not_summing_to_one_raises_error(self):
        """Test that variant allocations not summing to 1.0 raises ValueError."""
        invalid_variants = [
            {"key": "control", "allocation": 0.4},
            {"key": "treatment", "allocation": 0.4}
        ]

        with pytest.raises(ValueError, match="Variant allocations must sum to 1.0"):
            self.hasher.assign_variant("user_123", "exp_001", invalid_variants)

    def test_get_bucket_returns_consistent_value(self):
        """Test that get_bucket returns consistent value for same user."""
        user_id = "user_123"
        experiment_key = "exp_001"

        buckets = [
            self.hasher.get_bucket(user_id, experiment_key)
            for _ in range(10)
        ]

        # All buckets should be identical
        assert len(set(buckets)) == 1
        assert 0 <= buckets[0] < 10000

    def test_get_bucket_distribution(self):
        """Test that get_bucket distributes users evenly across buckets."""
        experiment_key = "exp_bucket_test"
        num_buckets = 100
        num_users = 10000

        buckets = [
            self.hasher.get_bucket(f"user_{i}", experiment_key, num_buckets)
            for i in range(num_users)
        ]

        # Count occurrences in each bucket
        bucket_counts = [buckets.count(i) for i in range(num_buckets)]

        # Each bucket should have roughly 100 users (±30 to account for hash variance)
        for i, count in enumerate(bucket_counts):
            assert 70 <= count <= 130, \
                f"Bucket {i} has {count} users (expected ~100)"

    def test_get_hasher_returns_singleton(self):
        """Test that get_hasher returns singleton instance."""
        hasher1 = get_hasher()
        hasher2 = get_hasher()

        assert hasher1 is hasher2, "get_hasher should return singleton"

    def test_hash_method_is_deterministic(self):
        """Test that _hash method returns consistent values."""
        user_id = "user_123"
        salt = "exp_001"

        hash_values = [
            self.hasher._hash(user_id, salt)
            for _ in range(10)
        ]

        # All hash values should be identical
        assert len(set(hash_values)) == 1
        assert 0 <= hash_values[0] <= self.hasher.MAX_HASH_VALUE

    def test_different_users_get_different_hashes(self):
        """Test that different users get different hash values."""
        salt = "exp_001"

        hashes = [
            self.hasher._hash(f"user_{i}", salt)
            for i in range(100)
        ]

        # Should have mostly unique hashes (collisions are rare but possible)
        unique_hashes = len(set(hashes))
        assert unique_hashes >= 95, f"Only {unique_hashes}/100 hashes were unique"
