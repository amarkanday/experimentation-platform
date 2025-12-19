"""
Unit tests for Error Handling (Day 4).

Tests comprehensive error scenarios including validation errors,
not found errors, and internal server errors.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from models import ExperimentConfig, VariantConfig, ExperimentStatus


class TestValidationErrors:
    """Test suite for 400 Bad Request errors."""

    def test_assign_variant_with_invalid_user_id(self):
        """Test that empty user_id is handled properly."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        experiment = ExperimentConfig(
            experiment_id="exp_test",
            key="test",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        # Empty user_id should raise ValueError
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            service.assign_variant("", experiment)

    def test_assign_variant_with_none_user_id(self):
        """Test that None user_id is handled properly."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        experiment = ExperimentConfig(
            experiment_id="exp_test",
            key="test",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        # None user_id should raise ValueError
        with pytest.raises(ValueError, match="user_id cannot be None"):
            service.assign_variant(None, experiment)

    def test_validate_experiment_config_with_no_variants(self):
        """Test validation fails when experiment has no variants."""
        from pydantic import ValidationError

        # Pydantic should raise ValidationError for empty variants list
        with pytest.raises(ValidationError, match="at least 2 items"):
            ExperimentConfig(
                experiment_id="exp_no_variants",
                key="test",
                status=ExperimentStatus.ACTIVE,
                variants=[]
            )

    def test_validate_experiment_config_with_single_variant(self):
        """Test validation fails when experiment has only one variant."""
        from pydantic import ValidationError

        # Pydantic should raise ValidationError for single variant
        with pytest.raises(ValidationError, match="at least 2 items"):
            ExperimentConfig(
                experiment_id="exp_single_variant",
                key="test",
                status=ExperimentStatus.ACTIVE,
                variants=[
                    VariantConfig(key="control", allocation=1.0)
                ]
            )

    def test_targeting_rules_with_invalid_operator(self):
        """Test that invalid targeting rule operators are handled."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        rules = [
            {"attribute": "country", "operator": "invalid_op", "value": "US"}
        ]
        context = {"country": "US"}

        # Should return False for invalid operator
        matches = service.evaluate_targeting_rules(rules, context)
        assert matches is False


class TestNotFoundErrors:
    """Test suite for 404 Not Found errors."""

    @patch('assignment_service.get_dynamodb_resource')
    def test_get_experiment_config_not_found(self, mock_get_resource):
        """Test handling of non-existent experiment."""
        from assignment_service import AssignmentService

        # Mock DynamoDB - no item found
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        service = AssignmentService()
        config = service.get_experiment_config("nonexistent_experiment")

        assert config is None

    @patch('utils.get_dynamodb_item')
    def test_get_assignment_not_found(self, mock_get_item):
        """Test handling of non-existent assignment."""
        from assignment_service import AssignmentService

        mock_get_item.return_value = None

        service = AssignmentService()
        assignment = service.get_assignment("user_999", "exp_nonexistent")

        assert assignment is None


class TestInternalServerErrors:
    """Test suite for 500 Internal Server errors."""

    @patch('assignment_service.get_dynamodb_resource')
    def test_get_experiment_config_dynamodb_error(self, mock_get_resource):
        """Test handling of DynamoDB errors when fetching experiment."""
        from assignment_service import AssignmentService

        # Mock DynamoDB error
        mock_table = Mock()
        mock_table.get_item.side_effect = Exception("DynamoDB connection error")
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        service = AssignmentService()
        config = service.get_experiment_config("test_experiment")

        # Should handle error gracefully and return None
        assert config is None

    @patch('utils.put_dynamodb_item')
    def test_store_assignment_dynamodb_error(self, mock_put_item):
        """Test handling of DynamoDB errors when storing assignment."""
        from assignment_service import AssignmentService
        from models import Assignment

        # Mock DynamoDB error
        mock_put_item.side_effect = Exception("DynamoDB write error")

        assignment = Assignment(
            assignment_id="assign_123",
            user_id="user_456",
            experiment_id="exp_789",
            experiment_key="test",
            variant="control",
            timestamp=datetime.now(timezone.utc)
        )

        service = AssignmentService()

        # Should handle error and return False
        with pytest.raises(Exception):
            service.store_assignment(assignment)

    @patch('utils.get_dynamodb_item')
    def test_get_assignment_dynamodb_error(self, mock_get_item):
        """Test handling of DynamoDB errors when retrieving assignment."""
        from assignment_service import AssignmentService

        # Mock DynamoDB error
        mock_get_item.side_effect = Exception("DynamoDB read error")

        service = AssignmentService()
        assignment = service.get_assignment("user_456", "exp_789")

        # Should handle error gracefully and return None
        assert assignment is None

    @patch('assignment_service.get_dynamodb_resource')
    def test_get_experiment_config_cached_error_handling(self, mock_get_resource):
        """Test that caching layer handles errors gracefully."""
        from assignment_service import AssignmentService

        # Mock DynamoDB error
        mock_table = Mock()
        mock_table.get_item.side_effect = Exception("Network timeout")
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        service = AssignmentService()
        config = service.get_experiment_config_cached("test_exp")

        # Should return None and cache the None result
        assert config is None

        # None result should be cached
        assert "test_exp" in service._experiment_cache
        assert service._experiment_cache["test_exp"]["config"] is None

    def test_hasher_error_handling(self):
        """Test handling of errors from consistent hasher."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        experiment = ExperimentConfig(
            experiment_id="exp_test",
            key="test",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        # Mock hasher to raise error
        with patch.object(service.hasher, 'assign_variant', side_effect=Exception("Hash error")):
            with pytest.raises(Exception):
                service.assign_variant("user_123", experiment)


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_traffic_allocation_zero(self):
        """Test experiment with 0% traffic allocation."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        experiment = ExperimentConfig(
            experiment_id="exp_zero_traffic",
            key="test",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ],
            traffic_allocation=0.0
        )

        # No user should be assigned
        for i in range(100):
            variant = service.assign_variant(f"user_{i}", experiment)
            assert variant is None

    def test_traffic_allocation_one(self):
        """Test experiment with 100% traffic allocation."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        experiment = ExperimentConfig(
            experiment_id="exp_full_traffic",
            key="test",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ],
            traffic_allocation=1.0
        )

        # All users should be assigned
        results = []
        for i in range(100):
            variant = service.assign_variant(f"user_{i}", experiment)
            results.append(variant)

        # Should have no None values
        assert None not in results

    def test_cache_with_expired_ttl(self):
        """Test that expired cache entries are not used."""
        from assignment_service import AssignmentService
        from time import sleep

        service = AssignmentService()
        service.cache_ttl = 0.1  # 100ms TTL

        # Add entry to cache
        service._cache_experiment_config("test_key", "test_config")

        # Verify it's valid immediately
        assert service._is_cache_valid("test_key") is True

        # Wait for expiration
        sleep(0.15)

        # Should be invalid now
        assert service._is_cache_valid("test_key") is False

    def test_context_with_none_values(self):
        """Test targeting rules with None values in context."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        rules = [
            {"attribute": "country", "operator": "equals", "value": "US"}
        ]
        context = {"country": None, "platform": "web"}

        # Should not match due to None value
        matches = service.evaluate_targeting_rules(rules, context)
        assert matches is False

    def test_empty_context(self):
        """Test targeting rules with empty context."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        rules = [
            {"attribute": "country", "operator": "equals", "value": "US"}
        ]
        context = {}

        # Should not match due to missing attribute
        matches = service.evaluate_targeting_rules(rules, context)
        assert matches is False

    @patch('utils.put_dynamodb_item')
    def test_store_assignment_without_context(self, mock_put_item):
        """Test storing assignment without user context."""
        from assignment_service import AssignmentService
        from models import Assignment

        mock_put_item.return_value = True

        assignment = Assignment(
            assignment_id="assign_123",
            user_id="user_456",
            experiment_id="exp_789",
            experiment_key="test",
            variant="control",
            timestamp=datetime.now(timezone.utc),
            context=None
        )

        service = AssignmentService()
        result = service.store_assignment(assignment)

        assert result is True

        # Verify context was not included in item
        call_kwargs = mock_put_item.call_args.kwargs
        item = call_kwargs['item']
        assert 'context' not in item

    def test_variant_allocation_sum_not_one(self):
        """Test handling of variant allocations that don't sum to 1.0."""
        from pydantic import ValidationError

        # Pydantic should raise ValidationError for allocations not summing to 1.0
        with pytest.raises(ValidationError, match="must sum to 1.0"):
            ExperimentConfig(
                experiment_id="exp_bad_allocation",
                key="test",
                status=ExperimentStatus.ACTIVE,
                variants=[
                    VariantConfig(key="control", allocation=0.4),
                    VariantConfig(key="treatment", allocation=0.5)
                ]
            )
