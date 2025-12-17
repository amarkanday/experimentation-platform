"""
Unit tests for audit log Pydantic schemas.

This module tests the audit log schemas including:
- AuditLogCreate validation
- AuditLogResponse serialization
- ToggleRequest validation
- ToggleResponse serialization
- AuditLogFilterParams validation
- Schema edge cases and error handling
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from pydantic import ValidationError

from backend.app.schemas.audit_log import (
    AuditLogCreate,
    AuditLogResponse,
    AuditLogListResponse,
    ToggleRequest,
    ToggleResponse,
    AuditLogFilterParams,
    AuditStatsResponse,
)
from backend.app.models.audit_log import ActionType, EntityType


class TestAuditLogCreateSchema:
    """Test cases for AuditLogCreate schema."""

    def test_audit_log_create_valid(self):
        """Test valid AuditLogCreate schema."""
        data = {
            "user_id": uuid4(),
            "user_email": "test@example.com",
            "action_type": ActionType.TOGGLE_ENABLE.value,
            "entity_type": EntityType.FEATURE_FLAG.value,
            "entity_id": uuid4(),
            "entity_name": "test_feature",
            "old_value": "inactive",
            "new_value": "active",
            "reason": "Testing audit log creation",
        }

        audit_log = AuditLogCreate(**data)

        assert audit_log.user_id == data["user_id"]
        assert audit_log.user_email == data["user_email"]
        assert audit_log.action_type == data["action_type"]
        assert audit_log.entity_type == data["entity_type"]
        assert audit_log.entity_id == data["entity_id"]
        assert audit_log.entity_name == data["entity_name"]
        assert audit_log.old_value == data["old_value"]
        assert audit_log.new_value == data["new_value"]
        assert audit_log.reason == data["reason"]

    def test_audit_log_create_minimal(self):
        """Test AuditLogCreate with minimal required fields."""
        data = {
            "user_email": "minimal@example.com",
            "action_type": ActionType.FEATURE_FLAG_CREATE.value,
            "entity_type": EntityType.FEATURE_FLAG.value,
            "entity_id": uuid4(),
            "entity_name": "minimal_feature",
        }

        audit_log = AuditLogCreate(**data)

        assert audit_log.user_id is None
        assert audit_log.old_value is None
        assert audit_log.new_value is None
        assert audit_log.reason is None

    def test_audit_log_create_invalid_action_type(self):
        """Test AuditLogCreate with invalid action type."""
        data = {
            "user_email": "test@example.com",
            "action_type": "invalid_action_type",
            "entity_type": EntityType.FEATURE_FLAG.value,
            "entity_id": uuid4(),
            "entity_name": "test_feature",
        }

        with pytest.raises(ValidationError) as exc_info:
            AuditLogCreate(**data)

        assert "Invalid action type" in str(exc_info.value)

    def test_audit_log_create_invalid_entity_type(self):
        """Test AuditLogCreate with invalid entity type."""
        data = {
            "user_email": "test@example.com",
            "action_type": ActionType.TOGGLE_ENABLE.value,
            "entity_type": "invalid_entity_type",
            "entity_id": uuid4(),
            "entity_name": "test_feature",
        }

        with pytest.raises(ValidationError) as exc_info:
            AuditLogCreate(**data)

        assert "Invalid entity type" in str(exc_info.value)

    def test_audit_log_create_missing_required_fields(self):
        """Test AuditLogCreate with missing required fields."""
        # Missing user_email
        with pytest.raises(ValidationError):
            AuditLogCreate(
                action_type=ActionType.TOGGLE_ENABLE.value,
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=uuid4(),
                entity_name="test_feature",
            )

        # Missing action_type
        with pytest.raises(ValidationError):
            AuditLogCreate(
                user_email="test@example.com",
                entity_type=EntityType.FEATURE_FLAG.value,
                entity_id=uuid4(),
                entity_name="test_feature",
            )


class TestAuditLogResponseSchema:
    """Test cases for AuditLogResponse schema."""

    def test_audit_log_response_valid(self):
        """Test valid AuditLogResponse schema."""
        data = {
            "id": uuid4(),
            "user_id": uuid4(),
            "user_email": "response@example.com",
            "action_type": ActionType.EXPERIMENT_CREATE.value,
            "entity_type": EntityType.EXPERIMENT.value,
            "entity_id": uuid4(),
            "entity_name": "response_experiment",
            "old_value": None,
            "new_value": "created",
            "reason": "Response test",
            "timestamp": datetime.now(timezone.utc),
            "action_description": "created",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        response = AuditLogResponse(**data)

        assert response.id == data["id"]
        assert response.user_id == data["user_id"]
        assert response.user_email == data["user_email"]
        assert response.action_type == data["action_type"]
        assert response.timestamp == data["timestamp"]
        assert response.action_description == data["action_description"]

    def test_audit_log_response_with_none_values(self):
        """Test AuditLogResponse with None values."""
        data = {
            "id": uuid4(),
            "user_id": None,
            "user_email": "system@example.com",
            "action_type": ActionType.SAFETY_ROLLBACK.value,
            "entity_type": EntityType.FEATURE_FLAG.value,
            "entity_id": uuid4(),
            "entity_name": "system_feature",
            "old_value": None,
            "new_value": None,
            "reason": None,
            "timestamp": datetime.now(timezone.utc),
            "action_description": "rolled back",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        response = AuditLogResponse(**data)

        assert response.user_id is None
        assert response.old_value is None
        assert response.new_value is None
        assert response.reason is None


class TestAuditLogListResponseSchema:
    """Test cases for AuditLogListResponse schema."""

    def test_audit_log_list_response_valid(self):
        """Test valid AuditLogListResponse schema."""
        item_data = {
            "id": uuid4(),
            "user_id": uuid4(),
            "user_email": "list@example.com",
            "action_type": ActionType.TOGGLE_ENABLE.value,
            "entity_type": EntityType.FEATURE_FLAG.value,
            "entity_id": uuid4(),
            "entity_name": "list_feature",
            "old_value": "inactive",
            "new_value": "active",
            "reason": "List test",
            "timestamp": datetime.now(timezone.utc),
            "action_description": "enabled",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        data = {
            "items": [AuditLogResponse(**item_data)],
            "total": 25,
            "page": 1,
            "limit": 10,
        }

        response = AuditLogListResponse(**data)

        assert len(response.items) == 1
        assert response.total == 25
        assert response.page == 1
        assert response.limit == 10
        assert response.total_pages == 3  # ceil(25/10)

    def test_audit_log_list_response_total_pages_calculation(self):
        """Test total pages calculation in AuditLogListResponse."""
        test_cases = [
            {"total": 0, "limit": 10, "expected_pages": 0},
            {"total": 5, "limit": 10, "expected_pages": 1},
            {"total": 10, "limit": 10, "expected_pages": 1},
            {"total": 11, "limit": 10, "expected_pages": 2},
            {"total": 25, "limit": 10, "expected_pages": 3},
            {"total": 100, "limit": 20, "expected_pages": 5},
        ]

        for case in test_cases:
            data = {
                "items": [],
                "total": case["total"],
                "page": 1,
                "limit": case["limit"],
            }

            response = AuditLogListResponse(**data)
            assert response.total_pages == case["expected_pages"]


class TestToggleRequestSchema:
    """Test cases for ToggleRequest schema."""

    def test_toggle_request_valid(self):
        """Test valid ToggleRequest schema."""
        data = {"reason": "Testing toggle request"}

        request = ToggleRequest(**data)

        assert request.reason == "Testing toggle request"

    def test_toggle_request_empty(self):
        """Test ToggleRequest with no reason."""
        request = ToggleRequest()

        assert request.reason is None

    def test_toggle_request_empty_reason(self):
        """Test ToggleRequest with empty string reason."""
        request = ToggleRequest(reason="   ")

        assert request.reason is None

    def test_toggle_request_reason_too_long(self):
        """Test ToggleRequest with reason exceeding length limit."""
        long_reason = "x" * 1001

        with pytest.raises(ValidationError) as exc_info:
            ToggleRequest(reason=long_reason)

        assert "1000 characters or less" in str(exc_info.value)

    def test_toggle_request_valid_long_reason(self):
        """Test ToggleRequest with maximum valid reason length."""
        max_reason = "x" * 1000

        request = ToggleRequest(reason=max_reason)

        assert request.reason == max_reason


class TestToggleResponseSchema:
    """Test cases for ToggleResponse schema."""

    def test_toggle_response_valid(self):
        """Test valid ToggleResponse schema."""
        data = {
            "id": uuid4(),
            "name": "Toggle Response Feature",
            "key": "toggle_response_feature",
            "status": "active",
            "updated_at": datetime.now(timezone.utc),
            "audit_log_id": uuid4(),
        }

        response = ToggleResponse(**data)

        assert response.id == data["id"]
        assert response.name == data["name"]
        assert response.key == data["key"]
        assert response.status == data["status"]
        assert response.updated_at == data["updated_at"]
        assert response.audit_log_id == data["audit_log_id"]


class TestAuditLogFilterParamsSchema:
    """Test cases for AuditLogFilterParams schema."""

    def test_filter_params_valid(self):
        """Test valid AuditLogFilterParams schema."""
        data = {
            "user_id": uuid4(),
            "entity_type": EntityType.FEATURE_FLAG.value,
            "entity_id": uuid4(),
            "action_type": ActionType.TOGGLE_ENABLE.value,
            "from_date": datetime.now(timezone.utc) - timedelta(days=7),
            "to_date": datetime.now(timezone.utc),
            "page": 2,
            "limit": 25,
        }

        params = AuditLogFilterParams(**data)

        assert params.user_id == data["user_id"]
        assert params.entity_type == data["entity_type"]
        assert params.entity_id == data["entity_id"]
        assert params.action_type == data["action_type"]
        assert params.from_date == data["from_date"]
        assert params.to_date == data["to_date"]
        assert params.page == data["page"]
        assert params.limit == data["limit"]

    def test_filter_params_defaults(self):
        """Test AuditLogFilterParams with default values."""
        params = AuditLogFilterParams()

        assert params.user_id is None
        assert params.entity_type is None
        assert params.entity_id is None
        assert params.action_type is None
        assert params.from_date is None
        assert params.to_date is None
        assert params.page == 1
        assert params.limit == 50

    def test_filter_params_invalid_page(self):
        """Test AuditLogFilterParams with invalid page number."""
        with pytest.raises(ValidationError) as exc_info:
            AuditLogFilterParams(page=0)

        assert "Page number must be 1 or greater" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            AuditLogFilterParams(page=-1)

        assert "Page number must be 1 or greater" in str(exc_info.value)

    def test_filter_params_invalid_limit(self):
        """Test AuditLogFilterParams with invalid limit values."""
        with pytest.raises(ValidationError) as exc_info:
            AuditLogFilterParams(limit=0)

        assert "Limit must be between 1 and 1000" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            AuditLogFilterParams(limit=1001)

        assert "Limit must be between 1 and 1000" in str(exc_info.value)

    def test_filter_params_invalid_entity_type(self):
        """Test AuditLogFilterParams with invalid entity type."""
        with pytest.raises(ValidationError) as exc_info:
            AuditLogFilterParams(entity_type="invalid_entity")

        assert "Invalid entity type" in str(exc_info.value)

    def test_filter_params_invalid_action_type(self):
        """Test AuditLogFilterParams with invalid action type."""
        with pytest.raises(ValidationError) as exc_info:
            AuditLogFilterParams(action_type="invalid_action")

        assert "Invalid action type" in str(exc_info.value)

    def test_filter_params_invalid_date_range(self):
        """Test AuditLogFilterParams with invalid date range."""
        from_date = datetime.now(timezone.utc)
        to_date = from_date - timedelta(days=1)  # Invalid: to_date before from_date

        with pytest.raises(ValidationError) as exc_info:
            AuditLogFilterParams(from_date=from_date, to_date=to_date)

        assert "to_date must be after from_date" in str(exc_info.value)

    def test_filter_params_valid_date_range(self):
        """Test AuditLogFilterParams with valid date range."""
        from_date = datetime.now(timezone.utc) - timedelta(days=7)
        to_date = datetime.now(timezone.utc)

        params = AuditLogFilterParams(from_date=from_date, to_date=to_date)

        assert params.from_date == from_date
        assert params.to_date == to_date

    def test_filter_params_valid_enum_values(self):
        """Test AuditLogFilterParams with valid enum string values."""
        params = AuditLogFilterParams(
            entity_type="feature_flag",
            action_type="toggle_enable"
        )

        assert params.entity_type == "feature_flag"
        assert params.action_type == "toggle_enable"


class TestAuditStatsResponseSchema:
    """Test cases for AuditStatsResponse schema."""

    def test_audit_stats_response_valid(self):
        """Test valid AuditStatsResponse schema."""
        data = {
            "total_logs": 1000,
            "action_counts": {
                "toggle_enable": 250,
                "toggle_disable": 200,
                "feature_flag_create": 150,
                "experiment_create": 100,
            },
            "entity_counts": {
                "feature_flag": 600,
                "experiment": 300,
                "user": 100,
            },
            "most_active_users": {
                "admin@example.com": 300,
                "developer@example.com": 250,
                "analyst@example.com": 150,
            },
            "date_range": {
                "from_date": "2024-01-01T00:00:00Z",
                "to_date": "2024-01-31T23:59:59Z",
            },
        }

        stats = AuditStatsResponse(**data)

        assert stats.total_logs == 1000
        assert stats.action_counts["toggle_enable"] == 250
        assert stats.entity_counts["feature_flag"] == 600
        assert stats.most_active_users["admin@example.com"] == 300
        assert stats.date_range["from_date"] == "2024-01-01T00:00:00Z"

    def test_audit_stats_response_empty_data(self):
        """Test AuditStatsResponse with empty data."""
        data = {
            "total_logs": 0,
            "action_counts": {},
            "entity_counts": {},
            "most_active_users": {},
            "date_range": {
                "from_date": None,
                "to_date": None,
            },
        }

        stats = AuditStatsResponse(**data)

        assert stats.total_logs == 0
        assert len(stats.action_counts) == 0
        assert len(stats.entity_counts) == 0
        assert len(stats.most_active_users) == 0
        assert stats.date_range["from_date"] is None
        assert stats.date_range["to_date"] is None


class TestSchemaIntegration:
    """Integration tests for schema interactions."""

    def test_audit_log_create_to_response_conversion(self):
        """Test converting AuditLogCreate data to AuditLogResponse."""
        create_data = {
            "user_id": uuid4(),
            "user_email": "integration@example.com",
            "action_type": ActionType.FEATURE_FLAG_UPDATE.value,
            "entity_type": EntityType.FEATURE_FLAG.value,
            "entity_id": uuid4(),
            "entity_name": "integration_feature",
            "old_value": "inactive",
            "new_value": "active",
            "reason": "Integration test",
        }

        create_schema = AuditLogCreate(**create_data)

        # Simulate database response data
        response_data = {
            "id": uuid4(),
            "timestamp": datetime.now(timezone.utc),
            "action_description": "updated",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            **create_data
        }

        response_schema = AuditLogResponse(**response_data)

        # Verify data consistency
        assert response_schema.user_id == create_schema.user_id
        assert response_schema.user_email == create_schema.user_email
        assert response_schema.action_type == create_schema.action_type
        assert response_schema.entity_type == create_schema.entity_type
        assert response_schema.old_value == create_schema.old_value
        assert response_schema.new_value == create_schema.new_value
        assert response_schema.reason == create_schema.reason

    def test_filter_params_to_service_call(self):
        """Test converting filter params to service method parameters."""
        filter_data = {
            "user_id": uuid4(),
            "entity_type": "feature_flag",
            "action_type": "toggle_enable",
            "page": 2,
            "limit": 25,
        }

        params = AuditLogFilterParams(**filter_data)

        # Verify values can be used for service calls
        assert str(params.user_id) == str(filter_data["user_id"])
        assert params.entity_type == filter_data["entity_type"]
        assert params.action_type == filter_data["action_type"]
        assert params.page == filter_data["page"]
        assert params.limit == filter_data["limit"]