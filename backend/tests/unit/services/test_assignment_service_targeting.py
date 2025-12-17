"""
Unit tests for assignment service targeting integration.

This module tests the integration between the assignment service and the enhanced
rules engine for targeted experiment assignments.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from uuid import UUID, uuid4

from backend.app.services.assignment_service import AssignmentService
from backend.app.models.experiment import Experiment, Variant, ExperimentStatus
from backend.app.models.assignment import Assignment
from backend.app.schemas.targeting_rule import (
    Condition,
    RuleGroup,
    TargetingRule,
    TargetingRules,
    LogicalOperator,
    OperatorType,
    AttributeType,
)


class TestAssignmentServiceTargeting:
    """Tests for targeted assignment functionality."""

    def setup_method(self):
        """Setup test data and mocks."""
        self.mock_db = Mock()
        self.mock_event_service = Mock()
        self.service = AssignmentService(self.mock_db)
        self.service.event_service = self.mock_event_service

        # Create test experiment
        self.experiment_id = uuid4()
        self.variant_a_id = uuid4()
        self.variant_b_id = uuid4()

        self.experiment = Mock(spec=Experiment)
        self.experiment.id = self.experiment_id
        self.experiment.status = ExperimentStatus.ACTIVE
        self.experiment.variants = [
            Mock(id=self.variant_a_id, traffic_allocation=50),
            Mock(id=self.variant_b_id, traffic_allocation=50)
        ]

        # Create targeting rules
        self.targeting_rules = {
            "version": "1.0",
            "rules": [
                {
                    "id": "premium_users",
                    "name": "Premium Users",
                    "rule": {
                        "operator": "and",
                        "conditions": [
                            {
                                "attribute": "subscription_tier",
                                "operator": "eq",
                                "value": "premium"
                            }
                        ]
                    },
                    "rollout_percentage": 100,
                    "priority": 1
                }
            ]
        }

    def test_assign_user_with_targeting_success(self):
        """Test successful assignment with targeting rules."""
        # Setup mocks
        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = self.experiment
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # Add targeting rules to experiment
        self.experiment.targeting_rules = json.dumps(self.targeting_rules)

        # Mock assignment creation
        mock_assignment = Mock(spec=Assignment)
        mock_assignment.id = uuid4()
        mock_assignment.user_id = "test-user"
        mock_assignment.experiment_id = self.experiment_id
        mock_assignment.variant_id = self.variant_a_id

        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()

        # Mock get_assignment to return formatted assignment
        assignment_dict = {
            "id": str(mock_assignment.id),
            "user_id": "test-user",
            "experiment_id": str(self.experiment_id),
            "variant_id": str(self.variant_a_id),
            "variant_name": "Variant A",
            "is_control": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        with patch.object(self.service, 'get_assignment', return_value=assignment_dict):
            with patch.object(self.service, '_hash_user_to_variant', return_value=self.variant_a_id):
                # User context that matches targeting rules
                user_context = {
                    "user_id": "test-user",
                    "subscription_tier": "premium",
                    "country": "US"
                }

                result = self.service.assign_user_with_targeting(
                    user_id="test-user",
                    experiment_id=self.experiment_id,
                    user_context=user_context
                )

                # Verify assignment was created
                assert result is not None
                assert result["user_id"] == "test-user"
                assert result["experiment_id"] == str(self.experiment_id)
                assert result["targeting_matched"] is True
                assert result["targeting_rule_id"] == "premium_users"
                assert result["user_context_validated"] is True

                # Verify database operations
                self.mock_db.add.assert_called_once()
                self.mock_db.commit.assert_called_once()

    def test_assign_user_with_targeting_no_match(self):
        """Test assignment when user doesn't match targeting rules."""
        # Setup mocks
        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = self.experiment
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # Add targeting rules to experiment
        self.experiment.targeting_rules = json.dumps(self.targeting_rules)

        # User context that doesn't match targeting rules
        user_context = {
            "user_id": "test-user",
            "subscription_tier": "basic",  # Doesn't match premium requirement
            "country": "US"
        }

        result = self.service.assign_user_with_targeting(
            user_id="test-user",
            experiment_id=self.experiment_id,
            user_context=user_context
        )

        # Verify no assignment was created
        assert result is not None
        assert result["assignment"] is None
        assert result["targeting_matched"] is False
        assert result["targeting_rule_id"] is None
        assert "No targeting rules matched" in result["reason"]

        # Verify no database operations for assignment creation
        self.mock_db.add.assert_not_called()

    def test_assign_user_with_no_targeting_rules(self):
        """Test assignment when experiment has no targeting rules."""
        # Setup mocks
        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = self.experiment
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # No targeting rules on experiment
        self.experiment.targeting_rules = None

        # Mock assignment creation
        mock_assignment = Mock(spec=Assignment)
        mock_assignment.id = uuid4()
        mock_assignment.user_id = "test-user"
        mock_assignment.experiment_id = self.experiment_id
        mock_assignment.variant_id = self.variant_a_id

        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()

        # Mock get_assignment to return formatted assignment
        assignment_dict = {
            "id": str(mock_assignment.id),
            "user_id": "test-user",
            "experiment_id": str(self.experiment_id),
            "variant_id": str(self.variant_a_id),
        }

        with patch.object(self.service, 'get_assignment', return_value=assignment_dict):
            with patch.object(self.service, '_hash_user_to_variant', return_value=self.variant_a_id):
                user_context = {
                    "user_id": "test-user",
                    "country": "US"
                }

                result = self.service.assign_user_with_targeting(
                    user_id="test-user",
                    experiment_id=self.experiment_id,
                    user_context=user_context
                )

                # Should assign user since no targeting rules means all users are eligible
                assert result is not None
                assert result["user_id"] == "test-user"
                assert result["targeting_matched"] is True
                assert result["targeting_rule_id"] is None

    def test_assign_user_with_existing_assignment(self):
        """Test assignment when user already has an assignment."""
        # Setup mocks for existing assignment
        existing_assignment = Mock(spec=Assignment)
        existing_assignment.id = uuid4()
        existing_assignment.user_id = "test-user"
        existing_assignment.experiment_id = self.experiment_id
        existing_assignment.variant_id = self.variant_b_id

        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = self.experiment
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = existing_assignment

        # Mock get_assignment to return existing assignment
        assignment_dict = {
            "id": str(existing_assignment.id),
            "user_id": "test-user",
            "experiment_id": str(self.experiment_id),
            "variant_id": str(self.variant_b_id),
        }

        with patch.object(self.service, 'get_assignment', return_value=assignment_dict):
            user_context = {
                "user_id": "test-user",
                "subscription_tier": "premium"
            }

            result = self.service.assign_user_with_targeting(
                user_id="test-user",
                experiment_id=self.experiment_id,
                user_context=user_context
            )

            # Should return existing assignment
            assert result is not None
            assert result["variant_id"] == str(self.variant_b_id)
            assert result["targeting_matched"] is True
            assert result["targeting_rule_id"] == "existing_assignment"

            # Should not create new assignment
            self.mock_db.add.assert_not_called()

    def test_assign_user_with_inactive_experiment(self):
        """Test assignment fails for inactive experiment."""
        # Setup mock for inactive experiment
        inactive_experiment = Mock(spec=Experiment)
        inactive_experiment.id = self.experiment_id
        inactive_experiment.status = ExperimentStatus.DRAFT

        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = inactive_experiment

        user_context = {"user_id": "test-user"}

        with pytest.raises(ValueError) as exc_info:
            self.service.assign_user_with_targeting(
                user_id="test-user",
                experiment_id=self.experiment_id,
                user_context=user_context
            )

        assert "Cannot assign users to experiment with status" in str(exc_info.value)

    def test_assign_user_with_nonexistent_experiment(self):
        """Test assignment fails for nonexistent experiment."""
        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None

        user_context = {"user_id": "test-user"}

        with pytest.raises(ValueError) as exc_info:
            self.service.assign_user_with_targeting(
                user_id="test-user",
                experiment_id=self.experiment_id,
                user_context=user_context
            )

        assert "not found" in str(exc_info.value)

    def test_evaluate_experiment_targeting_with_complex_rules(self):
        """Test targeting evaluation with complex rules."""
        # Create complex targeting rules
        complex_rules = {
            "version": "1.0",
            "rules": [
                {
                    "id": "complex_rule",
                    "name": "Complex Targeting",
                    "rule": {
                        "operator": "or",
                        "groups": [
                            {
                                "operator": "and",
                                "conditions": [
                                    {
                                        "attribute": "country",
                                        "operator": "eq",
                                        "value": "US"
                                    },
                                    {
                                        "attribute": "subscription_tier",
                                        "operator": "eq",
                                        "value": "premium"
                                    }
                                ]
                            },
                            {
                                "operator": "and",
                                "conditions": [
                                    {
                                        "attribute": "app_version",
                                        "operator": "semantic_version",
                                        "value": "1.2.0"
                                    }
                                ]
                            }
                        ]
                    },
                    "rollout_percentage": 100,
                    "priority": 1
                }
            ]
        }

        self.experiment.targeting_rules = json.dumps(complex_rules)

        # Test user that matches first group (US + premium)
        user_context_1 = {
            "user_id": "user1",
            "country": "US",
            "subscription_tier": "premium",
            "app_version": "1.0.0"
        }

        result = self.service._evaluate_experiment_targeting(
            self.experiment, user_context_1, validate_attributes=False
        )

        assert result["eligible"] is True
        assert result["rule_id"] == "complex_rule"

        # Test user that matches second group (app version)
        user_context_2 = {
            "user_id": "user2",
            "country": "CA",
            "subscription_tier": "basic",
            "app_version": "1.3.0"
        }

        result = self.service._evaluate_experiment_targeting(
            self.experiment, user_context_2, validate_attributes=False
        )

        assert result["eligible"] is True
        assert result["rule_id"] == "complex_rule"

        # Test user that matches neither group
        user_context_3 = {
            "user_id": "user3",
            "country": "CA",
            "subscription_tier": "basic",
            "app_version": "1.0.0"
        }

        result = self.service._evaluate_experiment_targeting(
            self.experiment, user_context_3, validate_attributes=False
        )

        assert result["eligible"] is False
        assert result["rule_id"] is None

    def test_targeting_performance_stats(self):
        """Test targeting performance statistics collection."""
        # Clear existing metrics
        self.service.clear_targeting_metrics()

        # Setup mocks
        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = self.experiment
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        self.experiment.targeting_rules = json.dumps(self.targeting_rules)

        # Mock assignment creation and get_assignment
        with patch.object(self.service, 'get_assignment') as mock_get_assignment:
            with patch.object(self.service, '_hash_user_to_variant', return_value=self.variant_a_id):
                mock_get_assignment.return_value = {
                    "id": str(uuid4()),
                    "user_id": "test-user",
                    "experiment_id": str(self.experiment_id),
                    "variant_id": str(self.variant_a_id),
                }

                # Perform multiple assignments
                for i in range(5):
                    user_context = {
                        "user_id": f"user-{i}",
                        "subscription_tier": "premium"
                    }

                    self.service.assign_user_with_targeting(
                        user_id=f"user-{i}",
                        experiment_id=self.experiment_id,
                        user_context=user_context
                    )

                # Get performance stats
                stats = self.service.get_targeting_performance_stats()

                assert stats["total_evaluations"] == 5
                assert stats["avg_evaluation_time_ms"] > 0
                assert stats["match_rate"] > 0

    def test_targeting_with_validation_errors(self):
        """Test targeting behavior with validation errors."""
        # Create rules with specific attribute types
        rules_with_validation = {
            "version": "1.0",
            "rules": [
                {
                    "id": "validated_rule",
                    "rule": {
                        "operator": "and",
                        "conditions": [
                            {
                                "attribute": "app_version",
                                "operator": "semantic_version",
                                "value": "1.2.0",
                                "attribute_type": "semantic_version"
                            }
                        ]
                    },
                    "rollout_percentage": 100,
                    "priority": 1
                }
            ]
        }

        self.experiment.targeting_rules = json.dumps(rules_with_validation)

        # Setup mocks
        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = self.experiment
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        # User context with invalid semantic version
        user_context = {
            "user_id": "test-user",
            "app_version": "invalid-version"  # Invalid semantic version format
        }

        result = self.service.assign_user_with_targeting(
            user_id="test-user",
            experiment_id=self.experiment_id,
            user_context=user_context,
            validate_attributes=True
        )

        # Should not assign due to validation error
        assert result["assignment"] is None
        assert result["targeting_matched"] is False
        assert result["user_context_validated"] is False

    def test_exposure_tracking_with_targeting_info(self):
        """Test that exposure events include targeting information."""
        # Setup mocks
        self.mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = self.experiment
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        self.experiment.targeting_rules = json.dumps(self.targeting_rules)

        # Mock assignment creation
        assignment_dict = {
            "id": str(uuid4()),
            "user_id": "test-user",
            "experiment_id": str(self.experiment_id),
            "variant_id": str(self.variant_a_id),
        }

        with patch.object(self.service, 'get_assignment', return_value=assignment_dict):
            with patch.object(self.service, '_hash_user_to_variant', return_value=self.variant_a_id):
                user_context = {
                    "user_id": "test-user",
                    "subscription_tier": "premium",
                    "country": "US"
                }

                self.service.assign_user_with_targeting(
                    user_id="test-user",
                    experiment_id=self.experiment_id,
                    user_context=user_context,
                    track_exposure=True
                )

                # Verify exposure event was tracked with targeting info
                self.mock_event_service.track_exposure.assert_called_once()

                call_args = self.mock_event_service.track_exposure.call_args
                exposure_properties = call_args[1]['properties']

                assert exposure_properties['targeting_rule_id'] == 'premium_users'
                assert exposure_properties['targeting_matched'] is True
                assert exposure_properties['subscription_tier'] == 'premium'