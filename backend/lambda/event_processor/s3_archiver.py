"""
S3 Archiver for Event Processor Lambda.

This module handles archiving enriched events to S3:
- Batching by size (5MB) and count (1000 events)
- gzip compression for storage efficiency
- Date-based partitioning (year/month/day/hour)
- Error handling and retry logic
- Metadata tagging for easier queries

Follows TDD (Test-Driven Development) - GREEN phase implementation.
"""

import gzip
import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Placeholder for S3 client - will be initialized in Lambda handler
s3_client = None


def create_s3_key(timestamp: str, file_id: Optional[str] = None) -> str:
    """
    Create S3 key with date partitioning.

    Args:
        timestamp: Event timestamp (ISO format string)
        file_id: Optional unique file identifier (UUID generated if not provided)

    Returns:
        S3 key in format: year=YYYY/month=MM/day=DD/hour=HH/events_{uuid}.json.gz
    """
    # Parse timestamp
    if isinstance(timestamp, str):
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    else:
        dt = timestamp

    # Generate unique file ID if not provided
    if not file_id:
        file_id = str(uuid.uuid4())

    # Create partitioned path
    s3_key = (
        f"year={dt.year:04d}/"
        f"month={dt.month:02d}/"
        f"day={dt.day:02d}/"
        f"hour={dt.hour:02d}/"
        f"events_{file_id}.json.gz"
    )

    return s3_key


def compress_events(events: List[Dict[str, Any]]) -> bytes:
    """
    Compress events list to gzip format.

    Args:
        events: List of event dictionaries

    Returns:
        gzip compressed bytes
    """
    # Convert events to JSON string
    json_str = json.dumps(events, default=str)  # default=str handles datetime objects

    # Compress with gzip
    compressed = gzip.compress(json_str.encode('utf-8'))

    return compressed


def archive_to_s3(
    enriched_events: List[Dict[str, Any]],
    bucket: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Archive a batch of enriched events to S3.

    Args:
        enriched_events: List of enriched event dictionaries
        bucket: S3 bucket name
        max_retries: Maximum retry attempts for transient failures

    Returns:
        Result dictionary with success status, S3 URI, and metadata
    """
    if not enriched_events:
        return {"success": False, "error": "No events to archive"}

    # Use timestamp from first event for partitioning
    timestamp = enriched_events[0].get("timestamp")
    if not timestamp:
        return {"success": False, "error": "Missing timestamp in events"}

    # Generate unique file ID
    file_id = str(uuid.uuid4())

    # Create S3 key with partitioning
    s3_key = create_s3_key(timestamp, file_id)

    # Compress events
    try:
        compressed_data = compress_events(enriched_events)
    except Exception as e:
        logger.error(f"Failed to compress events: {e}")
        return {"success": False, "error": f"Compression failed: {str(e)}"}

    # Attempt upload with retries
    retries = 0
    last_error = None

    for attempt in range(max_retries):
        try:
            # Upload to S3
            response = s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=compressed_data,
                ContentType="application/json",
                ContentEncoding="gzip",
                Metadata={
                    "event_count": str(len(enriched_events)),
                    "compression": "gzip",
                    "upload_timestamp": datetime.utcnow().isoformat()
                }
            )

            # Check response
            status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
            if status_code == 200:
                logger.info(f"Archived {len(enriched_events)} events to s3://{bucket}/{s3_key}")
                return {
                    "success": True,
                    "s3_uri": f"s3://{bucket}/{s3_key}",
                    "event_count": len(enriched_events),
                    "compressed_size": len(compressed_data),
                    "retries": retries
                }
            else:
                last_error = f"Unexpected status code: {status_code}"

        except Exception as e:
            last_error = str(e)
            logger.warning(f"S3 upload attempt {attempt + 1} failed: {e}")
            retries += 1

            # If not last attempt, continue to retry
            if attempt < max_retries - 1:
                continue
            else:
                # Max retries exhausted
                break

    # All retries failed
    logger.error(f"Failed to archive events after {max_retries} attempts: {last_error}")
    return {
        "success": False,
        "error": last_error,
        "retries": retries
    }


def archive_to_s3_batched(
    enriched_events: List[Dict[str, Any]],
    bucket: str,
    max_batch_size: int = 1000,
    max_batch_size_mb: float = 5.0
) -> Dict[str, Any]:
    """
    Archive events to S3 in multiple batches.

    Args:
        enriched_events: List of enriched event dictionaries
        bucket: S3 bucket name
        max_batch_size: Maximum events per batch
        max_batch_size_mb: Maximum batch size in MB

    Returns:
        Summary with batches_created, total_events, successes, failures
    """
    # Group events by hour for better partitioning
    events_by_hour = defaultdict(list)

    for event in enriched_events:
        timestamp = event.get("timestamp")
        if not timestamp:
            logger.warning(f"Skipping event {event.get('event_id')} - missing timestamp")
            continue

        # Parse timestamp and group by hour
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        hour_key = dt.strftime("%Y-%m-%d-%H")
        events_by_hour[hour_key].append(event)

    # Process each hour group
    batches_created = 0
    total_uploaded = 0
    failures = 0

    for hour_key, hour_events in events_by_hour.items():
        # Split into batches by count and size
        current_batch = []
        current_batch_size = 0
        max_bytes = int(max_batch_size_mb * 1024 * 1024)

        for event in hour_events:
            event_size = len(json.dumps(event, default=str).encode('utf-8'))

            # Check if adding this event would exceed limits
            if len(current_batch) >= max_batch_size or \
               (current_batch_size + event_size) > max_bytes:

                # Archive current batch
                if current_batch:
                    result = archive_to_s3(current_batch, bucket)
                    batches_created += 1

                    if result["success"]:
                        total_uploaded += len(current_batch)
                    else:
                        failures += 1
                        logger.error(f"Failed to archive batch: {result.get('error')}")

                    # Reset batch
                    current_batch = []
                    current_batch_size = 0

            # Add event to current batch
            current_batch.append(event)
            current_batch_size += event_size

        # Archive remaining events in current batch
        if current_batch:
            result = archive_to_s3(current_batch, bucket)
            batches_created += 1

            if result["success"]:
                total_uploaded += len(current_batch)
            else:
                failures += 1
                logger.error(f"Failed to archive batch: {result.get('error')}")

    return {
        "batches_created": batches_created,
        "total_events": len(enriched_events),
        "uploaded_events": total_uploaded,
        "failures": failures,
        "success": failures == 0
    }
