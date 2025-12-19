"""
Unit tests for Targeting Rules and Caching (Day 3).

Tests targeting rule evaluation and Lambda warm-start caching.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from time import sleep

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from models import ExperimentConfig, VariantConfig, ExperimentStatus


class TestTargetingRules:
    """Test suite for Targeting Rule Evaluation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.experiment_with_rules = ExperimentConfig(
            experiment_id="exp_targeted",
            key="targeted_test",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ],
            targeting_rules=[
                {
                    "attribute": "country",
                    "operator": "equals",
                    "value": "US"
                }
            ]
        )

    # Day 3, Task 2.9: Tests for targeting rule evaluation
    def test_evaluate_targeting_rules_user_matches(self):
        """Test that user matching targeting rule gets assigned."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        context = {"country": "US", "platform": "web"}

        matches = service.evaluate_targeting_rules(
            self.experiment_with_rules.targeting_rules,
            context
        )

        assert matches is True

    def test_evaluate_targeting_rules_user_not_matching(self):
        """Test that user not matching rule is excluded."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        context = {"country": "CA", "platform": "web"}

        matches = service.evaluate_targeting_rules(
            self.experiment_with_rules.targeting_rules,
            context
        )

        assert matches is False

    def test_evaluate_targeting_rules_multiple_rules_and_logic(self):
        """Test multiple rules with AND logic."""
        from assignment_service import AssignmentService

        rules = [
            {"attribute": "country", "operator": "equals", "value": "US"},
            {"attribute": "platform", "operator": "equals", "value": "web"}
        ]

        service = AssignmentService()

        # Both match
        context_match = {"country": "US", "platform": "web"}
        assert service.evaluate_targeting_rules(rules, context_match) is True

        # One doesn't match
        context_no_match = {"country": "US", "platform": "mobile"}
        assert service.evaluate_targeting_rules(rules, context_no_match) is False

    def test_evaluate_targeting_rules_missing_context_attribute(self):
        """Test handling of missing context attributes."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        context = {"platform": "web"}  # Missing 'country'

        matches = service.evaluate_targeting_rules(
            self.experiment_with_rules.targeting_rules,
            context
        )

        assert matches is False

    def test_evaluate_targeting_rules_no_rules_returns_true(self):
        """Test that experiments with no targeting rules accept all users."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        context = {"country": "CA"}

        matches = service.evaluate_targeting_rules(None, context)

        assert matches is True

    def test_evaluate_targeting_rules_empty_rules_returns_true(self):
        """Test that empty rules list accepts all users."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        context = {"country": "CA"}

        matches = service.evaluate_targeting_rules([], context)

        assert matches is True

    def test_evaluate_targeting_rules_in_operator(self):
        """Test 'in' operator for list values."""
        from assignment_service import AssignmentService

        rules = [
            {"attribute": "country", "operator": "in", "value": ["US", "CA", "UK"]}
        ]

        service = AssignmentService()

        # Should match
        assert service.evaluate_targeting_rules(
            rules, {"country": "US"}
        ) is True

        # Should not match
        assert service.evaluate_targeting_rules(
            rules, {"country": "FR"}
        ) is False

    def test_evaluate_targeting_rules_greater_than_operator(self):
        """Test 'greater_than' operator for numeric values."""
        from assignment_service import AssignmentService

        rules = [
            {"attribute": "age", "operator": "greater_than", "value": 18}
        ]

        service = AssignmentService()

        # Should match
        assert service.evaluate_targeting_rules(
            rules, {"age": 25}
        ) is True

        # Should not match
        assert service.evaluate_targeting_rules(
            rules, {"age": 16}
        ) is False

    def test_assign_variant_respects_targeting_rules(self):
        """Test that variant assignment respects targeting rules."""
        from assignment_service import AssignmentService

        service = AssignmentService()

        # User matching targeting rules should get assigned
        context_match = {"country": "US"}
        variant = service.assign_variant(
            "user_us_123",
            self.experiment_with_rules,
            context_match
        )
        assert variant in ["control", "treatment"]

        # User not matching targeting rules should not get assigned
        context_no_match = {"country": "CA"}
        variant_excluded = service.assign_variant(
            "user_ca_456",
            self.experiment_with_rules,
            context_no_match
        )
        assert variant_excluded is None


class TestLambdaCaching:
    """Test suite for Lambda Warm-Start Caching."""

    # Day 3, Task 2.11: Tests for caching layer
    @patch('assignment_service.get_dynamodb_resource')
    def test_get_experiment_config_caches_result(self, mock_get_resource):
        """Test that experiment config is cached after first fetch."""
        from assignment_service import AssignmentService

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'experiment_id': 'exp_cache_test',
                'key': 'cache_test',
                'status': 'active',
                'variants': [
                    {'key': 'control', 'allocation': 0.5},
                    {'key': 'treatment', 'allocation': 0.5}
                ],
                'traffic_allocation': 1.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        service = AssignmentService()

        # First call - should fetch from DynamoDB
        config1 = service.get_experiment_config_cached("cache_test")
        assert mock_table.get_item.call_count == 1

        # Second call - should use cache
        config2 = service.get_experiment_config_cached("cache_test")
        assert mock_table.get_item.call_count == 1  # Still 1, not 2

        # Both should return same config
        assert config1.experiment_id == config2.experiment_id

    @patch('assignment_service.get_dynamodb_resource')
    def test_cache_miss_fetches_from_dynamodb(self, mock_get_resource):
        """Test that cache miss triggers DynamoDB fetch."""
        from assignment_service import AssignmentService

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'experiment_id': 'exp_123',
                'key': 'test_exp',
                'status': 'active',
                'variants': [
                    {'key': 'control', 'allocation': 0.5},
                    {'key': 'treatment', 'allocation': 0.5}
                ],
                'traffic_allocation': 1.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        service = AssignmentService()
        config = service.get_experiment_config_cached("test_exp")

        assert config is not None
        assert mock_table.get_item.called

    def test_cache_invalidation_after_ttl(self):
        """Test that cache entries expire after TTL."""
        from assignment_service import AssignmentService

        service = AssignmentService()

        # Set a very short TTL for testing
        service.cache_ttl = 0.1  # 100ms

        # Add item to cache
        service._experiment_cache["test_key"] = {
            "config": "test_config",
            "timestamp": datetime.now(timezone.utc).timestamp()
        }

        # Immediately check - should be valid
        assert service._is_cache_valid("test_key") is True

        # Wait for TTL to expire
        sleep(0.15)

        # Should be invalid now
        assert service._is_cache_valid("test_key") is False

    def test_cache_stores_experiment_config(self):
        """Test that cache properly stores experiment configs."""
        from assignment_service import AssignmentService

        service = AssignmentService()

        config = ExperimentConfig(
            experiment_id="exp_123",
            key="test",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        # Store in cache
        service._cache_experiment_config("test", config)

        # Verify it's in cache
        assert "test" in service._experiment_cache
        cached_entry = service._experiment_cache["test"]
        assert cached_entry["config"].experiment_id == "exp_123"
        assert "timestamp" in cached_entry

    def test_cache_hit_rate_tracking(self):
        """Test that cache hit rate is tracked."""
        from assignment_service import AssignmentService

        service = AssignmentService()

        # Initialize counters
        service._cache_hits = 0
        service._cache_misses = 0

        # Simulate cache miss
        service._record_cache_miss()
        assert service._cache_misses == 1

        # Simulate cache hits
        service._record_cache_hit()
        service._record_cache_hit()
        assert service._cache_hits == 2

        # Calculate hit rate
        hit_rate = service.get_cache_hit_rate()
        assert hit_rate == pytest.approx(0.667, 0.01)  # 2/3 ≈ 66.7%

    @patch('assignment_service.get_dynamodb_resource')
    def test_different_experiments_cached_separately(self, mock_get_resource):
        """Test that different experiments are cached with separate keys."""
        from assignment_service import AssignmentService

        # Mock DynamoDB to return different experiments
        def get_item_side_effect(**kwargs):
            key = kwargs['Key']['key']
            return {
                'Item': {
                    'experiment_id': f'exp_{key}',
                    'key': key,
                    'status': 'active',
                    'variants': [
                        {'key': 'control', 'allocation': 0.5},
                        {'key': 'treatment', 'allocation': 0.5}
                    ],
                    'traffic_allocation': 1.0
                }
            }

        mock_table = Mock()
        mock_table.get_item.side_effect = get_item_side_effect
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        service = AssignmentService()

        # Fetch two different experiments
        config1 = service.get_experiment_config_cached("exp_a")
        config2 = service.get_experiment_config_cached("exp_b")

        # Both should be cached separately
        assert "exp_a" in service._experiment_cache
        assert "exp_b" in service._experiment_cache
        assert config1.experiment_id != config2.experiment_id

    def test_cache_handles_none_values(self):
        """Test that cache properly handles None (missing experiments)."""
        from assignment_service import AssignmentService

        service = AssignmentService()

        # Cache a None value (experiment not found)
        service._cache_experiment_config("missing_exp", None)

        # Should be in cache
        assert "missing_exp" in service._experiment_cache
        cached_entry = service._experiment_cache["missing_exp"]
        assert cached_entry["config"] is None
