"""
Rules engine for evaluating targeting rules.

This module provides functions for evaluating targeting rules against user contexts.
"""

import re
import logging
import hashlib
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime

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
        # Only equals/not equals operators make sense with None
        if operator == OperatorType.EQUALS:
            return expected_value is None
        elif operator == OperatorType.NOT_EQUALS:
            return expected_value is not None
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

    # Time elapsed operators
    elif operator in (OperatorType.DAYS_SINCE, OperatorType.MONTHS_SINCE):
        try:
            # Convert reference date (expected_value)
            if isinstance(expected_value, str):
                reference_date = datetime.fromisoformat(expected_value.replace('Z', '+00:00'))
            elif isinstance(expected_value, (int, float)):
                reference_date = datetime.fromtimestamp(expected_value)
            elif isinstance(expected_value, datetime):
                reference_date = expected_value
            else:
                logger.warning(f"Unsupported reference date format: {expected_value}")
                return False

            # Get current date or use provided date
            if actual_value == "now":
                current_date = datetime.now()
            elif isinstance(actual_value, str):
                current_date = datetime.fromisoformat(actual_value.replace('Z', '+00:00'))
            elif isinstance(actual_value, (int, float)):
                current_date = datetime.fromtimestamp(actual_value)
            elif isinstance(actual_value, datetime):
                current_date = actual_value
            else:
                logger.warning(f"Unsupported current date format: {actual_value}")
                return False

            # Calculate difference
            delta = current_date - reference_date

            if operator == OperatorType.DAYS_SINCE:
                days_elapsed = delta.days
                # additional_value can be a comparison like ">30" or "<=7"
                if additional_value and isinstance(additional_value, str):
                    if additional_value.startswith(">"):
                        threshold = int(additional_value[1:])
                        return days_elapsed > threshold
                    elif additional_value.startswith(">="):
                        threshold = int(additional_value[2:])
                        return days_elapsed >= threshold
                    elif additional_value.startswith("<"):
                        threshold = int(additional_value[1:])
                        return days_elapsed < threshold
                    elif additional_value.startswith("<="):
                        threshold = int(additional_value[2:])
                        return days_elapsed <= threshold
                    elif additional_value.startswith("=="):
                        threshold = int(additional_value[2:])
                        return days_elapsed == threshold
                    else:
                        # Default to equality if no operator specified
                        threshold = int(additional_value)
                        return days_elapsed == threshold
                return True  # If no additional value, just check if calculation works

            elif operator == OperatorType.MONTHS_SINCE:
                # Calculate months difference
                months_elapsed = (current_date.year - reference_date.year) * 12 + (current_date.month - reference_date.month)

                # Apply comparison if provided
                if additional_value and isinstance(additional_value, str):
                    try:
                        # Handle comparison operators
                        if additional_value.startswith(">="):
                            threshold = int(additional_value[2:])
                            return months_elapsed >= threshold
                        elif additional_value.startswith(">"):
                            threshold = int(additional_value[1:])
                            return months_elapsed > threshold
                        elif additional_value.startswith("<="):
                            threshold = int(additional_value[2:])
                            return months_elapsed <= threshold
                        elif additional_value.startswith("<"):
                            threshold = int(additional_value[1:])
                            return months_elapsed < threshold
                        elif additional_value.startswith("=="):
                            threshold = int(additional_value[2:])
                            return months_elapsed == threshold
                        else:
                            # Default to equality if no operator specified
                            threshold = int(additional_value)
                            return months_elapsed == threshold
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse MONTHS_SINCE comparison: {e}")
                        return False

                # If no additional value, just check if calculation succeeded
                return True

        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to evaluate time elapsed: {e}")
            return False

    # Unknown operator
    logger.warning(f"Unknown operator: {operator}")
    return False


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
