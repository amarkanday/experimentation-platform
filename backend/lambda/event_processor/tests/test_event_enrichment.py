"""
Unit tests for event enrichment - Event Processor Lambda.

This module tests the enrichment of validated events with:
- Assignment data from DynamoDB
- Experiment metadata
- Derived fields and calculations
- Graceful handling of missing data

Test-Driven Development (TDD) - RED phase:
- Write tests first, implementation follows
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any


class TestEventEnrichment:
    """Test suite for event enrichment functionality."""

    def test_enrich_event_with_assignment_data(self):
        """
        🔴 RED: Test that assignment data is fetched and added to event.

        Given: A validated event with user_id and experiment_id
        When: enrich_event() is called
        Then: Assignment data from DynamoDB is added to the event
        """
        # Arrange
        from event_validator import validate_event

        event_dict = {
            "event_id": "evt_123",
            "event_type": "page_view",
            "user_id": "user_456",
            "experiment_id": "exp_789",
            "timestamp": "2024-12-19T10:30:00Z"
        }

        validated_event = validate_event(event_dict)

        # Mock DynamoDB response with assignment
        mock_assignment = {
            "assignment_id": "assign_123",
            "user_id": "user_456",
            "experiment_id": "exp_789",
            "variant": "treatment",
            "timestamp": "2024-12-19T09:00:00Z"
        }

        from event_enricher import enrich_event

        # Act
        with patch('event_enricher.fetch_assignment_from_dynamodb', return_value=mock_assignment):
            enriched_event = enrich_event(validated_event)

        # Assert
        assert enriched_event["event_id"] == "evt_123"
        assert enriched_event["assignment_id"] == "assign_123"
        assert enriched_event["variant"] == "treatment"
        assert enriched_event["user_id"] == "user_456"  # Original data preserved

    def test_enrich_event_with_experiment_metadata(self):
        """
        🔴 RED: Test that experiment metadata is fetched and added.

        Given: A validated event with experiment_id
        When: enrich_event() is called
        Then: Experiment metadata (name, key, status) is added to event
        """
        # Arrange
        from event_validator import validate_event

        event_dict = {
            "event_id": "evt_456",
            "event_type": "conversion",
            "user_id": "user_789",
            "experiment_id": "exp_123",
            "timestamp": "2024-12-19T10:30:00Z"
        }

        validated_event = validate_event(event_dict)

        # Mock assignment data
        mock_assignment = {
            "assignment_id": "assign_456",
            "user_id": "user_789",
            "experiment_id": "exp_123",
            "variant": "control",
            "timestamp": "2024-12-19T09:00:00Z"
        }

        # Mock experiment metadata
        mock_experiment = {
            "experiment_id": "exp_123",
            "key": "checkout_redesign",
            "name": "Checkout Redesign Test",
            "status": "active"
        }

        from event_enricher import enrich_event

        # Act
        with patch('event_enricher.fetch_assignment_from_dynamodb', return_value=mock_assignment):
            with patch('event_enricher.fetch_experiment_metadata', return_value=mock_experiment):
                enriched_event = enrich_event(validated_event)

        # Assert
        assert enriched_event["experiment_key"] == "checkout_redesign"
        assert enriched_event["experiment_name"] == "Checkout Redesign Test"
        assert enriched_event["experiment_status"] == "active"

    def test_enrich_event_without_experiment_id(self):
        """
        🔴 RED: Test enrichment of events without experiment_id.

        Given: A validated event without experiment_id
        When: enrich_event() is called
        Then: Event is returned without assignment/experiment data
        """
        # Arrange
        from event_validator import validate_event

        event_dict = {
            "event_id": "evt_789",
            "event_type": "page_view",
            "user_id": "user_111",
            "timestamp": "2024-12-19T10:30:00Z"
            # No experiment_id
        }

        validated_event = validate_event(event_dict)

        from event_enricher import enrich_event

        # Act
        enriched_event = enrich_event(validated_event)

        # Assert
        assert enriched_event["event_id"] == "evt_789"
        assert "assignment_id" not in enriched_event
        assert "variant" not in enriched_event
        assert "experiment_key" not in enriched_event

    def test_enrich_event_with_missing_assignment_handled_gracefully(self):
        """
        🔴 RED: Test that missing assignment is handled gracefully.

        Given: A validated event with experiment_id but no assignment exists
        When: enrich_event() is called and DynamoDB returns None
        Then: Event is enriched with experiment metadata but no assignment data
        """
        # Arrange
        from event_validator import validate_event

        event_dict = {
            "event_id": "evt_999",
            "event_type": "page_view",
            "user_id": "user_new",
            "experiment_id": "exp_123",
            "timestamp": "2024-12-19T10:30:00Z"
        }

        validated_event = validate_event(event_dict)

        # Mock experiment metadata
        mock_experiment = {
            "experiment_id": "exp_123",
            "key": "checkout_redesign",
            "name": "Checkout Redesign Test",
            "status": "active"
        }

        from event_enricher import enrich_event

        # Act
        with patch('event_enricher.fetch_assignment_from_dynamodb', return_value=None):
            with patch('event_enricher.fetch_experiment_metadata', return_value=mock_experiment):
                enriched_event = enrich_event(validated_event)

        # Assert
        assert enriched_event["event_id"] == "evt_999"
        assert "assignment_id" not in enriched_event
        assert "variant" not in enriched_event
        # But experiment metadata should still be present
        assert enriched_event["experiment_key"] == "checkout_redesign"

    def test_enrich_event_preserves_original_data(self):
        """
        🔴 RED: Test that enrichment preserves all original event data.

        Given: A validated event with properties and metadata
        When: enrich_event() is called
        Then: Original properties and metadata are preserved
        """
        # Arrange
        from event_validator import validate_event

        event_dict = {
            "event_id": "evt_original",
            "event_type": "purchase",
            "user_id": "user_customer",
            "experiment_id": "exp_pricing",
            "timestamp": "2024-12-19T10:30:00Z",
            "properties": {
                "revenue": 99.99,
                "item_count": 3,
                "payment_method": "credit_card"
            },
            "metadata": {
                "source": "mobile_app",
                "version": "2.1.0",
                "platform": "ios"
            }
        }

        validated_event = validate_event(event_dict)

        # Mock assignment
        mock_assignment = {
            "assignment_id": "assign_pricing",
            "user_id": "user_customer",
            "experiment_id": "exp_pricing",
            "variant": "discount_20",
            "timestamp": "2024-12-19T09:00:00Z"
        }

        from event_enricher import enrich_event

        # Act
        with patch('event_enricher.fetch_assignment_from_dynamodb', return_value=mock_assignment):
            enriched_event = enrich_event(validated_event)

        # Assert - Original data preserved
        assert enriched_event["properties"]["revenue"] == 99.99
        assert enriched_event["properties"]["item_count"] == 3
        assert enriched_event["properties"]["payment_method"] == "credit_card"
        assert enriched_event["metadata"]["source"] == "mobile_app"
        assert enriched_event["metadata"]["version"] == "2.1.0"
        # And enrichment added
        assert enriched_event["variant"] == "discount_20"

    def test_enrich_event_with_derived_fields(self):
        """
        🔴 RED: Test that derived fields are calculated and added.

        Given: A validated event with timestamp
        When: enrich_event() is called
        Then: Derived fields like time_since_assignment are calculated
        """
        # Arrange
        from event_validator import validate_event

        event_dict = {
            "event_id": "evt_derived",
            "event_type": "conversion",
            "user_id": "user_123",
            "experiment_id": "exp_456",
            "timestamp": "2024-12-19T10:30:00Z"
        }

        validated_event = validate_event(event_dict)

        # Mock assignment with earlier timestamp
        mock_assignment = {
            "assignment_id": "assign_derived",
            "user_id": "user_123",
            "experiment_id": "exp_456",
            "variant": "treatment",
            "timestamp": "2024-12-19T09:00:00Z"  # 1.5 hours before event
        }

        from event_enricher import enrich_event

        # Act
        with patch('event_enricher.fetch_assignment_from_dynamodb', return_value=mock_assignment):
            enriched_event = enrich_event(validated_event)

        # Assert
        assert "time_since_assignment_seconds" in enriched_event
        # Should be approximately 1.5 hours = 5400 seconds
        assert enriched_event["time_since_assignment_seconds"] > 5000
        assert enriched_event["time_since_assignment_seconds"] < 6000

    def test_enrich_events_batch(self):
        """
        🔴 RED: Test batch enrichment of multiple events.

        Given: A list of validated events
        When: enrich_events_batch() is called
        Then: All events are enriched with their respective data
        """
        # Arrange
        from event_validator import validate_event

        events = [
            {
                "event_id": "evt_1",
                "event_type": "page_view",
                "user_id": "user_1",
                "experiment_id": "exp_a",
                "timestamp": "2024-12-19T10:00:00Z"
            },
            {
                "event_id": "evt_2",
                "event_type": "conversion",
                "user_id": "user_2",
                "experiment_id": "exp_b",
                "timestamp": "2024-12-19T10:01:00Z"
            },
            {
                "event_id": "evt_3",
                "event_type": "page_view",
                "user_id": "user_3",
                "timestamp": "2024-12-19T10:02:00Z"
                # No experiment_id
            }
        ]

        validated_events = [validate_event(e) for e in events]

        # Mock assignments for each experiment
        def mock_fetch_assignment(user_id, experiment_id):
            assignments = {
                ("user_1", "exp_a"): {"assignment_id": "a1", "variant": "control"},
                ("user_2", "exp_b"): {"assignment_id": "a2", "variant": "treatment"}
            }
            return assignments.get((user_id, experiment_id))

        from event_enricher import enrich_events_batch

        # Act
        with patch('event_enricher.fetch_assignment_from_dynamodb', side_effect=mock_fetch_assignment):
            enriched_events = enrich_events_batch(validated_events)

        # Assert
        assert len(enriched_events) == 3
        assert enriched_events[0]["variant"] == "control"
        assert enriched_events[1]["variant"] == "treatment"
        assert "variant" not in enriched_events[2]  # No experiment_id

    def test_enrich_event_handles_dynamodb_errors(self):
        """
        🔴 RED: Test that DynamoDB fetch errors are handled gracefully.

        Given: A validated event with experiment_id
        When: enrich_event() is called and DynamoDB raises an error
        Then: Event is returned with error flag, original data preserved
        """
        # Arrange
        from event_validator import validate_event

        event_dict = {
            "event_id": "evt_error",
            "event_type": "page_view",
            "user_id": "user_error",
            "experiment_id": "exp_error",
            "timestamp": "2024-12-19T10:30:00Z"
        }

        validated_event = validate_event(event_dict)

        from event_enricher import enrich_event

        # Act - Mock DynamoDB error
        with patch('event_enricher.fetch_assignment_from_dynamodb', side_effect=Exception("DynamoDB error")):
            enriched_event = enrich_event(validated_event)

        # Assert
        assert enriched_event["event_id"] == "evt_error"
        assert enriched_event.get("enrichment_error") is True
        assert "assignment_id" not in enriched_event
        # Original data should be preserved
        assert enriched_event["user_id"] == "user_error"
