"""
Unit tests for Kinesis event parsing - Event Processor Lambda.

This module tests the parsing of Kinesis stream events, including:
- Base64 decoding of event data
- JSON parsing
- Batch event processing
- Error handling for malformed data

Test-Driven Development (TDD) - RED phase:
- Write tests first, implementation follows
"""

import base64
import json
import pytest
from typing import List, Dict, Any


class TestKinesisEventParsing:
    """Test suite for Kinesis event parsing functionality."""

    def test_parse_valid_single_event(self):
        """
        🔴 RED: Test parsing a single valid Kinesis event.

        Given: A Kinesis event with valid base64-encoded JSON
        When: parse_kinesis_events() is called
        Then: Returns a list with one decoded event dict
        """
        # Arrange
        event_data = {"event_type": "page_view", "user_id": "user123", "timestamp": "2024-12-19T10:00:00Z"}
        encoded_data = base64.b64encode(json.dumps(event_data).encode('utf-8')).decode('utf-8')

        kinesis_event = {
            "Records": [
                {
                    "kinesis": {
                        "data": encoded_data,
                        "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
                        "partitionKey": "user123"
                    },
                    "eventID": "shardId-000000000000:49590338271490256608559692538361571095921575989136588898",
                    "eventSource": "aws:kinesis",
                    "eventVersion": "1.0",
                    "eventName": "aws:kinesis:record",
                    "invokeIdentityArn": "arn:aws:iam::EXAMPLE",
                    "awsRegion": "us-west-2",
                    "eventSourceARN": "arn:aws:kinesis:us-west-2:EXAMPLE:stream/test"
                }
            ]
        }

        # Import will fail initially (RED phase)
        from event_parser import parse_kinesis_events

        # Act
        parsed_events = parse_kinesis_events(kinesis_event)

        # Assert
        assert len(parsed_events) == 1
        assert parsed_events[0] == event_data
        assert parsed_events[0]["event_type"] == "page_view"
        assert parsed_events[0]["user_id"] == "user123"

    def test_parse_multiple_events_in_batch(self):
        """
        🔴 RED: Test parsing multiple events in a single Kinesis batch.

        Given: A Kinesis event with 3 records
        When: parse_kinesis_events() is called
        Then: Returns a list with 3 decoded event dicts
        """
        # Arrange
        events_data = [
            {"event_type": "page_view", "user_id": "user1"},
            {"event_type": "button_click", "user_id": "user2"},
            {"event_type": "purchase", "user_id": "user3", "value": 99.99}
        ]

        records = []
        for event_data in events_data:
            encoded_data = base64.b64encode(json.dumps(event_data).encode('utf-8')).decode('utf-8')
            records.append({
                "kinesis": {
                    "data": encoded_data,
                    "sequenceNumber": f"seq-{len(records)}",
                    "partitionKey": event_data["user_id"]
                }
            })

        kinesis_event = {"Records": records}

        from event_parser import parse_kinesis_events

        # Act
        parsed_events = parse_kinesis_events(kinesis_event)

        # Assert
        assert len(parsed_events) == 3
        assert parsed_events[0]["event_type"] == "page_view"
        assert parsed_events[1]["event_type"] == "button_click"
        assert parsed_events[2]["event_type"] == "purchase"
        assert parsed_events[2]["value"] == 99.99

    def test_parse_malformed_base64_returns_error(self):
        """
        🔴 RED: Test handling of malformed base64 data.

        Given: A Kinesis event with invalid base64
        When: parse_kinesis_events() is called
        Then: Raises ValueError with descriptive message
        """
        # Arrange
        kinesis_event = {
            "Records": [
                {
                    "kinesis": {
                        "data": "not-valid-base64!!!",
                        "sequenceNumber": "seq-1",
                        "partitionKey": "user123"
                    }
                }
            ]
        }

        from event_parser import parse_kinesis_events

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to decode base64 data"):
            parse_kinesis_events(kinesis_event)

    def test_parse_invalid_json_returns_error(self):
        """
        🔴 RED: Test handling of invalid JSON in decoded data.

        Given: A Kinesis event with valid base64 but invalid JSON
        When: parse_kinesis_events() is called
        Then: Raises ValueError with descriptive message
        """
        # Arrange
        invalid_json = "{ not valid json }"
        encoded_data = base64.b64encode(invalid_json.encode('utf-8')).decode('utf-8')

        kinesis_event = {
            "Records": [
                {
                    "kinesis": {
                        "data": encoded_data,
                        "sequenceNumber": "seq-1",
                        "partitionKey": "user123"
                    }
                }
            ]
        }

        from event_parser import parse_kinesis_events

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            parse_kinesis_events(kinesis_event)

    def test_parse_empty_records_returns_empty_list(self):
        """
        🔴 RED: Test handling of empty Records array.

        Given: A Kinesis event with empty Records
        When: parse_kinesis_events() is called
        Then: Returns empty list
        """
        # Arrange
        kinesis_event = {"Records": []}

        from event_parser import parse_kinesis_events

        # Act
        parsed_events = parse_kinesis_events(kinesis_event)

        # Assert
        assert parsed_events == []
        assert len(parsed_events) == 0

    def test_parse_partial_batch_failure_continues_processing(self):
        """
        🔴 RED: Test that one bad record doesn't stop processing of good records.

        Given: A Kinesis batch with 1 invalid and 2 valid records
        When: parse_kinesis_events() is called with skip_errors=True
        Then: Returns 2 valid events and logs error for invalid one
        """
        # Arrange
        valid_event_1 = {"event_type": "page_view", "user_id": "user1"}
        valid_event_2 = {"event_type": "button_click", "user_id": "user2"}

        records = [
            {
                "kinesis": {
                    "data": base64.b64encode(json.dumps(valid_event_1).encode('utf-8')).decode('utf-8'),
                    "sequenceNumber": "seq-1",
                    "partitionKey": "user1"
                }
            },
            {
                "kinesis": {
                    "data": "invalid-base64!!!",  # This one will fail
                    "sequenceNumber": "seq-2",
                    "partitionKey": "user-bad"
                }
            },
            {
                "kinesis": {
                    "data": base64.b64encode(json.dumps(valid_event_2).encode('utf-8')).decode('utf-8'),
                    "sequenceNumber": "seq-3",
                    "partitionKey": "user2"
                }
            }
        ]

        kinesis_event = {"Records": records}

        from event_parser import parse_kinesis_events

        # Act
        parsed_events, errors = parse_kinesis_events(kinesis_event, skip_errors=True)

        # Assert
        assert len(parsed_events) == 2
        assert len(errors) == 1
        assert parsed_events[0]["user_id"] == "user1"
        assert parsed_events[1]["user_id"] == "user2"
        assert "seq-2" in errors[0]["sequence_number"]

    def test_parse_handles_utf8_encoding(self):
        """
        🔴 RED: Test handling of UTF-8 characters in event data.

        Given: A Kinesis event with UTF-8 characters (emoji, special chars)
        When: parse_kinesis_events() is called
        Then: Returns correctly decoded UTF-8 data
        """
        # Arrange
        event_data = {
            "event_type": "message_sent",
            "user_id": "user123",
            "message": "Hello 👋 World! Special: é, ñ, 中文"
        }
        encoded_data = base64.b64encode(json.dumps(event_data).encode('utf-8')).decode('utf-8')

        kinesis_event = {
            "Records": [
                {
                    "kinesis": {
                        "data": encoded_data,
                        "sequenceNumber": "seq-1",
                        "partitionKey": "user123"
                    }
                }
            ]
        }

        from event_parser import parse_kinesis_events

        # Act
        parsed_events = parse_kinesis_events(kinesis_event)

        # Assert
        assert len(parsed_events) == 1
        assert parsed_events[0]["message"] == "Hello 👋 World! Special: é, ñ, 中文"

    def test_parse_preserves_nested_json_structure(self):
        """
        🔴 RED: Test that nested JSON structures are preserved.

        Given: A Kinesis event with nested objects and arrays
        When: parse_kinesis_events() is called
        Then: Returns data with correct nested structure
        """
        # Arrange
        event_data = {
            "event_type": "purchase",
            "user_id": "user123",
            "cart": {
                "items": [
                    {"id": "item1", "price": 10.00},
                    {"id": "item2", "price": 20.00}
                ],
                "total": 30.00
            },
            "metadata": {
                "source": "mobile_app",
                "version": "1.2.3"
            }
        }
        encoded_data = base64.b64encode(json.dumps(event_data).encode('utf-8')).decode('utf-8')

        kinesis_event = {
            "Records": [
                {
                    "kinesis": {
                        "data": encoded_data,
                        "sequenceNumber": "seq-1",
                        "partitionKey": "user123"
                    }
                }
            ]
        }

        from event_parser import parse_kinesis_events

        # Act
        parsed_events = parse_kinesis_events(kinesis_event)

        # Assert
        assert len(parsed_events) == 1
        assert parsed_events[0]["cart"]["total"] == 30.00
        assert len(parsed_events[0]["cart"]["items"]) == 2
        assert parsed_events[0]["metadata"]["version"] == "1.2.3"
