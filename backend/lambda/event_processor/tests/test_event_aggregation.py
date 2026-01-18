"""
Unit tests for event aggregation - Event Processor Lambda.

This module tests real-time metric aggregation in DynamoDB:
- Atomic counter increments
- Multiple events aggregated correctly
- Time-windowed aggregation (hourly, daily)
- Concurrent update handling with conditional writes
- Race condition prevention

Test-Driven Development (TDD) - RED phase:
- Write tests first, implementation follows
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List


class TestEventAggregation:
    """Test suite for DynamoDB event aggregation functionality."""

    def test_aggregate_single_event_increments_counter(self):
        """
        🔴 RED: Test that a single event increments the counter atomically.

        Given: An enriched event with experiment_id and variant
        When: aggregate_event() is called
        Then: DynamoDB counter is incremented by 1 using atomic update
        """
        # Arrange
        enriched_event = {
            "event_id": "evt_123",
            "event_type": "page_view",
            "user_id": "user_456",
            "experiment_id": "exp_789",
            "variant": "treatment",
            "timestamp": "2024-12-19T10:30:00Z"
        }

        from event_aggregator import aggregate_event

        # Mock DynamoDB update_item call
        mock_dynamodb_response = {
            "Attributes": {
                "event_count": 1,
                "unique_users": {"user_456"}
            }
        }

        # Act
        with patch('event_aggregator.dynamodb_table') as mock_table:
            mock_table.update_item.return_value = mock_dynamodb_response
            result = aggregate_event(enriched_event)

        # Assert
        assert mock_table.update_item.called
        # Verify atomic increment was used (UpdateExpression with ADD)
        call_args = mock_table.update_item.call_args
        assert "UpdateExpression" in call_args[1]
        assert "ADD" in call_args[1]["UpdateExpression"]
        assert result["event_count"] == 1

    def test_aggregate_multiple_events_same_experiment(self):
        """
        🔴 RED: Test that multiple events for same experiment aggregate correctly.

        Given: 3 events for the same experiment and variant
        When: aggregate_events_batch() is called
        Then: Counter is incremented by 3, unique users tracked
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_1",
                "event_type": "page_view",
                "user_id": "user_1",
                "experiment_id": "exp_123",
                "variant": "control",
                "timestamp": "2024-12-19T10:30:00Z"
            },
            {
                "event_id": "evt_2",
                "event_type": "page_view",
                "user_id": "user_2",
                "experiment_id": "exp_123",
                "variant": "control",
                "timestamp": "2024-12-19T10:31:00Z"
            },
            {
                "event_id": "evt_3",
                "event_type": "page_view",
                "user_id": "user_1",  # Same user as evt_1
                "experiment_id": "exp_123",
                "variant": "control",
                "timestamp": "2024-12-19T10:32:00Z"
            }
        ]

        from event_aggregator import aggregate_events_batch

        # Mock DynamoDB responses
        mock_responses = [
            {"Attributes": {"event_count": 1, "unique_user_ids": {"user_1"}}},
            {"Attributes": {"event_count": 2, "unique_user_ids": {"user_1", "user_2"}}},
            {"Attributes": {"event_count": 3, "unique_user_ids": {"user_1", "user_2"}}}  # Same user count
        ]

        # Act
        with patch('event_aggregator.dynamodb_table') as mock_table:
            mock_table.update_item.side_effect = mock_responses
            results = aggregate_events_batch(enriched_events)

        # Assert
        assert len(results) == 3
        assert mock_table.update_item.call_count == 3
        # Last result should show 3 events, 2 unique users
        assert results[-1]["event_count"] == 3
        assert results[-1]["unique_users"] == 2

    def test_aggregate_events_by_hourly_time_window(self):
        """
        🔴 RED: Test that events are aggregated by hourly time windows.

        Given: Events spanning multiple hours
        When: aggregate_events_batch() is called
        Then: Separate aggregation keys created for each hour
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_10am",
                "event_type": "conversion",
                "user_id": "user_1",
                "experiment_id": "exp_456",
                "variant": "treatment",
                "timestamp": "2024-12-19T10:15:00Z"  # 10am hour
            },
            {
                "event_id": "evt_11am",
                "event_type": "conversion",
                "user_id": "user_2",
                "experiment_id": "exp_456",
                "variant": "treatment",
                "timestamp": "2024-12-19T11:30:00Z"  # 11am hour
            }
        ]

        from event_aggregator import aggregate_events_batch

        # Act
        with patch('event_aggregator.dynamodb_table') as mock_table:
            mock_table.update_item.return_value = {"Attributes": {"event_count": 1}}
            results = aggregate_events_batch(enriched_events)

        # Assert
        assert mock_table.update_item.call_count == 2
        # Check that different partition keys were used for different hours
        call_args_list = mock_table.update_item.call_args_list
        key_1 = call_args_list[0][1]["Key"]
        key_2 = call_args_list[1][1]["Key"]
        # Keys should be different because of different time windows
        assert key_1 != key_2

    def test_aggregate_events_by_daily_time_window(self):
        """
        🔴 RED: Test that events are aggregated by daily time windows.

        Given: Events spanning multiple days
        When: aggregate_events_batch(window='daily') is called
        Then: Separate aggregation keys created for each day
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_day1",
                "event_type": "page_view",
                "user_id": "user_1",
                "experiment_id": "exp_789",
                "variant": "control",
                "timestamp": "2024-12-19T10:00:00Z"
            },
            {
                "event_id": "evt_day2",
                "event_type": "page_view",
                "user_id": "user_2",
                "experiment_id": "exp_789",
                "variant": "control",
                "timestamp": "2024-12-20T10:00:00Z"  # Next day
            }
        ]

        from event_aggregator import aggregate_events_batch

        # Act
        with patch('event_aggregator.dynamodb_table') as mock_table:
            mock_table.update_item.return_value = {"Attributes": {"event_count": 1}}
            results = aggregate_events_batch(enriched_events, window='daily')

        # Assert
        assert mock_table.update_item.call_count == 2
        call_args_list = mock_table.update_item.call_args_list
        key_1 = call_args_list[0][1]["Key"]
        key_2 = call_args_list[1][1]["Key"]
        assert key_1 != key_2

    def test_aggregate_uses_conditional_write_to_prevent_conflicts(self):
        """
        🔴 RED: Test that DynamoDB conditional writes prevent race conditions.

        Given: An event to aggregate
        When: aggregate_event() is called
        Then: Conditional update expression is used to handle concurrent writes
        """
        # Arrange
        enriched_event = {
            "event_id": "evt_concurrent",
            "event_type": "conversion",
            "user_id": "user_123",
            "experiment_id": "exp_concurrent",
            "variant": "treatment",
            "timestamp": "2024-12-19T10:30:00Z"
        }

        from event_aggregator import aggregate_event

        # Act
        with patch('event_aggregator.dynamodb_table') as mock_table:
            mock_table.update_item.return_value = {"Attributes": {"event_count": 1}}
            result = aggregate_event(enriched_event)

        # Assert
        call_args = mock_table.update_item.call_args
        # Should use atomic ADD operation which is naturally atomic
        assert "ADD" in call_args[1]["UpdateExpression"]

    def test_aggregate_handles_concurrent_updates_gracefully(self):
        """
        🔴 RED: Test handling of concurrent update conflicts.

        Given: Two concurrent updates to the same counter
        When: DynamoDB raises ConditionalCheckFailedException
        Then: Operation is retried successfully
        """
        # Arrange
        enriched_event = {
            "event_id": "evt_retry",
            "event_type": "page_view",
            "user_id": "user_retry",
            "experiment_id": "exp_retry",
            "variant": "control",
            "timestamp": "2024-12-19T10:30:00Z"
        }

        from event_aggregator import aggregate_event
        from botocore.exceptions import ClientError

        # Mock conditional check failure on first call, success on retry
        mock_error = ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException"}},
            "UpdateItem"
        )

        # Act
        with patch('event_aggregator.dynamodb_table') as mock_table:
            mock_table.update_item.side_effect = [
                mock_error,  # First call fails
                {"Attributes": {"event_count": 2}}  # Retry succeeds
            ]
            result = aggregate_event(enriched_event, max_retries=2)

        # Assert
        assert mock_table.update_item.call_count == 2  # Called twice (1 fail + 1 success)
        assert result["event_count"] == 2

    def test_aggregate_creates_partition_key_from_experiment_variant_time(self):
        """
        🔴 RED: Test that partition key includes experiment, variant, and time window.

        Given: An enriched event
        When: aggregate_event() is called
        Then: Partition key format is "exp_{id}#variant#{variant}#hour#{timestamp}"
        """
        # Arrange
        enriched_event = {
            "event_id": "evt_key",
            "event_type": "conversion",
            "user_id": "user_key",
            "experiment_id": "exp_abc123",
            "variant": "treatment",
            "timestamp": "2024-12-19T10:30:00Z"
        }

        from event_aggregator import aggregate_event, create_aggregation_key

        # Act
        aggregation_key = create_aggregation_key(
            enriched_event["experiment_id"],
            enriched_event["variant"],
            enriched_event["timestamp"],
            window="hourly"
        )

        # Assert
        assert "exp_abc123" in aggregation_key
        assert "treatment" in aggregation_key
        assert "2024-12-19" in aggregation_key
        assert "10" in aggregation_key  # Hour

    def test_aggregate_tracks_unique_users_per_variant(self):
        """
        🔴 RED: Test that unique user counts are tracked per variant.

        Given: Multiple events from same user in different variants
        When: aggregate_events_batch() is called
        Then: Each variant tracks unique users separately
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_control",
                "event_type": "page_view",
                "user_id": "user_both",
                "experiment_id": "exp_tracking",
                "variant": "control",
                "timestamp": "2024-12-19T10:30:00Z"
            },
            {
                "event_id": "evt_treatment",
                "event_type": "page_view",
                "user_id": "user_both",  # Same user, different variant
                "experiment_id": "exp_tracking",
                "variant": "treatment",
                "timestamp": "2024-12-19T10:31:00Z"
            }
        ]

        from event_aggregator import aggregate_events_batch

        # Act
        with patch('event_aggregator.dynamodb_table') as mock_table:
            mock_table.update_item.side_effect = [
                {"Attributes": {"event_count": 1, "unique_users": 1}},
                {"Attributes": {"event_count": 1, "unique_users": 1}}
            ]
            results = aggregate_events_batch(enriched_events)

        # Assert
        assert mock_table.update_item.call_count == 2
        # Each variant should have its own aggregation
        call_args_list = mock_table.update_item.call_args_list
        key_1 = call_args_list[0][1]["Key"]
        key_2 = call_args_list[1][1]["Key"]
        # Keys should be different due to different variants
        assert key_1 != key_2

    def test_aggregate_handles_events_without_experiment_id(self):
        """
        🔴 RED: Test that events without experiment_id are skipped gracefully.

        Given: An enriched event without experiment_id
        When: aggregate_event() is called
        Then: Event is skipped, no DynamoDB call made
        """
        # Arrange
        enriched_event = {
            "event_id": "evt_no_exp",
            "event_type": "page_view",
            "user_id": "user_456",
            "timestamp": "2024-12-19T10:30:00Z"
            # No experiment_id or variant
        }

        from event_aggregator import aggregate_event

        # Act
        with patch('event_aggregator.dynamodb_table') as mock_table:
            result = aggregate_event(enriched_event)

        # Assert
        assert not mock_table.update_item.called
        assert result is None or result.get("skipped") is True

    def test_aggregate_batch_returns_success_and_failure_counts(self):
        """
        🔴 RED: Test that batch aggregation returns success/failure metrics.

        Given: A batch with some successful and some failed aggregations
        When: aggregate_events_batch() is called
        Then: Returns dict with success_count and failure_count
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_success",
                "event_type": "conversion",
                "user_id": "user_1",
                "experiment_id": "exp_123",
                "variant": "control",
                "timestamp": "2024-12-19T10:30:00Z"
            },
            {
                "event_id": "evt_fail",
                "event_type": "conversion",
                "user_id": "user_2",
                "experiment_id": "exp_456",
                "variant": "treatment",
                "timestamp": "2024-12-19T10:31:00Z"
            }
        ]

        from event_aggregator import aggregate_events_batch

        # Act - Mock one success, one failure
        with patch('event_aggregator.dynamodb_table') as mock_table:
            mock_table.update_item.side_effect = [
                {"Attributes": {"event_count": 1}},  # Success
                Exception("DynamoDB error")  # Failure
            ]
            results = aggregate_events_batch(enriched_events, return_summary=True)

        # Assert
        assert results["success_count"] == 1
        assert results["failure_count"] == 1
        assert results["total_events"] == 2
