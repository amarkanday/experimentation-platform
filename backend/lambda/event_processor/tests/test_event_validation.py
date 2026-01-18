"""
Unit tests for event schema validation - Event Processor Lambda.

This module tests the validation of parsed events using Pydantic models:
- Required field validation
- Type checking
- Event type validation
- Data integrity checks

Test-Driven Development (TDD) - RED phase:
- Write tests first, implementation follows
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestEventSchemaValidation:
    """Test suite for event schema validation functionality."""

    def test_validate_valid_event_passes(self):
        """
        🔴 RED: Test that a valid event passes validation.

        Given: A properly formatted event dict with all required fields
        When: validate_event() is called
        Then: Returns validated EventData object
        """
        # Arrange
        event_dict = {
            "event_id": "evt_12345",
            "event_type": "page_view",
            "user_id": "user_67890",
            "timestamp": "2024-12-19T10:30:00Z"
        }

        from event_validator import validate_event

        # Act
        validated_event = validate_event(event_dict)

        # Assert
        assert validated_event.event_id == "evt_12345"
        assert validated_event.event_type == "page_view"
        assert validated_event.user_id == "user_67890"
        assert isinstance(validated_event.timestamp, datetime)

    def test_validate_event_with_optional_fields(self):
        """
        🔴 RED: Test validation of event with optional fields.

        Given: An event with optional experiment_id, properties, metadata
        When: validate_event() is called
        Then: Returns validated EventData with all fields
        """
        # Arrange
        event_dict = {
            "event_id": "evt_123",
            "event_type": "conversion",
            "user_id": "user_456",
            "timestamp": "2024-12-19T10:30:00Z",
            "experiment_id": "exp_789",
            "properties": {"revenue": 99.99, "item_count": 3},
            "metadata": {"source": "mobile_app", "version": "1.2.3"}
        }

        from event_validator import validate_event

        # Act
        validated_event = validate_event(event_dict)

        # Assert
        assert validated_event.experiment_id == "exp_789"
        assert validated_event.properties["revenue"] == 99.99
        assert validated_event.metadata["source"] == "mobile_app"

    def test_validate_missing_required_field_raises_error(self):
        """
        🔴 RED: Test that missing required fields raise ValidationError.

        Given: An event missing required field (user_id)
        When: validate_event() is called
        Then: Raises ValidationError with field name in message
        """
        # Arrange
        event_dict = {
            "event_id": "evt_123",
            "event_type": "page_view",
            # Missing user_id
            "timestamp": "2024-12-19T10:30:00Z"
        }

        from event_validator import validate_event

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_event(event_dict)

        error = exc_info.value
        assert "user_id" in str(error)
        assert "field required" in str(error).lower()

    def test_validate_invalid_event_type_field_raises_error(self):
        """
        🔴 RED: Test that incompatible field types raise ValidationError.

        Given: An event with event_type as dict instead of string
        When: validate_event() is called
        Then: Raises ValidationError with type error message
        """
        # Arrange
        event_dict = {
            "event_id": "evt_123",
            "event_type": {"invalid": "type"},  # Invalid: should be string
            "user_id": "user_456",
            "timestamp": "2024-12-19T10:30:00Z"
        }

        from event_validator import validate_event

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_event(event_dict)

        error = exc_info.value
        assert "event_type" in str(error)

    def test_validate_empty_event_raises_error(self):
        """
        🔴 RED: Test that empty event dict raises ValidationError.

        Given: An empty dictionary
        When: validate_event() is called
        Then: Raises ValidationError for all missing required fields
        """
        # Arrange
        event_dict = {}

        from event_validator import validate_event

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validate_event(event_dict)

        error = exc_info.value
        # Should mention multiple missing fields
        error_str = str(error)
        assert "event_id" in error_str
        assert "event_type" in error_str
        assert "user_id" in error_str

    def test_validate_batch_of_events(self):
        """
        🔴 RED: Test validation of multiple events in a batch.

        Given: A list of 3 valid event dicts
        When: validate_events_batch() is called
        Then: Returns list of 3 validated EventData objects
        """
        # Arrange
        events_batch = [
            {
                "event_id": "evt_1",
                "event_type": "page_view",
                "user_id": "user_1",
                "timestamp": "2024-12-19T10:00:00Z"
            },
            {
                "event_id": "evt_2",
                "event_type": "button_click",
                "user_id": "user_2",
                "timestamp": "2024-12-19T10:01:00Z"
            },
            {
                "event_id": "evt_3",
                "event_type": "conversion",
                "user_id": "user_3",
                "timestamp": "2024-12-19T10:02:00Z",
                "properties": {"value": 50.00}
            }
        ]

        from event_validator import validate_events_batch

        # Act
        validated_events = validate_events_batch(events_batch)

        # Assert
        assert len(validated_events) == 3
        assert validated_events[0].event_type == "page_view"
        assert validated_events[1].event_type == "button_click"
        assert validated_events[2].event_type == "conversion"
        assert validated_events[2].properties["value"] == 50.00

    def test_validate_batch_with_invalid_events_skips_and_reports(self):
        """
        🔴 RED: Test batch validation with skip_invalid=True.

        Given: A batch with 2 valid and 1 invalid event
        When: validate_events_batch(skip_invalid=True) is called
        Then: Returns (2 valid events, 1 error dict)
        """
        # Arrange
        events_batch = [
            {
                "event_id": "evt_1",
                "event_type": "page_view",
                "user_id": "user_1",
                "timestamp": "2024-12-19T10:00:00Z"
            },
            {
                # Invalid: missing user_id
                "event_id": "evt_2",
                "event_type": "button_click",
                "timestamp": "2024-12-19T10:01:00Z"
            },
            {
                "event_id": "evt_3",
                "event_type": "conversion",
                "user_id": "user_3",
                "timestamp": "2024-12-19T10:02:00Z"
            }
        ]

        from event_validator import validate_events_batch

        # Act
        validated_events, validation_errors = validate_events_batch(
            events_batch,
            skip_invalid=True
        )

        # Assert
        assert len(validated_events) == 2
        assert len(validation_errors) == 1
        assert validated_events[0].event_id == "evt_1"
        assert validated_events[1].event_id == "evt_3"
        assert validation_errors[0]["event_id"] == "evt_2"
        assert "user_id" in validation_errors[0]["error"]

    def test_validate_batch_without_skip_invalid_raises_on_first_error(self):
        """
        🔴 RED: Test batch validation fails fast without skip_invalid.

        Given: A batch with 1 invalid event
        When: validate_events_batch(skip_invalid=False) is called
        Then: Raises ValidationError on first invalid event
        """
        # Arrange
        events_batch = [
            {
                "event_id": "evt_1",
                "event_type": "page_view",
                "user_id": "user_1",
                "timestamp": "2024-12-19T10:00:00Z"
            },
            {
                # Invalid: missing user_id
                "event_id": "evt_2",
                "event_type": "button_click",
                "timestamp": "2024-12-19T10:01:00Z"
            }
        ]

        from event_validator import validate_events_batch

        # Act & Assert
        with pytest.raises(ValidationError):
            validate_events_batch(events_batch, skip_invalid=False)

    def test_validate_event_with_extra_fields_allowed(self):
        """
        🔴 RED: Test that extra unknown fields are allowed.

        Given: An event with extra fields not in schema
        When: validate_event() is called
        Then: Returns validated event (Pydantic ignores extra fields by default)
        """
        # Arrange
        event_dict = {
            "event_id": "evt_123",
            "event_type": "page_view",
            "user_id": "user_456",
            "timestamp": "2024-12-19T10:30:00Z",
            "unknown_field": "should_be_ignored",
            "another_extra": 12345
        }

        from event_validator import validate_event

        # Act
        validated_event = validate_event(event_dict)

        # Assert
        assert validated_event.event_id == "evt_123"
        # Extra fields should be ignored, not cause error

    def test_validate_event_id_uniqueness_check(self):
        """
        🔴 RED: Test optional event_id uniqueness validation.

        Given: A batch with duplicate event_ids
        When: validate_events_batch(check_duplicates=True) is called
        Then: Returns validation error for duplicate event_id
        """
        # Arrange
        events_batch = [
            {
                "event_id": "evt_123",  # Duplicate
                "event_type": "page_view",
                "user_id": "user_1",
                "timestamp": "2024-12-19T10:00:00Z"
            },
            {
                "event_id": "evt_123",  # Duplicate
                "event_type": "button_click",
                "user_id": "user_2",
                "timestamp": "2024-12-19T10:01:00Z"
            }
        ]

        from event_validator import validate_events_batch

        # Act
        validated_events, validation_errors = validate_events_batch(
            events_batch,
            skip_invalid=True,
            check_duplicates=True
        )

        # Assert
        # Should flag the duplicate
        assert len(validation_errors) >= 1
        assert any("duplicate" in err.get("error", "").lower() for err in validation_errors)

    def test_validate_preserves_datetime_formats(self):
        """
        🔴 RED: Test that various datetime formats are parsed correctly.

        Given: Events with different valid timestamp formats
        When: validate_event() is called
        Then: All are parsed to datetime objects correctly
        """
        # Arrange
        timestamp_formats = [
            "2024-12-19T10:30:00Z",           # ISO with Z
            "2024-12-19T10:30:00+00:00",      # ISO with timezone
            "2024-12-19T10:30:00.123456Z",    # ISO with microseconds
        ]

        from event_validator import validate_event

        for ts_format in timestamp_formats:
            event_dict = {
                "event_id": f"evt_{ts_format}",
                "event_type": "page_view",
                "user_id": "user_123",
                "timestamp": ts_format
            }

            # Act
            validated_event = validate_event(event_dict)

            # Assert
            assert isinstance(validated_event.timestamp, datetime)

    def test_validate_nested_properties_preserved(self):
        """
        🔴 RED: Test that nested dicts in properties/metadata are preserved.

        Given: An event with deeply nested properties
        When: validate_event() is called
        Then: Nested structure is preserved in validated object
        """
        # Arrange
        event_dict = {
            "event_id": "evt_123",
            "event_type": "purchase",
            "user_id": "user_456",
            "timestamp": "2024-12-19T10:30:00Z",
            "properties": {
                "cart": {
                    "items": [
                        {"id": "item1", "price": 10.00},
                        {"id": "item2", "price": 20.00}
                    ],
                    "total": 30.00
                },
                "payment": {
                    "method": "credit_card",
                    "last_four": "1234"
                }
            }
        }

        from event_validator import validate_event

        # Act
        validated_event = validate_event(event_dict)

        # Assert
        assert validated_event.properties["cart"]["total"] == 30.00
        assert len(validated_event.properties["cart"]["items"]) == 2
        assert validated_event.properties["payment"]["method"] == "credit_card"
