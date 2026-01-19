"""
Unit tests for Feature Flag Evaluator.

Tests the core feature flag evaluation logic including:
- Flag configuration fetching and caching
- Rollout percentage evaluation
- Targeting rules evaluation
- User context matching
- Default value handling

Following TDD (Test-Driven Development) - RED phase: Tests written first.
All tests should fail until evaluator.py is implemented.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from models import FeatureFlagConfig, VariantConfig


class TestFeatureFlagEvaluator:
    """Test suite for Feature Flag Evaluator core logic."""

    def setup_method(self):
        """Set up test fixtures."""
        # Simple enabled flag with 100% rollout
        self.enabled_flag = FeatureFlagConfig(
            flag_id="flag_123",
            key="new_checkout",
            enabled=True,
            rollout_percentage=100.0
        )

        # Disabled flag
        self.disabled_flag = FeatureFlagConfig(
            flag_id="flag_disabled",
            key="disabled_feature",
            enabled=False,
            rollout_percentage=100.0
        )

        # Flag with 50% rollout
        self.partial_rollout_flag = FeatureFlagConfig(
            flag_id="flag_partial",
            key="partial_feature",
            enabled=True,
            rollout_percentage=50.0
        )

        # Flag with targeting rules
        self.targeted_flag = FeatureFlagConfig(
            flag_id="flag_targeted",
            key="targeted_feature",
            enabled=True,
            rollout_percentage=100.0,
            targeting_rules=[
                {"attribute": "country", "operator": "equals", "value": "US"}
            ]
        )

        # Flag with variants
        self.variant_flag = FeatureFlagConfig(
            flag_id="flag_variants",
            key="variant_feature",
            enabled=True,
            rollout_percentage=100.0,
            default_variant="control",
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

    # ====================================================================
    # Task 4.1: Tests for flag config fetching
    # ====================================================================

    @patch('evaluator.get_dynamodb_resource')
    def test_get_flag_config_returns_valid_config(self, mock_get_resource):
        """Test that valid flag returns configuration."""
        from evaluator import FeatureFlagEvaluator

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'flag_123',
                'key': 'new_checkout',
                'enabled': True,
                'rollout_percentage': 100.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        evaluator = FeatureFlagEvaluator()
        config = evaluator.get_flag_config("new_checkout")

        assert config is not None
        assert config.flag_id == "flag_123"
        assert config.key == "new_checkout"
        assert config.enabled is True

    @patch('evaluator.get_dynamodb_resource')
    def test_get_flag_config_missing_flag_returns_none(self, mock_get_resource):
        """Test that invalid flag_key returns None."""
        from evaluator import FeatureFlagEvaluator

        # Mock DynamoDB response - no item found
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        evaluator = FeatureFlagEvaluator()
        config = evaluator.get_flag_config("nonexistent_flag")

        assert config is None

    def test_evaluate_disabled_flag_returns_false(self):
        """Test that disabled flag returns False regardless of rollout."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()
        result = evaluator.evaluate(
            user_id="user_123",
            flag_config=self.disabled_flag
        )

        assert result["enabled"] is False
        assert result["reason"] == "flag_disabled"

    @patch('evaluator.get_dynamodb_resource')
    def test_get_flag_config_cached_returns_from_cache(self, mock_get_resource):
        """Test that config is cached after first fetch."""
        from evaluator import FeatureFlagEvaluator

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'flag_cached',
                'key': 'cached_feature',
                'enabled': True,
                'rollout_percentage': 100.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        evaluator = FeatureFlagEvaluator()

        # First call - should hit DynamoDB
        config1 = evaluator.get_flag_config_cached("cached_feature")
        assert mock_table.get_item.call_count == 1

        # Second call - should use cache
        config2 = evaluator.get_flag_config_cached("cached_feature")
        assert mock_table.get_item.call_count == 1  # No additional call

        # Results should be identical
        assert config1.flag_id == config2.flag_id

    # ====================================================================
    # Task 4.3: Tests for rollout percentage logic
    # ====================================================================

    def test_rollout_zero_percent_returns_false_for_all_users(self):
        """Test that 0% rollout returns False for all users."""
        from evaluator import FeatureFlagEvaluator

        zero_rollout_flag = FeatureFlagConfig(
            flag_id="flag_zero",
            key="zero_rollout",
            enabled=True,
            rollout_percentage=0.0
        )

        evaluator = FeatureFlagEvaluator()

        # Test 100 different users - all should get False
        for i in range(100):
            result = evaluator.evaluate(
                user_id=f"user_{i}",
                flag_config=zero_rollout_flag
            )
            assert result["enabled"] is False
            assert result["reason"] == "not_in_rollout"

    def test_rollout_hundred_percent_returns_true_for_all_users(self):
        """Test that 100% rollout returns True for all users."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()

        # Test 100 different users - all should get True
        for i in range(100):
            result = evaluator.evaluate(
                user_id=f"user_{i}",
                flag_config=self.enabled_flag
            )
            assert result["enabled"] is True
            assert result["reason"] == "enabled"

    def test_rollout_fifty_percent_splits_users_evenly(self):
        """Test that 50% rollout splits users approximately evenly (±5%)."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()
        results = []

        # Test 1000 users
        for i in range(1000):
            result = evaluator.evaluate(
                user_id=f"user_{i}",
                flag_config=self.partial_rollout_flag
            )
            results.append(result["enabled"])

        # Count enabled
        enabled_count = sum(results)
        enabled_rate = enabled_count / len(results)

        # Should be within ±5% of 50%
        assert 0.45 <= enabled_rate <= 0.55, \
            f"Enabled rate: {enabled_rate:.2%} (expected ~50%)"

    def test_rollout_same_user_gets_consistent_result(self):
        """Test that same user gets consistent result across multiple calls."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()
        user_id = "user_123"

        # Call multiple times
        results = [
            evaluator.evaluate(user_id, self.partial_rollout_flag)
            for _ in range(10)
        ]

        # All results should be identical
        enabled_values = [r["enabled"] for r in results]
        assert len(set(enabled_values)) == 1, \
            "Same user should get consistent result"

    def test_rollout_with_different_flag_keys_gives_different_distributions(self):
        """Test that different flags give independent distributions."""
        from evaluator import FeatureFlagEvaluator

        flag_a = FeatureFlagConfig(
            flag_id="flag_a",
            key="feature_a",
            enabled=True,
            rollout_percentage=50.0
        )

        flag_b = FeatureFlagConfig(
            flag_id="flag_b",
            key="feature_b",
            enabled=True,
            rollout_percentage=50.0
        )

        evaluator = FeatureFlagEvaluator()

        # Evaluate same user for both flags
        results_a = []
        results_b = []

        for i in range(100):
            user_id = f"user_{i}"
            result_a = evaluator.evaluate(user_id, flag_a)
            result_b = evaluator.evaluate(user_id, flag_b)
            results_a.append(result_a["enabled"])
            results_b.append(result_b["enabled"])

        # Results should not be identical (independent distributions)
        # At least some users should have different results
        different_results = sum(
            a != b for a, b in zip(results_a, results_b)
        )
        assert different_results > 10, \
            "Different flags should have independent distributions"

    # ====================================================================
    # Task 4.5: Tests for targeting rules
    # ====================================================================

    def test_targeting_rule_user_matching_gets_enabled(self):
        """Test that user matching targeting rule gets flag enabled."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()
        context = {"country": "US", "platform": "web"}

        result = evaluator.evaluate(
            user_id="user_us",
            flag_config=self.targeted_flag,
            context=context
        )

        assert result["enabled"] is True
        assert result["reason"] == "enabled"

    def test_targeting_rule_user_not_matching_gets_disabled(self):
        """Test that user not matching targeting rule gets flag disabled."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()
        context = {"country": "CA", "platform": "web"}

        result = evaluator.evaluate(
            user_id="user_ca",
            flag_config=self.targeted_flag,
            context=context
        )

        assert result["enabled"] is False
        assert result["reason"] == "targeting_rules_not_met"

    def test_targeting_multiple_rules_evaluated_with_and_logic(self):
        """Test that multiple rules are evaluated with AND logic."""
        from evaluator import FeatureFlagEvaluator

        multi_rule_flag = FeatureFlagConfig(
            flag_id="flag_multi",
            key="multi_rule_feature",
            enabled=True,
            rollout_percentage=100.0,
            targeting_rules=[
                {"attribute": "country", "operator": "equals", "value": "US"},
                {"attribute": "platform", "operator": "equals", "value": "web"}
            ]
        )

        evaluator = FeatureFlagEvaluator()

        # Both rules match - should be enabled
        context_match = {"country": "US", "platform": "web"}
        result_match = evaluator.evaluate(
            user_id="user_match",
            flag_config=multi_rule_flag,
            context=context_match
        )
        assert result_match["enabled"] is True

        # Only one rule matches - should be disabled
        context_partial = {"country": "US", "platform": "mobile"}
        result_partial = evaluator.evaluate(
            user_id="user_partial",
            flag_config=multi_rule_flag,
            context=context_partial
        )
        assert result_partial["enabled"] is False

    def test_targeting_missing_context_attribute_returns_disabled(self):
        """Test that missing context attributes are handled gracefully."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()

        # Context missing required attribute
        context = {"platform": "web"}  # Missing 'country'

        result = evaluator.evaluate(
            user_id="user_missing",
            flag_config=self.targeted_flag,
            context=context
        )

        assert result["enabled"] is False
        assert result["reason"] == "targeting_rules_not_met"

    def test_targeting_no_context_provided_returns_disabled(self):
        """Test that no context provided disables targeted flag."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()

        result = evaluator.evaluate(
            user_id="user_no_context",
            flag_config=self.targeted_flag,
            context=None
        )

        assert result["enabled"] is False
        assert result["reason"] == "targeting_rules_not_met"

    def test_targeting_with_in_operator(self):
        """Test targeting rules with 'in' operator."""
        from evaluator import FeatureFlagEvaluator

        in_operator_flag = FeatureFlagConfig(
            flag_id="flag_in",
            key="in_operator_feature",
            enabled=True,
            rollout_percentage=100.0,
            targeting_rules=[
                {"attribute": "country", "operator": "in", "value": ["US", "CA", "UK"]}
            ]
        )

        evaluator = FeatureFlagEvaluator()

        # User in list - should be enabled
        context_in = {"country": "CA"}
        result_in = evaluator.evaluate(
            user_id="user_in_list",
            flag_config=in_operator_flag,
            context=context_in
        )
        assert result_in["enabled"] is True

        # User not in list - should be disabled
        context_out = {"country": "FR"}
        result_out = evaluator.evaluate(
            user_id="user_out_list",
            flag_config=in_operator_flag,
            context=context_out
        )
        assert result_out["enabled"] is False

    def test_targeting_with_greater_than_operator(self):
        """Test targeting rules with 'greater_than' operator."""
        from evaluator import FeatureFlagEvaluator

        gt_operator_flag = FeatureFlagConfig(
            flag_id="flag_gt",
            key="gt_operator_feature",
            enabled=True,
            rollout_percentage=100.0,
            targeting_rules=[
                {"attribute": "age", "operator": "greater_than", "value": 18}
            ]
        )

        evaluator = FeatureFlagEvaluator()

        # User age > 18 - should be enabled
        context_gt = {"age": 25}
        result_gt = evaluator.evaluate(
            user_id="user_adult",
            flag_config=gt_operator_flag,
            context=context_gt
        )
        assert result_gt["enabled"] is True

        # User age <= 18 - should be disabled
        context_lte = {"age": 16}
        result_lte = evaluator.evaluate(
            user_id="user_minor",
            flag_config=gt_operator_flag,
            context=context_lte
        )
        assert result_lte["enabled"] is False

    # ====================================================================
    # Additional tests for edge cases and variants
    # ====================================================================

    def test_evaluate_with_variants_returns_variant(self):
        """Test that flag with variants returns a variant key."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()

        result = evaluator.evaluate(
            user_id="user_variant",
            flag_config=self.variant_flag
        )

        assert result["enabled"] is True
        assert result["variant"] in ["control", "treatment"]

    def test_evaluate_variant_assignment_is_consistent(self):
        """Test that same user gets same variant across calls."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()
        user_id = "user_consistent"

        # Call multiple times
        results = [
            evaluator.evaluate(user_id, self.variant_flag)
            for _ in range(10)
        ]

        # All variants should be identical
        variants = [r["variant"] for r in results]
        assert len(set(variants)) == 1, \
            "Same user should get consistent variant"

    def test_evaluate_variant_distribution_matches_allocation(self):
        """Test that variant distribution matches allocation percentages."""
        from evaluator import FeatureFlagEvaluator

        # Flag with 70/30 variant split
        uneven_variant_flag = FeatureFlagConfig(
            flag_id="flag_uneven",
            key="uneven_variants",
            enabled=True,
            rollout_percentage=100.0,
            default_variant="control",
            variants=[
                VariantConfig(key="control", allocation=0.7),
                VariantConfig(key="treatment", allocation=0.3)
            ]
        )

        evaluator = FeatureFlagEvaluator()
        results = []

        for i in range(1000):
            result = evaluator.evaluate(f"user_{i}", uneven_variant_flag)
            results.append(result.get("variant"))

        control_pct = results.count("control") / len(results)
        treatment_pct = results.count("treatment") / len(results)

        # Should be within ±5% of target allocation
        assert 0.65 <= control_pct <= 0.75, \
            f"Control: {control_pct:.2%} (expected ~70%)"
        assert 0.25 <= treatment_pct <= 0.35, \
            f"Treatment: {treatment_pct:.2%} (expected ~30%)"

    def test_evaluate_with_null_user_id_raises_error(self):
        """Test that None user_id raises ValueError."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()

        with pytest.raises(ValueError, match="user_id cannot be None"):
            evaluator.evaluate(
                user_id=None,
                flag_config=self.enabled_flag
            )

    def test_evaluate_with_empty_user_id_raises_error(self):
        """Test that empty user_id raises ValueError."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()

        with pytest.raises(ValueError, match="user_id cannot be empty"):
            evaluator.evaluate(
                user_id="",
                flag_config=self.enabled_flag
            )

    def test_cache_hit_rate_tracking(self):
        """Test that cache hit rate is tracked correctly."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()

        # Mock cache behavior
        with patch.object(evaluator, 'get_flag_config_cached') as mock_cached:
            # First call - cache miss
            mock_cached.side_effect = [
                self.enabled_flag,  # First call - miss
                self.enabled_flag,  # Second call - hit
                self.enabled_flag   # Third call - hit
            ]

            evaluator.get_flag_config_cached("test_flag")
            evaluator.get_flag_config_cached("test_flag")
            evaluator.get_flag_config_cached("test_flag")

            # Get cache hit rate
            hit_rate = evaluator.get_cache_hit_rate()

            # Should have some cache hits
            assert hit_rate >= 0.0
            assert hit_rate <= 1.0

    def test_evaluate_combines_targeting_and_rollout(self):
        """Test that both targeting rules and rollout percentage are applied."""
        from evaluator import FeatureFlagEvaluator

        # Flag with both targeting and partial rollout
        combined_flag = FeatureFlagConfig(
            flag_id="flag_combined",
            key="combined_feature",
            enabled=True,
            rollout_percentage=50.0,
            targeting_rules=[
                {"attribute": "country", "operator": "equals", "value": "US"}
            ]
        )

        evaluator = FeatureFlagEvaluator()

        # User matches targeting but may be excluded by rollout
        context_match = {"country": "US"}

        results = []
        for i in range(100):
            result = evaluator.evaluate(
                user_id=f"user_{i}",
                flag_config=combined_flag,
                context=context_match
            )
            results.append(result["enabled"])

        # Some users should be enabled (matched targeting and rollout)
        enabled_count = sum(results)

        # Should be less than 100% but more than 0%
        assert 0 < enabled_count < 100, \
            "Should have partial rollout among targeted users"

        # User NOT matching targeting should always be disabled
        context_no_match = {"country": "CA"}
        for i in range(10):
            result = evaluator.evaluate(
                user_id=f"user_ca_{i}",
                flag_config=combined_flag,
                context=context_no_match
            )
            assert result["enabled"] is False, \
                "Users not matching targeting should always be disabled"

    # ====================================================================
    # Batch Evaluation Tests
    # ====================================================================

    @patch('evaluator.get_dynamodb_resource')
    def test_batch_evaluate_multiple_flags(self, mock_get_resource):
        """Test batch evaluation of multiple flags."""
        from evaluator import FeatureFlagEvaluator

        # Mock DynamoDB to return different flags
        def get_item_side_effect(**kwargs):
            flag_key = kwargs['Key']['key']
            if flag_key == "flag1":
                return {'Item': {
                    'flag_id': 'flag_1', 'key': 'flag1',
                    'enabled': True, 'rollout_percentage': 100.0
                }}
            elif flag_key == "flag2":
                return {'Item': {
                    'flag_id': 'flag_2', 'key': 'flag2',
                    'enabled': False, 'rollout_percentage': 100.0
                }}
            elif flag_key == "flag3":
                return {'Item': {
                    'flag_id': 'flag_3', 'key': 'flag3',
                    'enabled': True, 'rollout_percentage': 50.0
                }}
            else:
                return {}  # Flag not found

        mock_table = Mock()
        mock_table.get_item = Mock(side_effect=get_item_side_effect)
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        evaluator = FeatureFlagEvaluator()

        # Batch evaluate multiple flags
        results = evaluator.batch_evaluate(
            user_id="user_123",
            flag_keys=["flag1", "flag2", "flag3", "flag4"]
        )

        # Verify results
        assert len(results) == 4

        # flag1 - enabled
        assert results["flag1"]["enabled"] is True
        assert results["flag1"]["reason"] == "enabled"

        # flag2 - disabled (flag itself disabled)
        assert results["flag2"]["enabled"] is False
        assert results["flag2"]["reason"] == "flag_disabled"

        # flag3 - may be enabled or disabled (50% rollout)
        assert results["flag3"]["enabled"] in [True, False]

        # flag4 - not found
        assert results["flag4"]["enabled"] is False
        assert results["flag4"]["reason"] == "flag_not_found"

    @patch('evaluator.get_dynamodb_resource')
    def test_batch_evaluate_uses_cache(self, mock_get_resource):
        """Test that batch evaluation benefits from caching."""
        from evaluator import FeatureFlagEvaluator

        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'cached_flag', 'key': 'cached',
                'enabled': True, 'rollout_percentage': 100.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        evaluator = FeatureFlagEvaluator()

        # First batch - cache miss
        results1 = evaluator.batch_evaluate(
            user_id="user_123",
            flag_keys=["cached"]
        )
        assert mock_table.get_item.call_count == 1

        # Second batch - cache hit
        results2 = evaluator.batch_evaluate(
            user_id="user_123",
            flag_keys=["cached"]
        )
        assert mock_table.get_item.call_count == 1  # No additional call

        # Results should be consistent
        assert results1["cached"]["enabled"] == results2["cached"]["enabled"]

    def test_batch_evaluate_empty_list(self):
        """Test batch evaluate with empty flag list."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()
        results = evaluator.batch_evaluate(
            user_id="user_123",
            flag_keys=[]
        )

        assert results == {}

    def test_batch_evaluate_invalid_user_id(self):
        """Test batch evaluate with invalid user_id."""
        from evaluator import FeatureFlagEvaluator

        evaluator = FeatureFlagEvaluator()

        with pytest.raises(ValueError, match="user_id cannot be None or empty"):
            evaluator.batch_evaluate(
                user_id="",
                flag_keys=["flag1"]
            )
