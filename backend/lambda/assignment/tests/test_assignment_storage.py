"""
Unit tests for Assignment Storage (Day 2).

Tests DynamoDB assignment storage and retrieval logic.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

from models import ExperimentConfig, VariantConfig, ExperimentStatus, Assignment


class TestAssignmentStorage:
    """Test suite for Assignment Storage in DynamoDB."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_assignment = Assignment(
            assignment_id="assign_abc123",
            user_id="user_456",
            experiment_id="exp_789",
            experiment_key="checkout_test",
            variant="treatment",
            timestamp=datetime.now(timezone.utc)
        )

    # Day 2, Task 2.5: Tests for assignment storage
    @patch('utils.put_dynamodb_item')
    def test_store_assignment_success(self, mock_put_item):
        """Test successful assignment storage."""
        from assignment_service import AssignmentService

        mock_put_item.return_value = True

        service = AssignmentService()
        result = service.store_assignment(self.valid_assignment)

        assert result is True
        mock_put_item.assert_called_once()

        # Verify the item being stored has correct structure
        assert mock_put_item.called
        call_kwargs = mock_put_item.call_args.kwargs
        assert 'item' in call_kwargs
        item = call_kwargs['item']
        assert item['user_id'] == "user_456"
        assert item['experiment_id'] == "exp_789"
        assert item['variant'] == "treatment"

    @patch('utils.put_dynamodb_item')
    def test_store_assignment_with_ttl(self, mock_put_item):
        """Test that assignments are stored with TTL for cleanup."""
        from assignment_service import AssignmentService

        mock_put_item.return_value = True

        service = AssignmentService()
        service.store_assignment(self.valid_assignment)

        # Verify TTL is set (90 days from now)
        call_kwargs = mock_put_item.call_args.kwargs
        item = call_kwargs['item']
        assert 'ttl' in item
        assert isinstance(item['ttl'], (int, float))

    @patch('utils.put_dynamodb_item')
    def test_store_assignment_prevents_duplicates(self, mock_put_item):
        """Test that duplicate assignments use conditional writes."""
        from assignment_service import AssignmentService

        mock_put_item.return_value = True

        service = AssignmentService()
        service.store_assignment(self.valid_assignment)

        # Verify condition expression is used
        call_kwargs = mock_put_item.call_args.kwargs
        assert 'condition_expression' in call_kwargs

    @patch('utils.put_dynamodb_item')
    def test_store_assignment_handles_errors(self, mock_put_item):
        """Test that storage errors are handled gracefully."""
        from assignment_service import AssignmentService

        mock_put_item.return_value = False

        service = AssignmentService()
        result = service.store_assignment(self.valid_assignment)

        assert result is False

    @patch('utils.put_dynamodb_item')
    def test_store_assignment_with_context(self, mock_put_item):
        """Test storing assignment with user context."""
        from assignment_service import AssignmentService

        context = {"country": "US", "platform": "web"}
        assignment = Assignment(
            assignment_id="assign_123",
            user_id="user_456",
            experiment_id="exp_789",
            experiment_key="test",
            variant="control",
            context=context
        )

        mock_put_item.return_value = True

        service = AssignmentService()
        service.store_assignment(assignment)

        call_kwargs = mock_put_item.call_args.kwargs
        item = call_kwargs['item']
        assert 'context' in item
        assert item['context'] == context

    # Day 2, Task 2.7: Tests for assignment retrieval
    @patch('utils.get_dynamodb_item')
    def test_get_assignment_existing_returns_assignment(self, mock_get_item):
        """Test retrieving existing assignment returns correct data."""
        from assignment_service import AssignmentService

        # Mock DynamoDB response
        mock_get_item.return_value = {
            'assignment_id': 'assign_abc123',
            'user_id': 'user_456',
            'experiment_id': 'exp_789',
            'experiment_key': 'checkout_test',
            'variant': 'treatment',
            'timestamp': '2025-12-18T10:30:00Z'
        }

        service = AssignmentService()
        assignment = service.get_assignment("user_456", "exp_789")

        assert assignment is not None
        assert assignment.user_id == "user_456"
        assert assignment.experiment_id == "exp_789"
        assert assignment.variant == "treatment"

    @patch('utils.get_dynamodb_item')
    def test_get_assignment_not_found_returns_none(self, mock_get_item):
        """Test that missing assignment returns None."""
        from assignment_service import AssignmentService

        mock_get_item.return_value = None

        service = AssignmentService()
        assignment = service.get_assignment("user_999", "exp_nonexistent")

        assert assignment is None

    @patch('utils.get_dynamodb_item')
    def test_get_assignment_handles_errors(self, mock_get_item):
        """Test that retrieval errors are handled gracefully."""
        from assignment_service import AssignmentService

        mock_get_item.side_effect = Exception("DynamoDB error")

        service = AssignmentService()
        assignment = service.get_assignment("user_456", "exp_789")

        assert assignment is None

    @patch('utils.get_dynamodb_item')
    @patch('assignment_service.AssignmentService.assign_variant')
    @patch('assignment_service.AssignmentService.store_assignment')
    def test_get_or_create_assignment_existing(
        self, mock_store, mock_assign, mock_get_item
    ):
        """Test get_or_create returns existing assignment."""
        from assignment_service import AssignmentService

        # Mock existing assignment
        mock_get_item.return_value = {
            'assignment_id': 'assign_abc123',
            'user_id': 'user_456',
            'experiment_id': 'exp_789',
            'experiment_key': 'checkout_test',
            'variant': 'treatment',
            'timestamp': '2025-12-18T10:30:00Z'
        }

        experiment_config = ExperimentConfig(
            experiment_id="exp_789",
            key="checkout_test",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        service = AssignmentService()
        assignment = service.get_or_create_assignment("user_456", experiment_config)

        assert assignment is not None
        assert assignment.variant == "treatment"
        # Should not create new assignment
        mock_assign.assert_not_called()
        mock_store.assert_not_called()

    @patch('utils.get_dynamodb_item')
    @patch('assignment_service.AssignmentService.assign_variant')
    @patch('assignment_service.AssignmentService.store_assignment')
    def test_get_or_create_assignment_new(
        self, mock_store, mock_assign, mock_get_item
    ):
        """Test get_or_create creates new assignment when none exists."""
        from assignment_service import AssignmentService

        # Mock no existing assignment
        mock_get_item.return_value = None
        mock_assign.return_value = "control"
        mock_store.return_value = True

        experiment_config = ExperimentConfig(
            experiment_id="exp_789",
            key="checkout_test",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        service = AssignmentService()
        assignment = service.get_or_create_assignment("user_999", experiment_config)

        assert assignment is not None
        assert assignment.variant == "control"
        # Should create new assignment
        mock_assign.assert_called_once()
        mock_store.assert_called_once()

    @patch('utils.get_dynamodb_item')
    @patch('assignment_service.AssignmentService.assign_variant')
    def test_get_or_create_assignment_excluded_by_traffic(
        self, mock_assign, mock_get_item
    ):
        """Test get_or_create handles users excluded by traffic allocation."""
        from assignment_service import AssignmentService

        # Mock no existing assignment
        mock_get_item.return_value = None
        # User excluded by traffic allocation
        mock_assign.return_value = None

        experiment_config = ExperimentConfig(
            experiment_id="exp_789",
            key="checkout_test",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ],
            traffic_allocation=0.5
        )

        service = AssignmentService()
        assignment = service.get_or_create_assignment("user_excluded", experiment_config)

        assert assignment is None
