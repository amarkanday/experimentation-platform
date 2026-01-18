"""
Event Enricher for Event Processor Lambda.

This module enriches validated events with:
- Assignment data from DynamoDB (user's experiment variant)
- Experiment metadata (name, key, status)
- Derived fields (time since assignment, etc.)
- Graceful handling of missing data

Follows TDD (Test-Driven Development) - GREEN phase implementation.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Add shared module to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from models import EventData

logger = logging.getLogger(__name__)


def fetch_assignment_from_dynamodb(user_id: str, experiment_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user assignment from DynamoDB.

    Args:
        user_id: User identifier
        experiment_id: Experiment identifier

    Returns:
        Assignment dict or None if not found

    Note: This is a placeholder. Real implementation will use boto3 DynamoDB client.
    """
    # Placeholder - will be implemented when DynamoDB integration is added
    # In real implementation, this would query DynamoDB assignments table
    logger.debug(f"Fetching assignment for user_id={user_id}, experiment_id={experiment_id}")
    return None


def fetch_experiment_metadata(experiment_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch experiment metadata from DynamoDB or cache.

    Args:
        experiment_id: Experiment identifier

    Returns:
        Experiment metadata dict or None if not found

    Note: This is a placeholder. Real implementation will use boto3 DynamoDB client.
    """
    # Placeholder - will be implemented when DynamoDB integration is added
    logger.debug(f"Fetching experiment metadata for experiment_id={experiment_id}")
    return None


def calculate_time_since_assignment(
    event_timestamp: datetime,
    assignment_timestamp: str
) -> int:
    """
    Calculate time elapsed since assignment in seconds.

    Args:
        event_timestamp: Event timestamp (datetime object)
        assignment_timestamp: Assignment timestamp (ISO string)

    Returns:
        Seconds elapsed between assignment and event
    """
    # Parse assignment timestamp
    if isinstance(assignment_timestamp, str):
        assignment_dt = datetime.fromisoformat(assignment_timestamp.replace('Z', '+00:00'))
    else:
        assignment_dt = assignment_timestamp

    # Calculate difference
    time_delta = event_timestamp - assignment_dt
    return int(time_delta.total_seconds())


def enrich_event(validated_event: EventData) -> Dict[str, Any]:
    """
    Enrich a validated event with assignment and experiment data.

    Args:
        validated_event: Validated EventData object from Pydantic

    Returns:
        Enriched event dictionary with additional fields

    Flow:
        1. Convert Pydantic model to dict
        2. If experiment_id exists, fetch assignment
        3. If assignment exists, add assignment data and calculate derived fields
        4. If experiment_id exists, fetch experiment metadata
        5. Handle errors gracefully, preserving original data
    """
    # Convert Pydantic model to dict
    enriched = validated_event.model_dump()

    # Convert datetime to ISO string for JSON serialization
    if isinstance(enriched.get('timestamp'), datetime):
        enriched['timestamp'] = enriched['timestamp'].isoformat()

    experiment_id = enriched.get('experiment_id')

    # If no experiment_id, return as-is
    if not experiment_id:
        return enriched

    try:
        # Fetch assignment data
        assignment = fetch_assignment_from_dynamodb(
            enriched['user_id'],
            experiment_id
        )

        if assignment:
            # Add assignment fields
            enriched['assignment_id'] = assignment.get('assignment_id')
            enriched['variant'] = assignment.get('variant')

            # Calculate derived fields
            if 'timestamp' in assignment:
                try:
                    time_since = calculate_time_since_assignment(
                        validated_event.timestamp,
                        assignment['timestamp']
                    )
                    enriched['time_since_assignment_seconds'] = time_since
                except Exception as e:
                    logger.warning(f"Failed to calculate time_since_assignment: {e}")

        # Fetch experiment metadata
        experiment_metadata = fetch_experiment_metadata(experiment_id)

        if experiment_metadata:
            enriched['experiment_key'] = experiment_metadata.get('key')
            enriched['experiment_name'] = experiment_metadata.get('name')
            enriched['experiment_status'] = experiment_metadata.get('status')

    except Exception as e:
        # Log error but don't fail - preserve original event data
        logger.error(f"Error enriching event {enriched.get('event_id', 'unknown')}: {e}")
        enriched['enrichment_error'] = True

    return enriched


def enrich_events_batch(validated_events: List[EventData]) -> List[Dict[str, Any]]:
    """
    Enrich a batch of validated events.

    Args:
        validated_events: List of validated EventData objects

    Returns:
        List of enriched event dictionaries

    Note: Processes events sequentially. Future optimization could batch
          DynamoDB queries for better performance.
    """
    enriched_events = []

    for event in validated_events:
        try:
            enriched_event = enrich_event(event)
            enriched_events.append(enriched_event)
        except Exception as e:
            # Even if enrichment fails completely, preserve the original event
            logger.error(f"Failed to enrich event {event.event_id}: {e}")
            event_dict = event.model_dump()
            if isinstance(event_dict.get('timestamp'), datetime):
                event_dict['timestamp'] = event_dict['timestamp'].isoformat()
            event_dict['enrichment_error'] = True
            enriched_events.append(event_dict)

    return enriched_events
