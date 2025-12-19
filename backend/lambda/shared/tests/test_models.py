"""
Unit tests for Pydantic data models.

Tests all shared data models for validation and serialization.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from pydantic import ValidationError

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import (
    Assignment,
    VariantConfig,
    ExperimentConfig,
    ExperimentStatus,
    FeatureFlagConfig,
    EventData,
    LambdaResponse,
)


class TestAssignment:
    """Test suite for Assignment model."""

    def test_valid_assignment_creation(self):
        """Test creating a valid assignment."""
        assignment = Assignment(
            assignment_id="assign_123",
            user_id="user_456",
            experiment_id="exp_789",
            experiment_key="checkout_redesign",
            variant="treatment"
        )

        assert assignment.assignment_id == "assign_123"
        assert assignment.user_id == "user_456"
        assert assignment.experiment_id == "exp_789"
        assert assignment.experiment_key == "checkout_redesign"
        assert assignment.variant == "treatment"
        assert isinstance(assignment.timestamp, datetime)

    def test_assignment_with_context(self):
        """Test assignment with user context."""
        context = {"country": "US", "platform": "web"}
        assignment = Assignment(
            assignment_id="assign_123",
            user_id="user_456",
            experiment_id="exp_789",
            experiment_key="test_exp",
            variant="control",
            context=context
        )

        assert assignment.context == context

    def test_assignment_missing_required_fields(self):
        """Test that missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            Assignment(user_id="user_123")

    def test_assignment_serialization(self):
        """Test that assignment can be serialized to dict."""
        assignment = Assignment(
            assignment_id="assign_123",
            user_id="user_456",
            experiment_id="exp_789",
            experiment_key="test_exp",
            variant="treatment"
        )

        data = assignment.model_dump()
        assert isinstance(data, dict)
        assert data["assignment_id"] == "assign_123"
        assert "timestamp" in data


class TestVariantConfig:
    """Test suite for VariantConfig model."""

    def test_valid_variant_config(self):
        """Test creating a valid variant config."""
        variant = VariantConfig(
            key="treatment",
            allocation=0.5
        )

        assert variant.key == "treatment"
        assert variant.allocation == 0.5
        assert variant.payload is None

    def test_variant_with_payload(self):
        """Test variant with payload data."""
        payload = {"button_color": "blue", "size": "large"}
        variant = VariantConfig(
            key="variant_a",
            allocation=0.33,
            payload=payload
        )

        assert variant.payload == payload

    def test_invalid_allocation_too_high(self):
        """Test that allocation > 1.0 raises ValidationError."""
        with pytest.raises(ValidationError):
            VariantConfig(key="control", allocation=1.5)

    def test_invalid_allocation_negative(self):
        """Test that negative allocation raises ValidationError."""
        with pytest.raises(ValidationError):
            VariantConfig(key="control", allocation=-0.1)

    def test_allocation_boundary_values(self):
        """Test allocation boundary values (0.0 and 1.0)."""
        variant_zero = VariantConfig(key="v1", allocation=0.0)
        variant_one = VariantConfig(key="v2", allocation=1.0)

        assert variant_zero.allocation == 0.0
        assert variant_one.allocation == 1.0


class TestExperimentConfig:
    """Test suite for ExperimentConfig model."""

    def test_valid_experiment_config(self):
        """Test creating a valid experiment config."""
        variants = [
            VariantConfig(key="control", allocation=0.5),
            VariantConfig(key="treatment", allocation=0.5)
        ]

        experiment = ExperimentConfig(
            experiment_id="exp_123",
            key="checkout_test",
            status=ExperimentStatus.ACTIVE,
            variants=variants
        )

        assert experiment.experiment_id == "exp_123"
        assert experiment.key == "checkout_test"
        assert experiment.status == ExperimentStatus.ACTIVE
        assert len(experiment.variants) == 2
        assert experiment.traffic_allocation == 1.0

    def test_experiment_with_traffic_allocation(self):
        """Test experiment with custom traffic allocation."""
        variants = [
            VariantConfig(key="control", allocation=0.5),
            VariantConfig(key="treatment", allocation=0.5)
        ]

        experiment = ExperimentConfig(
            experiment_id="exp_123",
            key="test",
            status=ExperimentStatus.ACTIVE,
            variants=variants,
            traffic_allocation=0.5
        )

        assert experiment.traffic_allocation == 0.5

    def test_experiment_with_targeting_rules(self):
        """Test experiment with targeting rules."""
        variants = [
            VariantConfig(key="control", allocation=0.5),
            VariantConfig(key="treatment", allocation=0.5)
        ]
        rules = [{"attribute": "country", "operator": "equals", "value": "US"}]

        experiment = ExperimentConfig(
            experiment_id="exp_123",
            key="test",
            status=ExperimentStatus.ACTIVE,
            variants=variants,
            targeting_rules=rules
        )

        assert experiment.targeting_rules == rules

    def test_variant_allocations_must_sum_to_one(self):
        """Test that variant allocations must sum to ~1.0."""
        variants = [
            VariantConfig(key="control", allocation=0.4),
            VariantConfig(key="treatment", allocation=0.4)
        ]

        with pytest.raises(ValidationError, match="Variant allocations must sum to 1.0"):
            ExperimentConfig(
                experiment_id="exp_123",
                key="test",
                status=ExperimentStatus.ACTIVE,
                variants=variants
            )

    def test_variant_allocations_sum_with_tolerance(self):
        """Test that variant allocations sum allows small tolerance."""
        # 0.995 should be accepted (within 0.99-1.01 range)
        variants = [
            VariantConfig(key="control", allocation=0.495),
            VariantConfig(key="treatment", allocation=0.5)
        ]

        experiment = ExperimentConfig(
            experiment_id="exp_123",
            key="test",
            status=ExperimentStatus.ACTIVE,
            variants=variants
        )

        assert experiment is not None

    def test_minimum_two_variants_required(self):
        """Test that at least 2 variants are required."""
        variants = [VariantConfig(key="control", allocation=1.0)]

        with pytest.raises(ValidationError):
            ExperimentConfig(
                experiment_id="exp_123",
                key="test",
                status=ExperimentStatus.ACTIVE,
                variants=variants
            )

    def test_experiment_status_enum_values(self):
        """Test all experiment status enum values."""
        variants = [
            VariantConfig(key="control", allocation=0.5),
            VariantConfig(key="treatment", allocation=0.5)
        ]

        for status in [ExperimentStatus.DRAFT, ExperimentStatus.ACTIVE,
                       ExperimentStatus.PAUSED, ExperimentStatus.COMPLETED]:
            experiment = ExperimentConfig(
                experiment_id="exp_123",
                key="test",
                status=status,
                variants=variants
            )
            assert experiment.status == status


class TestFeatureFlagConfig:
    """Test suite for FeatureFlagConfig model."""

    def test_valid_feature_flag_config(self):
        """Test creating a valid feature flag config."""
        flag = FeatureFlagConfig(
            flag_id="flag_123",
            key="new_checkout",
            enabled=True,
            rollout_percentage=50.0
        )

        assert flag.flag_id == "flag_123"
        assert flag.key == "new_checkout"
        assert flag.enabled is True
        assert flag.rollout_percentage == 50.0

    def test_feature_flag_with_targeting_rules(self):
        """Test feature flag with targeting rules."""
        rules = [{"attribute": "beta_user", "operator": "equals", "value": True}]

        flag = FeatureFlagConfig(
            flag_id="flag_123",
            key="beta_feature",
            enabled=True,
            targeting_rules=rules
        )

        assert flag.targeting_rules == rules

    def test_feature_flag_with_variants(self):
        """Test feature flag with multiple variants."""
        variants = [
            VariantConfig(key="small", allocation=0.5),
            VariantConfig(key="large", allocation=0.5)
        ]

        flag = FeatureFlagConfig(
            flag_id="flag_123",
            key="button_size",
            enabled=True,
            variants=variants,
            default_variant="small"
        )

        assert len(flag.variants) == 2
        assert flag.default_variant == "small"

    def test_rollout_percentage_boundaries(self):
        """Test rollout percentage boundary values."""
        flag_0 = FeatureFlagConfig(
            flag_id="flag_1", key="test", rollout_percentage=0.0
        )
        flag_100 = FeatureFlagConfig(
            flag_id="flag_2", key="test", rollout_percentage=100.0
        )

        assert flag_0.rollout_percentage == 0.0
        assert flag_100.rollout_percentage == 100.0

    def test_invalid_rollout_percentage(self):
        """Test that invalid rollout percentage raises ValidationError."""
        with pytest.raises(ValidationError):
            FeatureFlagConfig(
                flag_id="flag_123",
                key="test",
                rollout_percentage=150.0
            )

        with pytest.raises(ValidationError):
            FeatureFlagConfig(
                flag_id="flag_123",
                key="test",
                rollout_percentage=-10.0
            )

    def test_disabled_flag_defaults(self):
        """Test default values for disabled flag."""
        flag = FeatureFlagConfig(
            flag_id="flag_123",
            key="test_flag"
        )

        assert flag.enabled is False
        assert flag.rollout_percentage == 0.0
        assert flag.targeting_rules is None
        assert flag.variants is None


class TestEventData:
    """Test suite for EventData model."""

    def test_valid_event_data(self):
        """Test creating valid event data."""
        event = EventData(
            event_id="evt_123",
            event_type="conversion",
            user_id="user_456"
        )

        assert event.event_id == "evt_123"
        assert event.event_type == "conversion"
        assert event.user_id == "user_456"
        assert isinstance(event.timestamp, datetime)

    def test_event_with_experiment_id(self):
        """Test event associated with experiment."""
        event = EventData(
            event_id="evt_123",
            event_type="click",
            user_id="user_456",
            experiment_id="exp_789"
        )

        assert event.experiment_id == "exp_789"

    def test_event_with_properties(self):
        """Test event with custom properties."""
        properties = {"revenue": 99.99, "item_count": 3}

        event = EventData(
            event_id="evt_123",
            event_type="purchase",
            user_id="user_456",
            properties=properties
        )

        assert event.properties == properties

    def test_event_with_metadata(self):
        """Test event with metadata."""
        metadata = {"source": "mobile_app", "version": "1.2.3"}

        event = EventData(
            event_id="evt_123",
            event_type="page_view",
            user_id="user_456",
            metadata=metadata
        )

        assert event.metadata == metadata

    def test_event_missing_required_fields(self):
        """Test that missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            EventData(event_id="evt_123")

    def test_event_serialization(self):
        """Test that event can be serialized."""
        event = EventData(
            event_id="evt_123",
            event_type="conversion",
            user_id="user_456"
        )

        data = event.model_dump()
        assert isinstance(data, dict)
        assert data["event_id"] == "evt_123"


class TestLambdaResponse:
    """Test suite for LambdaResponse model."""

    def test_valid_lambda_response(self):
        """Test creating a valid Lambda response."""
        body = {"variant": "treatment", "experiment_id": "exp_123"}

        response = LambdaResponse(
            statusCode=200,
            body=body
        )

        assert response.statusCode == 200
        assert response.body == body
        assert "Content-Type" in response.headers

    def test_lambda_response_with_custom_headers(self):
        """Test Lambda response with custom headers."""
        body = {"message": "success"}
        headers = {
            "Content-Type": "application/json",
            "X-Custom-Header": "value"
        }

        response = LambdaResponse(
            statusCode=200,
            body=body,
            headers=headers
        )

        assert response.headers == headers
        assert response.headers["X-Custom-Header"] == "value"

    def test_lambda_error_response(self):
        """Test Lambda error response."""
        body = {"error": "Invalid request"}

        response = LambdaResponse(
            statusCode=400,
            body=body
        )

        assert response.statusCode == 400
        assert "error" in response.body

    def test_lambda_response_serialization(self):
        """Test that Lambda response can be serialized."""
        response = LambdaResponse(
            statusCode=200,
            body={"success": True}
        )

        data = response.model_dump()
        assert isinstance(data, dict)
        assert data["statusCode"] == 200
        assert isinstance(data["body"], dict)
