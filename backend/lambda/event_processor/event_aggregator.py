"""
Event Aggregator for Event Processor Lambda.

This module provides real-time metric aggregation to DynamoDB:
- Atomic counter increments for event counts
- Unique user tracking per experiment/variant
- Time-windowed aggregation (hourly, daily)
- Conditional writes to prevent race conditions
- Retry logic for concurrent updates

Follows TDD (Test-Driven Development) - GREEN phase implementation.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Placeholder for DynamoDB table - will be initialized in Lambda handler
dynamodb_table = None


def create_aggregation_key(
    experiment_id: str,
    variant: str,
    timestamp: str,
    window: str = "hourly"
) -> str:
    """
    Create aggregation partition key from experiment, variant, and time window.

    Args:
        experiment_id: Experiment identifier
        variant: Variant key
        timestamp: Event timestamp (ISO format string)
        window: Time window - 'hourly' or 'daily'

    Returns:
        Partition key string in format:
        - Hourly: "exp_{id}#variant#{variant}#hour#{YYYY-MM-DD-HH}"
        - Daily: "exp_{id}#variant#{variant}#day#{YYYY-MM-DD}"
    """
    # Parse timestamp
    if isinstance(timestamp, str):
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    else:
        dt = timestamp

    # Create time window suffix
    if window == "hourly":
        time_suffix = dt.strftime("%Y-%m-%d-%H")
        window_key = "hour"
    elif window == "daily":
        time_suffix = dt.strftime("%Y-%m-%d")
        window_key = "day"
    else:
        raise ValueError(f"Invalid window: {window}. Must be 'hourly' or 'daily'")

    # Create partition key
    partition_key = f"exp_{experiment_id}#variant#{variant}#{window_key}#{time_suffix}"

    return partition_key


def aggregate_event(
    enriched_event: Dict[str, Any],
    window: str = "hourly",
    max_retries: int = 3
) -> Optional[Dict[str, Any]]:
    """
    Aggregate a single enriched event to DynamoDB.

    Args:
        enriched_event: Enriched event dictionary
        window: Time window for aggregation ('hourly' or 'daily')
        max_retries: Maximum retry attempts for conditional write failures

    Returns:
        Aggregation result with updated counts, or None if skipped

    Flow:
        1. Check if event has experiment_id and variant
        2. Create aggregation key from experiment, variant, time window
        3. Use atomic DynamoDB update with ADD operation
        4. Retry on conditional check failures
        5. Return updated counts
    """
    # Skip events without experiment_id or variant
    experiment_id = enriched_event.get('experiment_id')
    variant = enriched_event.get('variant')

    if not experiment_id or not variant:
        logger.debug(f"Skipping aggregation for event {enriched_event.get('event_id')} - no experiment/variant")
        return {"skipped": True}

    # Create partition key
    timestamp = enriched_event.get('timestamp')
    partition_key = create_aggregation_key(experiment_id, variant, timestamp, window)

    # Event type for sort key
    event_type = enriched_event.get('event_type', 'unknown')
    sort_key = f"event_type#{event_type}"

    # User ID for unique user tracking
    user_id = enriched_event.get('user_id')

    # Attempt update with retries
    for attempt in range(max_retries):
        try:
            # Use DynamoDB atomic ADD operation
            update_expression = "ADD event_count :inc"
            expression_attribute_values = {":inc": 1}

            # Add unique user to set (if provided)
            if user_id:
                update_expression += ", unique_user_ids :user_set"
                expression_attribute_values[":user_set"] = {user_id}

            # Perform atomic update
            response = dynamodb_table.update_item(
                Key={
                    "partition_key": partition_key,
                    "sort_key": sort_key
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW"
            )

            # Extract updated attributes
            attributes = response.get("Attributes", {})
            result = {
                "event_count": attributes.get("event_count", 0),
                "unique_users": len(attributes.get("unique_user_ids", set())),
                "partition_key": partition_key
            }

            logger.debug(f"Aggregated event {enriched_event.get('event_id')} to {partition_key}")
            return result

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")

            if error_code == "ConditionalCheckFailedException" and attempt < max_retries - 1:
                # Retry on conditional check failure
                logger.warning(f"Conditional check failed, retrying ({attempt + 1}/{max_retries})")
                continue
            else:
                # Re-raise for other errors or max retries exceeded
                logger.error(f"Failed to aggregate event {enriched_event.get('event_id')}: {e}")
                raise

        except Exception as e:
            logger.error(f"Unexpected error aggregating event {enriched_event.get('event_id')}: {e}")
            raise

    # Should not reach here, but return None if all retries exhausted
    return None


def aggregate_events_batch(
    enriched_events: List[Dict[str, Any]],
    window: str = "hourly",
    return_summary: bool = False
) -> Any:
    """
    Aggregate a batch of enriched events to DynamoDB.

    Args:
        enriched_events: List of enriched event dictionaries
        window: Time window for aggregation ('hourly' or 'daily')
        return_summary: If True, return summary dict instead of individual results

    Returns:
        If return_summary=False: List of aggregation results
        If return_summary=True: Dict with success_count, failure_count, total_events
    """
    results = []
    success_count = 0
    failure_count = 0

    for event in enriched_events:
        try:
            result = aggregate_event(event, window=window)

            if result and not result.get("skipped"):
                success_count += 1
            results.append(result)

        except Exception as e:
            logger.error(f"Failed to aggregate event {event.get('event_id')}: {e}")
            failure_count += 1
            results.append({"error": str(e)})

    if return_summary:
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "total_events": len(enriched_events),
            "results": results
        }

    return results
