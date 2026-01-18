"""
Kinesis Event Parser for Event Processor Lambda.

This module handles parsing and decoding of Kinesis stream events including:
- Base64 decoding
- JSON parsing
- Batch processing
- Error handling

Follows TDD (Test-Driven Development) - GREEN phase implementation.
"""

import base64
import json
import logging
from typing import List, Dict, Any, Tuple, Union

logger = logging.getLogger(__name__)


def parse_kinesis_events(
    kinesis_event: Dict[str, Any],
    skip_errors: bool = False
) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]]:
    """
    Parse and decode Kinesis stream events from base64-encoded JSON.

    Args:
        kinesis_event: The Kinesis event from Lambda trigger containing Records
        skip_errors: If True, skip invalid records and return errors separately

    Returns:
        If skip_errors=False: List of parsed event dictionaries
        If skip_errors=True: Tuple of (parsed_events, errors)

    Raises:
        ValueError: If base64 decoding or JSON parsing fails (when skip_errors=False)
    """
    records = kinesis_event.get("Records", [])

    if not records:
        if skip_errors:
            return [], []
        return []

    parsed_events = []
    errors = []

    for record in records:
        try:
            # Extract Kinesis data
            kinesis_data = record.get("kinesis", {})
            encoded_data = kinesis_data.get("data", "")
            sequence_number = kinesis_data.get("sequenceNumber", "unknown")

            # Decode base64
            try:
                decoded_bytes = base64.b64decode(encoded_data)
            except Exception as e:
                error_msg = f"Failed to decode base64 data for sequence {sequence_number}: {str(e)}"
                logger.error(error_msg)
                if skip_errors:
                    errors.append({
                        "sequence_number": sequence_number,
                        "error": "base64_decode_error",
                        "message": error_msg
                    })
                    continue
                raise ValueError(error_msg)

            # Decode UTF-8
            try:
                decoded_str = decoded_bytes.decode('utf-8')
            except UnicodeDecodeError as e:
                error_msg = f"Failed to decode UTF-8 for sequence {sequence_number}: {str(e)}"
                logger.error(error_msg)
                if skip_errors:
                    errors.append({
                        "sequence_number": sequence_number,
                        "error": "utf8_decode_error",
                        "message": error_msg
                    })
                    continue
                raise ValueError(error_msg)

            # Parse JSON
            try:
                event_data = json.loads(decoded_str)
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON for sequence {sequence_number}: {str(e)}"
                logger.error(error_msg)
                if skip_errors:
                    errors.append({
                        "sequence_number": sequence_number,
                        "error": "json_parse_error",
                        "message": error_msg
                    })
                    continue
                raise ValueError(error_msg)

            # Successfully parsed - add to results
            parsed_events.append(event_data)

        except Exception as e:
            # Unexpected error
            if not skip_errors:
                raise
            sequence_num = record.get("kinesis", {}).get("sequenceNumber", "unknown")
            errors.append({
                "sequence_number": sequence_num,
                "error": "unexpected_error",
                "message": str(e)
            })

    if skip_errors:
        return parsed_events, errors

    return parsed_events
