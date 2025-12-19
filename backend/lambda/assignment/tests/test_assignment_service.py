"""
Unit tests for Assignment Service.

Tests the core assignment logic including consistent hashing, config validation,
and variant assignment.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from models import ExperimentConfig, VariantConfig, ExperimentStatus, Assignment


class TestAssignmentService:
    """Test suite for Assignment Service core logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_experiment_config = ExperimentConfig(
            experiment_id="exp_123",
            key="checkout_redesign",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ],
            traffic_allocation=1.0
        )

    # Day 1, Task 2.1: Tests for consistent hashing integration
    def test_assign_variant_returns_consistent_result(self):
        """Test that same user gets same variant across multiple calls."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        user_id = "user_123"

        # Call multiple times
        results = [
            service.assign_variant(user_id, self.valid_experiment_config)
            for _ in range(10)
        ]

        # All results should be identical
        assert len(set(results)) == 1, "Same user should get consistent variant"
        assert results[0] in ["control", "treatment"]

    def test_assign_variant_respects_traffic_allocation(self):
        """Test that traffic allocation excludes correct percentage."""
        from assignment_service import AssignmentService

        # Create experiment with 50% traffic allocation
        experiment = ExperimentConfig(
            experiment_id="exp_traffic",
            key="test_traffic",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ],
            traffic_allocation=0.5
        )

        service = AssignmentService()
        results = []

        for i in range(1000):
            variant = service.assign_variant(f"user_{i}", experiment)
            results.append(variant)

        # Count non-None assignments
        assigned = [r for r in results if r is not None]
        assignment_rate = len(assigned) / len(results)

        # Should be within ±5% of 50%
        assert 0.45 <= assignment_rate <= 0.55, \
            f"Assignment rate: {assignment_rate:.2%} (expected ~50%)"

    def test_assign_variant_distribution_matches_allocation(self):
        """Test that variant distribution matches allocation percentages."""
        from assignment_service import AssignmentService

        # Create experiment with 70/30 split
        experiment = ExperimentConfig(
            experiment_id="exp_uneven",
            key="test_uneven",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.7),
                VariantConfig(key="treatment", allocation=0.3)
            ],
            traffic_allocation=1.0
        )

        service = AssignmentService()
        results = []

        for i in range(1000):
            variant = service.assign_variant(f"user_{i}", experiment)
            results.append(variant)

        control_pct = results.count("control") / len(results)
        treatment_pct = results.count("treatment") / len(results)

        # Should be within ±5% of target allocation
        assert 0.65 <= control_pct <= 0.75, \
            f"Control: {control_pct:.2%} (expected ~70%)"
        assert 0.25 <= treatment_pct <= 0.35, \
            f"Treatment: {treatment_pct:.2%} (expected ~30%)"

    def test_assign_variant_with_three_variants(self):
        """Test assignment with three variants."""
        from assignment_service import AssignmentService

        experiment = ExperimentConfig(
            experiment_id="exp_three",
            key="test_three",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.33),
                VariantConfig(key="variant_a", allocation=0.33),
                VariantConfig(key="variant_b", allocation=0.34)
            ],
            traffic_allocation=1.0
        )

        service = AssignmentService()
        results = []

        for i in range(1000):
            variant = service.assign_variant(f"user_{i}", experiment)
            results.append(variant)

        # Check all three variants are assigned
        unique_variants = set(results)
        assert len(unique_variants) == 3
        assert "control" in unique_variants
        assert "variant_a" in unique_variants
        assert "variant_b" in unique_variants

    # Day 1, Task 2.3: Tests for experiment config validation
    def test_validate_experiment_config_active_experiment(self):
        """Test that ACTIVE experiments pass validation."""
        from assignment_service import AssignmentService

        service = AssignmentService()

        # Should not raise exception
        is_valid = service.validate_experiment_config(self.valid_experiment_config)
        assert is_valid is True

    def test_validate_experiment_config_draft_experiment_rejected(self):
        """Test that DRAFT experiments are rejected."""
        from assignment_service import AssignmentService

        draft_experiment = ExperimentConfig(
            experiment_id="exp_draft",
            key="test_draft",
            status=ExperimentStatus.DRAFT,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        service = AssignmentService()
        is_valid = service.validate_experiment_config(draft_experiment)

        assert is_valid is False

    def test_validate_experiment_config_paused_experiment_rejected(self):
        """Test that PAUSED experiments are rejected."""
        from assignment_service import AssignmentService

        paused_experiment = ExperimentConfig(
            experiment_id="exp_paused",
            key="test_paused",
            status=ExperimentStatus.PAUSED,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        service = AssignmentService()
        is_valid = service.validate_experiment_config(paused_experiment)

        assert is_valid is False

    def test_validate_experiment_config_completed_experiment_rejected(self):
        """Test that COMPLETED experiments are rejected."""
        from assignment_service import AssignmentService

        completed_experiment = ExperimentConfig(
            experiment_id="exp_completed",
            key="test_completed",
            status=ExperimentStatus.COMPLETED,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        service = AssignmentService()
        is_valid = service.validate_experiment_config(completed_experiment)

        assert is_valid is False

    @patch('assignment_service.get_dynamodb_resource')
    def test_get_experiment_config_returns_config(self, mock_get_resource):
        """Test fetching experiment config from DynamoDB."""
        from assignment_service import AssignmentService

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'experiment_id': 'exp_123',
                'key': 'checkout_test',
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
        config = service.get_experiment_config("checkout_test")

        assert config is not None
        assert config.experiment_id == "exp_123"
        assert config.key == "checkout_test"
        assert config.status == ExperimentStatus.ACTIVE

    @patch('assignment_service.get_dynamodb_resource')
    def test_get_experiment_config_missing_experiment_returns_none(self, mock_get_resource):
        """Test that missing experiment returns None."""
        from assignment_service import AssignmentService

        # Mock DynamoDB response - no item found
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        service = AssignmentService()
        config = service.get_experiment_config("nonexistent_experiment")

        assert config is None

    @patch('assignment_service.get_dynamodb_resource')
    def test_get_experiment_config_handles_dynamodb_errors(self, mock_get_resource):
        """Test that DynamoDB errors are handled gracefully."""
        from assignment_service import AssignmentService

        # Mock DynamoDB error
        mock_table = Mock()
        mock_table.get_item.side_effect = Exception("DynamoDB error")
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        service = AssignmentService()
        config = service.get_experiment_config("test_experiment")

        assert config is None

    def test_create_assignment_object(self):
        """Test creating Assignment object with correct fields."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        user_id = "user_456"
        variant = "treatment"

        assignment = service.create_assignment(
            user_id=user_id,
            experiment_config=self.valid_experiment_config,
            variant=variant
        )

        assert assignment.user_id == user_id
        assert assignment.experiment_id == "exp_123"
        assert assignment.experiment_key == "checkout_redesign"
        assert assignment.variant == variant
        assert isinstance(assignment.timestamp, datetime)

    def test_create_assignment_with_context(self):
        """Test creating assignment with user context."""
        from assignment_service import AssignmentService

        service = AssignmentService()
        context = {"country": "US", "platform": "web"}

        assignment = service.create_assignment(
            user_id="user_789",
            experiment_config=self.valid_experiment_config,
            variant="control",
            context=context
        )

        assert assignment.context == context
