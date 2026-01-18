"""
Unit tests for S3 archival - Event Processor Lambda.

This module tests archiving enriched events to S3:
- Event batching by size/time limits
- gzip compression
- Date-based partitioning (year/month/day/hour)
- Error handling for S3 upload failures
- Retry logic

Test-Driven Development (TDD) - RED phase:
- Write tests first, implementation follows
"""

import pytest
import gzip
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any


class TestS3Archival:
    """Test suite for S3 archival functionality."""

    def test_archive_events_to_s3_with_date_partitioning(self):
        """
        🔴 RED: Test that events are archived to S3 with date-based partitioning.

        Given: A batch of enriched events from 2024-12-19
        When: archive_to_s3() is called
        Then: Events uploaded to s3://bucket/year=2024/month=12/day=19/hour=10/
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_1",
                "event_type": "page_view",
                "user_id": "user_1",
                "timestamp": "2024-12-19T10:30:00Z"
            },
            {
                "event_id": "evt_2",
                "event_type": "conversion",
                "user_id": "user_2",
                "timestamp": "2024-12-19T10:31:00Z"
            }
        ]

        from s3_archiver import archive_to_s3

        # Act
        with patch('s3_archiver.s3_client') as mock_s3:
            mock_s3.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
            result = archive_to_s3(enriched_events, bucket="event-archive")

        # Assert
        assert mock_s3.put_object.called
        call_args = mock_s3.put_object.call_args[1]
        s3_key = call_args["Key"]

        # Verify date partitioning
        assert "year=2024" in s3_key
        assert "month=12" in s3_key
        assert "day=19" in s3_key
        assert "hour=10" in s3_key
        assert result["success"] is True

    def test_archive_events_compressed_with_gzip(self):
        """
        🔴 RED: Test that events are compressed with gzip before upload.

        Given: A batch of enriched events
        When: archive_to_s3() is called
        Then: Data is gzip compressed and uploadable
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_compress",
                "event_type": "page_view",
                "user_id": "user_compress",
                "timestamp": "2024-12-19T10:30:00Z",
                "properties": {"large_data": "x" * 1000}  # Some data to compress
            }
        ]

        from s3_archiver import archive_to_s3

        # Act
        with patch('s3_archiver.s3_client') as mock_s3:
            mock_s3.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
            result = archive_to_s3(enriched_events, bucket="event-archive")

        # Assert
        call_args = mock_s3.put_object.call_args[1]
        uploaded_body = call_args["Body"]

        # Verify it's gzip compressed (can decompress)
        decompressed = gzip.decompress(uploaded_body)
        events_list = json.loads(decompressed.decode('utf-8'))
        assert len(events_list) == 1
        assert events_list[0]["event_id"] == "evt_compress"

    def test_archive_batches_events_by_max_count(self):
        """
        🔴 RED: Test that events are batched by maximum count (1000 events).

        Given: 2500 enriched events
        When: archive_to_s3_batched() is called
        Then: Creates 3 batches (1000, 1000, 500)
        """
        # Arrange
        enriched_events = [
            {
                "event_id": f"evt_{i}",
                "event_type": "page_view",
                "user_id": f"user_{i}",
                "timestamp": "2024-12-19T10:30:00Z"
            }
            for i in range(2500)
        ]

        from s3_archiver import archive_to_s3_batched

        # Act
        with patch('s3_archiver.s3_client') as mock_s3:
            mock_s3.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
            result = archive_to_s3_batched(
                enriched_events,
                bucket="event-archive",
                max_batch_size=1000
            )

        # Assert
        assert mock_s3.put_object.call_count == 3
        assert result["batches_created"] == 3
        assert result["total_events"] == 2500

    def test_archive_batches_events_by_max_size(self):
        """
        🔴 RED: Test that events are batched by maximum size (5MB).

        Given: Events that would exceed 5MB in a single batch
        When: archive_to_s3_batched() is called
        Then: Creates multiple batches to stay under size limit
        """
        # Arrange - Create events with large payloads
        enriched_events = [
            {
                "event_id": f"evt_{i}",
                "event_type": "page_view",
                "user_id": f"user_{i}",
                "timestamp": "2024-12-19T10:30:00Z",
                "properties": {"large_data": "x" * 10000}  # ~10KB per event
            }
            for i in range(600)  # ~6MB total
        ]

        from s3_archiver import archive_to_s3_batched

        # Act
        with patch('s3_archiver.s3_client') as mock_s3:
            mock_s3.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
            result = archive_to_s3_batched(
                enriched_events,
                bucket="event-archive",
                max_batch_size_mb=5
            )

        # Assert
        # Should create at least 2 batches due to size constraint
        assert mock_s3.put_object.call_count >= 2
        assert result["batches_created"] >= 2

    def test_archive_creates_unique_filenames_with_timestamp(self):
        """
        🔴 RED: Test that S3 keys include unique timestamp/UUID.

        Given: Multiple batches of events
        When: archive_to_s3() is called multiple times
        Then: Each file has unique name to prevent overwrites
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_unique",
                "event_type": "page_view",
                "user_id": "user_unique",
                "timestamp": "2024-12-19T10:30:00Z"
            }
        ]

        from s3_archiver import archive_to_s3

        # Act - Upload twice
        with patch('s3_archiver.s3_client') as mock_s3:
            mock_s3.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
            result1 = archive_to_s3(enriched_events, bucket="event-archive")
            result2 = archive_to_s3(enriched_events, bucket="event-archive")

        # Assert
        assert mock_s3.put_object.call_count == 2
        call_args_list = mock_s3.put_object.call_args_list
        key1 = call_args_list[0][1]["Key"]
        key2 = call_args_list[1][1]["Key"]

        # Keys should be different
        assert key1 != key2

    def test_archive_handles_s3_upload_errors_gracefully(self):
        """
        🔴 RED: Test that S3 upload errors are handled gracefully.

        Given: A batch of enriched events
        When: S3 put_object raises an exception
        Then: Error is logged and returned in result
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_error",
                "event_type": "page_view",
                "user_id": "user_error",
                "timestamp": "2024-12-19T10:30:00Z"
            }
        ]

        from s3_archiver import archive_to_s3

        # Act
        with patch('s3_archiver.s3_client') as mock_s3:
            mock_s3.put_object.side_effect = Exception("S3 error: Access Denied")
            result = archive_to_s3(enriched_events, bucket="event-archive")

        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "S3 error" in result["error"]

    def test_archive_retries_on_transient_failures(self):
        """
        🔴 RED: Test retry logic for transient S3 failures.

        Given: A batch of enriched events
        When: S3 upload fails twice then succeeds
        Then: Operation is retried and eventually succeeds
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_retry",
                "event_type": "page_view",
                "user_id": "user_retry",
                "timestamp": "2024-12-19T10:30:00Z"
            }
        ]

        from s3_archiver import archive_to_s3

        # Act - Mock first two calls fail, third succeeds
        with patch('s3_archiver.s3_client') as mock_s3:
            mock_s3.put_object.side_effect = [
                Exception("Temporary error"),
                Exception("Temporary error"),
                {"ResponseMetadata": {"HTTPStatusCode": 200}}
            ]
            result = archive_to_s3(
                enriched_events,
                bucket="event-archive",
                max_retries=3
            )

        # Assert
        assert mock_s3.put_object.call_count == 3
        assert result["success"] is True
        assert result.get("retries") == 2

    def test_archive_groups_events_by_hour_for_partitioning(self):
        """
        🔴 RED: Test that events from different hours go to different partitions.

        Given: Events spanning multiple hours
        When: archive_to_s3_batched() is called
        Then: Separate S3 keys created for each hour
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_10am",
                "event_type": "page_view",
                "user_id": "user_1",
                "timestamp": "2024-12-19T10:30:00Z"  # 10am
            },
            {
                "event_id": "evt_11am",
                "event_type": "page_view",
                "user_id": "user_2",
                "timestamp": "2024-12-19T11:15:00Z"  # 11am
            },
            {
                "event_id": "evt_10am_2",
                "event_type": "page_view",
                "user_id": "user_3",
                "timestamp": "2024-12-19T10:45:00Z"  # 10am
            }
        ]

        from s3_archiver import archive_to_s3_batched

        # Act
        with patch('s3_archiver.s3_client') as mock_s3:
            mock_s3.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
            result = archive_to_s3_batched(enriched_events, bucket="event-archive")

        # Assert - Should create 2 batches (one for 10am, one for 11am)
        assert mock_s3.put_object.call_count == 2
        call_args_list = mock_s3.put_object.call_args_list

        key_1 = call_args_list[0][1]["Key"]
        key_2 = call_args_list[1][1]["Key"]

        # One should have hour=10, other should have hour=11
        assert ("hour=10" in key_1 and "hour=11" in key_2) or \
               ("hour=10" in key_2 and "hour=11" in key_1)

    def test_archive_includes_metadata_in_s3_object(self):
        """
        🔴 RED: Test that S3 objects include useful metadata.

        Given: A batch of enriched events
        When: archive_to_s3() is called
        Then: S3 object has metadata (event_count, compression, timestamp)
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_meta",
                "event_type": "page_view",
                "user_id": "user_meta",
                "timestamp": "2024-12-19T10:30:00Z"
            }
        ]

        from s3_archiver import archive_to_s3

        # Act
        with patch('s3_archiver.s3_client') as mock_s3:
            mock_s3.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
            result = archive_to_s3(enriched_events, bucket="event-archive")

        # Assert
        call_args = mock_s3.put_object.call_args[1]
        metadata = call_args.get("Metadata", {})

        assert "event_count" in metadata
        assert metadata["event_count"] == "1"
        assert "compression" in metadata
        assert metadata["compression"] == "gzip"

    def test_archive_returns_s3_location_in_result(self):
        """
        🔴 RED: Test that archive result includes S3 location.

        Given: A batch of enriched events
        When: archive_to_s3() is called
        Then: Result includes full S3 URI
        """
        # Arrange
        enriched_events = [
            {
                "event_id": "evt_location",
                "event_type": "page_view",
                "user_id": "user_location",
                "timestamp": "2024-12-19T10:30:00Z"
            }
        ]

        from s3_archiver import archive_to_s3

        # Act
        with patch('s3_archiver.s3_client') as mock_s3:
            mock_s3.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
            result = archive_to_s3(enriched_events, bucket="event-archive")

        # Assert
        assert "s3_uri" in result
        assert result["s3_uri"].startswith("s3://event-archive/")
