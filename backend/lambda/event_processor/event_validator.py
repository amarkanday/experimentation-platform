"""
Event Schema Validator for Event Processor Lambda.

This module validates parsed events using Pydantic models from shared module:
- Type checking and validation
- Required field enforcement
- Batch validation support
- Duplicate detection

Follows TDD (Test-Driven Development) - GREEN phase implementation.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from pydantic import ValidationError
import logging

# Add shared module to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from models import EventData

logger = logging.getLogger(__name__)


def validate_event(event_dict: Dict[str, Any]) -> EventData:
    """
    Validate a single event using Pydantic EventData model.

    Args:
        event_dict: Dictionary containing event data

    Returns:
        EventData: Validated event object

    Raises:
        ValidationError: If validation fails (missing fields, wrong types, etc.)
    """
    try:
        validated_event = EventData(**event_dict)
        return validated_event
    except ValidationError as e:
        logger.error(f"Event validation failed for event_id={event_dict.get('event_id', 'unknown')}: {e}")
        raise


def validate_events_batch(
    events_batch: List[Dict[str, Any]],
    skip_invalid: bool = False,
    check_duplicates: bool = False
) -> Tuple[List[EventData], List[Dict[str, Any]]]:
    """
    Validate a batch of events.

    Args:
        events_batch: List of event dictionaries to validate
        skip_invalid: If True, skip invalid events and return them separately
        check_duplicates: If True, check for duplicate event_ids

    Returns:
        If skip_invalid=False: List of validated EventData objects
        If skip_invalid=True: Tuple of (valid_events, validation_errors)

    Raises:
        ValidationError: If skip_invalid=False and any event fails validation
    """
    validated_events = []
    validation_errors = []
    seen_event_ids = set()

    for event_dict in events_batch:
        try:
            # Validate the event
            validated_event = EventData(**event_dict)

            # Check for duplicates if requested
            if check_duplicates:
                event_id = validated_event.event_id
                if event_id in seen_event_ids:
                    error_dict = {
                        "event_id": event_id,
                        "error": f"Duplicate event_id: {event_id}",
                        "event_data": event_dict
                    }
                    logger.warning(f"Duplicate event_id detected: {event_id}")

                    if skip_invalid:
                        validation_errors.append(error_dict)
                        continue
                    else:
                        raise ValidationError(f"Duplicate event_id: {event_id}", model=EventData)

                seen_event_ids.add(event_id)

            validated_events.append(validated_event)

        except ValidationError as e:
            event_id = event_dict.get("event_id", "unknown")
            error_dict = {
                "event_id": event_id,
                "error": str(e),
                "event_data": event_dict
            }

            logger.error(f"Validation failed for event {event_id}: {e}")

            if skip_invalid:
                validation_errors.append(error_dict)
            else:
                raise

        except Exception as e:
            # Unexpected error
            event_id = event_dict.get("event_id", "unknown")
            error_dict = {
                "event_id": event_id,
                "error": f"Unexpected error: {str(e)}",
                "event_data": event_dict
            }

            logger.error(f"Unexpected error validating event {event_id}: {e}")

            if skip_invalid:
                validation_errors.append(error_dict)
            else:
                raise

    if skip_invalid:
        return validated_events, validation_errors

    # Return only validated_events when skip_invalid=False
    return validated_events
