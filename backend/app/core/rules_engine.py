"""
Rules engine for evaluating targeting rules.

This module provides functions for evaluating targeting rules against user contexts.
"""

import re
import logging
import hashlib
import math
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, time as datetime_time
import semver
try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False

from backend.app.schemas.targeting_rule import (
    LogicalOperator,
    OperatorType,
    Condition,
    RuleGroup,
    TargetingRule,
    TargetingRules,
)

logger = logging.getLogger(__name__)

# Type alias for user context
UserContext = Dict[str, Any]


def evaluate_targeting_rules(targeting_rules: TargetingRules, user_context: UserContext) -> Optional[TargetingRule]:
    """
    Evaluate a set of targeting rules against a user context.
    Returns the first matching rule, or None if no rules match.

    Args:
        targeting_rules: The full targeting rules configuration
        user_context: Dictionary containing user attributes

    Returns:
        The first matching targeting rule, or None if no rules match
    """
    if not targeting_rules or not targeting_rules.rules:
        return targeting_rules.default_rule

    # Sort rules by priority (lower number = higher priority)
    sorted_rules = sorted(targeting_rules.rules, key=lambda r: r.priority)

    for rule in sorted_rules:
        # Check if rule matches
        if evaluate_rule(rule, user_context):
            # Check rollout percentage
            if should_include_in_rollout(rule, user_context):
                return rule

    # If no rules match, use default rule
    return targeting_rules.default_rule


def evaluate_rule(rule: TargetingRule, user_context: UserContext) -> bool:
    """
    Evaluate if a targeting rule matches a user context.

    Args:
        rule: The targeting rule to evaluate
        user_context: Dictionary containing user attributes

    Returns:
        True if the rule matches, False otherwise
    """
    return evaluate_rule_group(rule.rule, user_context)


def evaluate_rule_group(rule_group: RuleGroup, user_context: UserContext) -> bool:
    """
    Evaluate a rule group against a user context.

    Args:
        rule_group: The rule group to evaluate
        user_context: Dictionary containing user attributes

    Returns:
        True if the rule group matches, False otherwise
    """
    operator = rule_group.operator

    # Evaluate conditions
    condition_results = [evaluate_condition(condition, user_context) for condition in rule_group.conditions]

    # Evaluate nested groups
    if rule_group.groups:
        group_results = [evaluate_rule_group(group, user_context) for group in rule_group.groups]
    else:
        group_results = []

    # Combine all results
    all_results = condition_results + group_results

    # If there are no conditions or groups, return True
    if not all_results:
        return True

    # Apply logical operator
    if operator == LogicalOperator.AND:
        return all(all_results)
    elif operator == LogicalOperator.OR:
        return any(all_results)
    elif operator == LogicalOperator.NOT:
        # NOT operator should negate the combined result of all conditions and groups
        # If there's only one condition/group, simply negate it
        # If there are multiple, assume they're combined with AND
        if len(all_results) == 1:
            return not all_results[0]
        else:
            return not all(all_results)

    # Default fallback
    logger.warning(f"Unknown logical operator: {operator}")
    return False


def evaluate_condition(condition: Condition, user_context: UserContext) -> bool:
    """
    Evaluate a single condition against a user context.

    Args:
        condition: The condition to evaluate
        user_context: Dictionary containing user attributes

    Returns:
        True if the condition matches, False otherwise
    """
    attribute = condition.attribute
    operator = condition.operator
    expected_value = condition.value

    # Get actual value from user context
    if attribute not in user_context:
        logger.debug(f"Attribute {attribute} not found in user context")
        return False

    actual_value = user_context[attribute]

    # Apply operator
    return apply_operator(operator, actual_value, expected_value, condition.additional_value)


def apply_operator(
    operator: OperatorType,
    actual_value: Any,
    expected_value: Any,
    additional_value: Optional[Any] = None
) -> bool:
    """
    Apply an operator to compare actual and expected values.

    Args:
        operator: The operator to apply
        actual_value: The actual value from user context
        expected_value: The expected value from the condition
        additional_value: Additional value for operators that need two values

    Returns:
        True if the operator evaluates to true, False otherwise
    """
    # Handle None values
    if actual_value is None:
        # Only certain operators make sense with None
        if operator == OperatorType.EQUALS:
            return expected_value is None
        elif operator == OperatorType.NOT_EQUALS:
            return expected_value is not None
        elif operator == OperatorType.TIME_WINDOW:
            # For TIME_WINDOW, None means "use current time"
            pass  # Continue to the operator handler
        else:
            return False

    # Simple equality operators
    if operator == OperatorType.EQUALS:
        return actual_value == expected_value
    elif operator == OperatorType.NOT_EQUALS:
        return actual_value != expected_value

    # Collection operators
    elif operator == OperatorType.IN:
        # Check if actual_value is in expected_value (which should be a collection)
        if not isinstance(expected_value, (list, tuple, set)):
            logger.warning(f"Expected value for IN operator should be a collection, got {type(expected_value)}")
            return False
        return actual_value in expected_value
    elif operator == OperatorType.NOT_IN:
        if not isinstance(expected_value, (list, tuple, set)):
            logger.warning(f"Expected value for NOT_IN operator should be a collection, got {type(expected_value)}")
            return False
        return actual_value not in expected_value

    # String operators
    elif operator == OperatorType.CONTAINS:
        # Check if expected_value is in actual_value (string contains)
        if not isinstance(actual_value, str):
            # Convert to string for non-string types
            actual_value = str(actual_value)
        if not isinstance(expected_value, str):
            expected_value = str(expected_value)
        return expected_value in actual_value
    elif operator == OperatorType.NOT_CONTAINS:
        if not isinstance(actual_value, str):
            actual_value = str(actual_value)
        if not isinstance(expected_value, str):
            expected_value = str(expected_value)
        return expected_value not in actual_value
    elif operator == OperatorType.STARTS_WITH:
        if not isinstance(actual_value, str):
            actual_value = str(actual_value)
        if not isinstance(expected_value, str):
            expected_value = str(expected_value)
        return actual_value.startswith(expected_value)
    elif operator == OperatorType.ENDS_WITH:
        if not isinstance(actual_value, str):
            actual_value = str(actual_value)
        if not isinstance(expected_value, str):
            expected_value = str(expected_value)
        return actual_value.endswith(expected_value)
    elif operator == OperatorType.MATCH_REGEX:
        if not isinstance(actual_value, str):
            actual_value = str(actual_value)
        try:
            pattern = re.compile(expected_value)
            return bool(pattern.search(actual_value))
        except (re.error, TypeError):
            logger.warning(f"Invalid regex pattern: {expected_value}")
            return False

    # Numeric comparison operators
    elif operator == OperatorType.GREATER_THAN:
        try:
            return float(actual_value) > float(expected_value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to compare {actual_value} > {expected_value}")
            return False
    elif operator == OperatorType.GREATER_THAN_OR_EQUAL:
        try:
            return float(actual_value) >= float(expected_value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to compare {actual_value} >= {expected_value}")
            return False
    elif operator == OperatorType.LESS_THAN:
        try:
            return float(actual_value) < float(expected_value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to compare {actual_value} < {expected_value}")
            return False
    elif operator == OperatorType.LESS_THAN_OR_EQUAL:
        try:
            return float(actual_value) <= float(expected_value)
        except (ValueError, TypeError):
            logger.warning(f"Failed to compare {actual_value} <= {expected_value}")
            return False

    # Date comparison operators
    elif operator in (OperatorType.BEFORE, OperatorType.AFTER):
        try:
            # Convert to datetime if not already
            if isinstance(actual_value, str):
                actual_date = datetime.fromisoformat(actual_value.replace('Z', '+00:00'))
            elif isinstance(actual_value, (int, float)):
                actual_date = datetime.fromtimestamp(actual_value)
            elif isinstance(actual_value, datetime):
                actual_date = actual_value
            else:
                logger.warning(f"Unsupported date format for actual value: {actual_value}")
                return False

            if isinstance(expected_value, str):
                expected_date = datetime.fromisoformat(expected_value.replace('Z', '+00:00'))
            elif isinstance(expected_value, (int, float)):
                expected_date = datetime.fromtimestamp(expected_value)
            elif isinstance(expected_value, datetime):
                expected_date = expected_value
            else:
                logger.warning(f"Unsupported date format for expected value: {expected_value}")
                return False

            if operator == OperatorType.BEFORE:
                return actual_date < expected_date
            else:  # AFTER
                return actual_date > expected_date

        except (ValueError, TypeError):
            logger.warning(f"Failed to compare dates: {actual_value} and {expected_value}")
            return False

    # Range operators
    elif operator == OperatorType.BETWEEN:
        # Check if value is between expected_value and additional_value
        if additional_value is None:
            logger.warning("BETWEEN operator requires additional_value")
            return False

        try:
            # Handle numeric ranges
            if all(isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '', 1).isdigit())
                  for v in (actual_value, expected_value, additional_value)):
                actual = float(actual_value)
                lower = float(expected_value)
                upper = float(additional_value)
                return lower <= actual <= upper

            # Handle date ranges
            if isinstance(actual_value, datetime):
                actual_date = actual_value
            elif isinstance(actual_value, str):
                actual_date = datetime.fromisoformat(actual_value.replace('Z', '+00:00'))
            elif isinstance(actual_value, (int, float)):
                actual_date = datetime.fromtimestamp(actual_value)
            else:
                logger.warning(f"Unsupported format for BETWEEN operator: {actual_value}")
                return False

            if isinstance(expected_value, datetime):
                lower_date = expected_value
            elif isinstance(expected_value, str):
                lower_date = datetime.fromisoformat(expected_value.replace('Z', '+00:00'))
            elif isinstance(expected_value, (int, float)):
                lower_date = datetime.fromtimestamp(expected_value)
            else:
                logger.warning(f"Unsupported format for BETWEEN lower bound: {expected_value}")
                return False

            if isinstance(additional_value, datetime):
                upper_date = additional_value
            elif isinstance(additional_value, str):
                upper_date = datetime.fromisoformat(additional_value.replace('Z', '+00:00'))
            elif isinstance(additional_value, (int, float)):
                upper_date = datetime.fromtimestamp(additional_value)
            else:
                logger.warning(f"Unsupported format for BETWEEN upper bound: {additional_value}")
                return False

            return lower_date <= actual_date <= upper_date

        except (ValueError, TypeError):
            logger.warning(f"Failed to evaluate BETWEEN operator with {actual_value}, {expected_value}, {additional_value}")
            return False

    # Array operators
    elif operator == OperatorType.CONTAINS_ALL:
        # Check if actual_value contains all elements in expected_value
        if not isinstance(expected_value, (list, tuple, set)):
            logger.warning(f"Expected value for CONTAINS_ALL should be a collection, got {type(expected_value)}")
            return False

        if not isinstance(actual_value, (list, tuple, set)):
            if isinstance(actual_value, str):
                # Handle special case for strings
                return all(item in actual_value for item in expected_value)
            logger.warning(f"Actual value for CONTAINS_ALL should be a collection, got {type(actual_value)}")
            return False

        return all(item in actual_value for item in expected_value)

    elif operator == OperatorType.CONTAINS_ANY:
        # Check if actual_value contains any elements in expected_value
        if not isinstance(expected_value, (list, tuple, set)):
            logger.warning(f"Expected value for CONTAINS_ANY should be a collection, got {type(expected_value)}")
            return False

        if not isinstance(actual_value, (list, tuple, set)):
            if isinstance(actual_value, str):
                # Handle special case for strings
                return any(item in actual_value for item in expected_value)
            logger.warning(f"Actual value for CONTAINS_ANY should be a collection, got {type(actual_value)}")
            return False

        return any(item in actual_value for item in expected_value)

    # Semantic version operators
    elif operator == OperatorType.SEMANTIC_VERSION:
        try:
            # Parse the versions
            if not isinstance(actual_value, str) or not isinstance(expected_value, str):
                logger.warning(f"Semantic version requires string values, got {type(actual_value)} and {type(expected_value)}")
                return False

            # Remove leading 'v' if present (be lenient)
            actual_clean = actual_value.lstrip('v')
            expected_clean = expected_value.lstrip('v')

            # Validate format
            try:
                actual_ver = semver.Version.parse(actual_clean)
                expected_ver = semver.Version.parse(expected_clean)
            except ValueError as e:
                logger.warning(f"Invalid semantic version format: {e}")
                return False

            # Determine comparison type from additional_value
            comparison_type = additional_value if additional_value else "eq"

            # According to SemVer 2.0 spec, build metadata should be ignored when determining version precedence
            # We compare major, minor, patch, and prerelease, but not build
            if comparison_type == "eq":
                # For equality, we ignore build metadata per SemVer spec
                return (actual_ver.major == expected_ver.major and
                        actual_ver.minor == expected_ver.minor and
                        actual_ver.patch == expected_ver.patch and
                        actual_ver.prerelease == expected_ver.prerelease)
            elif comparison_type == "gt":
                return actual_ver > expected_ver
            elif comparison_type == "gte":
                return actual_ver >= expected_ver
            elif comparison_type == "lt":
                return actual_ver < expected_ver
            elif comparison_type == "lte":
                return actual_ver <= expected_ver
            else:
                logger.warning(f"Unknown semantic version comparison type: {comparison_type}")
                return False

        except Exception as e:
            logger.warning(f"Error comparing semantic versions: {e}")
            return False

    # Array length operator
    elif operator == OperatorType.ARRAY_LENGTH:
        try:
            # Get the actual length of the collection
            try:
                actual_length = len(actual_value)
            except TypeError:
                # Value doesn't have length (e.g., int, float, None)
                logger.debug(f"Value {actual_value} does not have length")
                return False

            # Determine comparison type from additional_value
            comparison_type = additional_value if additional_value else "eq"

            # Handle different comparison types
            if comparison_type == "eq":
                try:
                    return actual_length == int(expected_value)
                except (ValueError, TypeError):
                    logger.warning(f"Expected value for array length must be numeric, got {expected_value}")
                    return False

            elif comparison_type == "gt":
                try:
                    return actual_length > int(expected_value)
                except (ValueError, TypeError):
                    logger.warning(f"Expected value for array length must be numeric, got {expected_value}")
                    return False

            elif comparison_type == "lt":
                try:
                    return actual_length < int(expected_value)
                except (ValueError, TypeError):
                    logger.warning(f"Expected value for array length must be numeric, got {expected_value}")
                    return False

            elif comparison_type == "gte":
                try:
                    return actual_length >= int(expected_value)
                except (ValueError, TypeError):
                    logger.warning(f"Expected value for array length must be numeric, got {expected_value}")
                    return False

            elif comparison_type == "lte":
                try:
                    return actual_length <= int(expected_value)
                except (ValueError, TypeError):
                    logger.warning(f"Expected value for array length must be numeric, got {expected_value}")
                    return False

            elif comparison_type == "between":
                # Expected value should be a dict with min and max
                if not isinstance(expected_value, dict):
                    logger.warning(f"BETWEEN operator for array length requires dict with 'min' and 'max', got {type(expected_value)}")
                    return False

                if "min" not in expected_value or "max" not in expected_value:
                    logger.warning(f"BETWEEN operator for array length requires 'min' and 'max' keys")
                    return False

                try:
                    min_val = int(expected_value["min"])
                    max_val = int(expected_value["max"])
                    return min_val <= actual_length <= max_val
                except (ValueError, TypeError, KeyError) as e:
                    logger.warning(f"Invalid min/max values for BETWEEN operator: {e}")
                    return False

            else:
                logger.warning(f"Unknown array length comparison type: {comparison_type}")
                return False

        except Exception as e:
            logger.warning(f"Error evaluating array length operator: {e}")
            return False

    # Geographic distance operator
    elif operator == OperatorType.GEO_DISTANCE:
        try:
            # Extract coordinates from actual_value
            actual_coords = _extract_coordinates(actual_value)
            if not actual_coords:
                logger.debug(f"Failed to extract coordinates from actual value: {actual_value}")
                return False

            # Extract coordinates from expected_value
            expected_coords = _extract_coordinates(expected_value)
            if not expected_coords:
                logger.debug(f"Failed to extract coordinates from expected value: {expected_value}")
                return False

            # Validate coordinates
            if not _validate_coordinates(actual_coords):
                logger.warning(f"Invalid actual coordinates: {actual_coords}")
                return False

            if not _validate_coordinates(expected_coords):
                logger.warning(f"Invalid expected coordinates: {expected_coords}")
                return False

            # Extract radius from expected_value
            if not isinstance(expected_value, dict) or "radius" not in expected_value:
                logger.warning("GEO_DISTANCE operator requires 'radius' in expected_value")
                return False

            try:
                radius = float(expected_value["radius"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid radius value: {expected_value.get('radius')}")
                return False

            # Validate radius (must be non-negative)
            if radius < 0:
                logger.warning(f"Radius must be non-negative, got: {radius}")
                return False

            # Get unit (default to km)
            unit = expected_value.get("unit", "km")
            if isinstance(unit, str):
                unit = unit.lower()

            # Calculate distance using Haversine formula
            distance = _haversine_distance(
                actual_coords["lat"],
                actual_coords["lon"],
                expected_coords["lat"],
                expected_coords["lon"],
                unit
            )

            if distance is None:
                logger.warning("Failed to calculate distance")
                return False

            # Get comparison type (default to within radius, i.e., <=)
            comparison = expected_value.get("comparison", "lte")

            # Perform comparison
            if comparison == "lte" or comparison is None:
                return distance <= radius
            elif comparison == "lt":
                return distance < radius
            elif comparison == "gt":
                return distance > radius
            elif comparison == "gte":
                return distance >= radius
            elif comparison == "eq":
                # For equality, we use a small epsilon for floating point comparison
                epsilon = 0.01  # 10 meters tolerance
                return abs(distance - radius) < epsilon
            else:
                logger.warning(f"Unknown comparison type for GEO_DISTANCE: {comparison}")
                return False

        except Exception as e:
            logger.warning(f"Error evaluating GEO_DISTANCE operator: {e}")
            return False

    # Time window operator
    elif operator == OperatorType.TIME_WINDOW:
        try:
            # Parse actual_value to datetime
            dt = _parse_datetime(actual_value)

            # Validate expected_value is a dict
            if not isinstance(expected_value, dict):
                logger.warning(f"TIME_WINDOW operator requires dict configuration, got {type(expected_value)}")
                return False

            # Empty config matches everything
            if not expected_value:
                return True

            # Apply timezone conversion if specified
            timezone_str = expected_value.get("timezone")
            if timezone_str and HAS_PYTZ:
                try:
                    tz = pytz.timezone(timezone_str)

                    # If dt is None (no value provided), use current time in the specified timezone
                    if dt is None:
                        dt = datetime.now(tz)
                    elif dt.tzinfo is None:
                        # For naive datetime with timezone specified, localize it to the specified timezone
                        # (treat it as being in that timezone, not UTC)
                        dt = tz.localize(dt)
                    else:
                        # Timezone-aware datetime, convert to specified timezone
                        dt = dt.astimezone(tz)
                except Exception as e:
                    logger.warning(f"Invalid timezone or conversion error: {e}")
                    return False
            elif timezone_str and not HAS_PYTZ:
                logger.warning("Timezone specified but pytz not available")
                return False
            else:
                # No timezone specified
                if dt is None:
                    # Use current time if no value provided
                    dt = datetime.now()

            # Safety check: ensure dt is not None
            if dt is None:
                logger.warning("Failed to parse datetime value")
                return False

            # Check day of week if specified
            if "days" in expected_value:
                days = expected_value["days"]
                if not isinstance(days, list):
                    logger.warning(f"Days must be a list, got {type(days)}")
                    return False

                # Validate day numbers (0-6)
                if not all(isinstance(d, int) and 0 <= d <= 6 for d in days):
                    logger.warning(f"Invalid day numbers in {days}")
                    return False

                # Check if current day matches
                current_day = dt.weekday()  # Monday = 0, Sunday = 6
                if current_day not in days:
                    return False

            # Check time range if specified
            if "start_time" in expected_value or "end_time" in expected_value:
                if "start_time" not in expected_value or "end_time" not in expected_value:
                    logger.warning("Both start_time and end_time must be specified together")
                    return False

                start_time = _parse_time(expected_value["start_time"])
                end_time = _parse_time(expected_value["end_time"])

                if start_time is None or end_time is None:
                    logger.warning("Failed to parse start_time or end_time")
                    return False

                current_time = dt.time()

                # Helper function for inclusive time comparison
                # Treats times within the same minute as equal for end boundary
                def time_matches_or_before_end(current: datetime_time, end: datetime_time) -> bool:
                    # If hours and minutes match, consider it within range regardless of seconds
                    if current.hour == end.hour and current.minute == end.minute:
                        return True
                    return current <= end

                # Handle overnight time range (e.g., 22:00 to 02:00)
                if start_time > end_time:
                    # Overnight: match if time >= start OR time <= end (with minute-level inclusivity)
                    if not (current_time >= start_time or time_matches_or_before_end(current_time, end_time)):
                        return False
                else:
                    # Normal range: match if start <= time <= end (with minute-level inclusivity)
                    if not (current_time >= start_time and time_matches_or_before_end(current_time, end_time)):
                        return False

            # Check date range if specified
            if "start_date" in expected_value or "end_date" in expected_value:
                if "start_date" not in expected_value or "end_date" not in expected_value:
                    logger.warning("Both start_date and end_date must be specified together")
                    return False

                start_date = _parse_date(expected_value["start_date"])
                end_date = _parse_date(expected_value["end_date"])

                if start_date is None or end_date is None:
                    logger.warning("Failed to parse start_date or end_date")
                    return False

                # Validate date range (start must be before or equal to end)
                if start_date > end_date:
                    logger.warning(f"Invalid date range: start_date {start_date} after end_date {end_date}")
                    return False

                # Check if current date is in range (date only, ignore time)
                current_date = dt.date()
                if not (start_date <= current_date <= end_date):
                    return False

            # All checks passed
            return True

        except Exception as e:
            logger.warning(f"Error evaluating TIME_WINDOW operator: {e}")
            return False

    # Enhanced operators - delegate to evaluation service if available
    elif operator in ['percentage_bucket', 'json_path']:
        # For backward compatibility, these will be handled by the evaluation service
        # Fall back to False for now if not handled by evaluation service
        logger.warning(f"Enhanced operator {operator} requires RulesEvaluationService")
        return False

    # Unknown operator
    logger.warning(f"Unknown operator: {operator}")
    return False


def _parse_datetime(value: Any) -> Optional[datetime]:
    """
    Parse value into a datetime object.

    Supports:
    - datetime objects (returned as-is)
    - ISO format strings
    - Unix timestamps (int or float)
    - None (returns None, caller can use datetime.now())

    Args:
        value: The value to parse

    Returns:
        datetime object or None if parsing fails
    """
    try:
        # Already a datetime
        if isinstance(value, datetime):
            return value

        # None value (caller should use current time)
        if value is None:
            return None

        # ISO format string
        if isinstance(value, str):
            try:
                # Try parsing ISO format
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                logger.debug(f"Failed to parse datetime string: {value}")
                return None

        # Unix timestamp (seconds since epoch)
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value)
            except (ValueError, OSError):
                logger.debug(f"Failed to parse timestamp: {value}")
                return None

        return None

    except Exception as e:
        logger.debug(f"Error parsing datetime: {e}")
        return None


def _parse_time(value: str) -> Optional[datetime_time]:
    """
    Parse time string in HH:MM format.

    Args:
        value: Time string (e.g., "09:00", "17:30")

    Returns:
        time object or None if parsing fails
    """
    try:
        if not isinstance(value, str):
            return None

        # Expected format: "HH:MM" or "HH:MM:SS"
        parts = value.split(":")
        if len(parts) == 2:
            hour, minute = int(parts[0]), int(parts[1])
            return datetime_time(hour, minute)
        elif len(parts) == 3:
            hour, minute, second = int(parts[0]), int(parts[1]), int(parts[2])
            return datetime_time(hour, minute, second)
        else:
            return None

    except (ValueError, AttributeError):
        return None


def _parse_date(value: str):
    """
    Parse date string in YYYY-MM-DD format.

    Args:
        value: Date string (e.g., "2024-01-01")

    Returns:
        date object or None if parsing fails
    """
    try:
        if not isinstance(value, str):
            return None

        # Expected format: "YYYY-MM-DD"
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.date()

    except ValueError:
        return None


def _extract_coordinates(value: Any) -> Optional[Dict[str, float]]:
    """
    Extract latitude and longitude from various coordinate formats.

    Supports:
    - {"lat": 37.7749, "lon": -122.4194}
    - {"latitude": 37.7749, "longitude": -122.4194}
    - [37.7749, -122.4194]  (array format: [lat, lon])

    Args:
        value: The value to extract coordinates from

    Returns:
        Dictionary with 'lat' and 'lon' keys, or None if extraction fails
    """
    try:
        # Handle dict format
        if isinstance(value, dict):
            # Try lat/lon keys first
            if "lat" in value and "lon" in value:
                return {
                    "lat": float(value["lat"]),
                    "lon": float(value["lon"])
                }
            # Try latitude/longitude keys
            elif "latitude" in value and "longitude" in value:
                return {
                    "lat": float(value["latitude"]),
                    "lon": float(value["longitude"])
                }
            # Try mixed formats
            elif "lat" in value and "longitude" in value:
                return {
                    "lat": float(value["lat"]),
                    "lon": float(value["longitude"])
                }
            elif "latitude" in value and "lon" in value:
                return {
                    "lat": float(value["latitude"]),
                    "lon": float(value["lon"])
                }

        # Handle array format [lat, lon]
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            return {
                "lat": float(value[0]),
                "lon": float(value[1])
            }

        return None

    except (ValueError, TypeError, KeyError):
        return None


def _validate_coordinates(coords: Dict[str, float]) -> bool:
    """
    Validate that coordinates are within valid ranges.

    Args:
        coords: Dictionary with 'lat' and 'lon' keys

    Returns:
        True if coordinates are valid, False otherwise
    """
    try:
        lat = coords["lat"]
        lon = coords["lon"]

        # Latitude must be between -90 and 90
        if lat < -90 or lat > 90:
            return False

        # Longitude must be between -180 and 180
        if lon < -180 or lon > 180:
            return False

        return True

    except (KeyError, TypeError):
        return False


def _haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    unit: str = "km"
) -> Optional[float]:
    """
    Calculate the great circle distance between two points on Earth using the Haversine formula.

    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees
        unit: Unit for distance ('km', 'miles', 'meters')

    Returns:
        Distance in the specified unit, or None if calculation fails
    """
    try:
        # Earth's radius in kilometers
        earth_radius_km = 6371.0

        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        # Distance in kilometers
        distance_km = earth_radius_km * c

        # Convert to requested unit
        if unit in ("km", "kilometers", "kilometre", "kilometres"):
            return distance_km
        elif unit in ("miles", "mi"):
            return distance_km * 0.621371  # km to miles
        elif unit in ("meters", "metres", "m"):
            return distance_km * 1000  # km to meters
        else:
            logger.warning(f"Unknown distance unit: {unit}")
            return None

    except (ValueError, TypeError) as e:
        logger.warning(f"Error calculating Haversine distance: {e}")
        return None


def should_include_in_rollout(rule: TargetingRule, user_context: UserContext) -> bool:
    """
    Determine if a user should be included in a rollout based on percentage and deterministic hashing.

    Args:
        rule: The targeting rule with rollout percentage
        user_context: Dictionary containing user attributes

    Returns:
        True if the user should be included in the rollout, False otherwise
    """
    rollout_percentage = rule.rollout_percentage

    # If rollout is 0%, no one gets the feature
    if rollout_percentage == 0:
        return False

    # If rollout is 100%, everyone gets the feature
    if rollout_percentage == 100:
        return True

    # Get a unique, stable identifier for the user
    user_id = get_stable_user_id(user_context)

    # Create a hash of the user ID and rule ID for deterministic bucketing
    hash_input = f"{user_id}:{rule.id}"
    hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

    # Calculate the bucket (0-99)
    bucket = hash_value % 100

    # User is included if their bucket is less than the rollout percentage
    return bucket < rollout_percentage


def get_stable_user_id(user_context: UserContext) -> str:
    """
    Get a stable identifier for the user from the context.

    Args:
        user_context: Dictionary containing user attributes

    Returns:
        A string identifier for the user
    """
    # Try common user identifier fields
    for field in ['user_id', 'id', 'email', 'username', 'device_id', 'client_id', 'session_id']:
        if field in user_context and user_context[field]:
            return str(user_context[field])

    # If no suitable ID is found, use a hash of all available data
    # This isn't ideal for stable bucketing but better than nothing
    context_str = str(sorted(user_context.items()))
    return hashlib.md5(context_str.encode()).hexdigest()
