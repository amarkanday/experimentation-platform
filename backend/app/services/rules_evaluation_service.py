"""
Enhanced rules evaluation service with custom attribute validation and performance monitoring.

This service provides advanced rule evaluation capabilities with:
- Custom attribute validation
- Performance metrics and monitoring
- Error tracking and logging
- Integration with assignment service
"""

import json
import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re
import math

from backend.app.schemas.targeting_rule import (
    TargetingRule,
    TargetingRules,
    Condition,
    RuleGroup,
    OperatorType,
    AttributeType,
    LogicalOperator,
)
from backend.app.core.rules_engine import (
    evaluate_targeting_rules as base_evaluate_targeting_rules,
    apply_operator as base_apply_operator,
    UserContext,
)

logger = logging.getLogger(__name__)


@dataclass
class RuleEvaluationMetrics:
    """Metrics for rule evaluation performance."""
    rule_id: str
    evaluation_time_ms: float
    matched: bool
    error: Optional[str] = None
    complexity_score: int = 0
    attribute_count: int = 0


@dataclass
class AttributeValidationResult:
    """Result of attribute validation."""
    is_valid: bool
    error_message: Optional[str] = None
    normalized_value: Optional[Any] = None


class RulesEvaluationService:
    """Enhanced rules evaluation service with validation and monitoring."""

    def __init__(self):
        """Initialize the service."""
        self.evaluation_metrics: List[RuleEvaluationMetrics] = []
        self.attribute_cache: Dict[str, Any] = {}
        self.error_counts = defaultdict(int)
        self.performance_stats = defaultdict(list)

    def evaluate_rules_with_validation(
        self,
        targeting_rules: TargetingRules,
        user_context: UserContext,
        validate_attributes: bool = True,
        track_metrics: bool = True,
    ) -> Tuple[Optional[TargetingRule], Optional[RuleEvaluationMetrics]]:
        """
        Evaluate targeting rules with enhanced validation and monitoring.

        Args:
            targeting_rules: The targeting rules to evaluate
            user_context: User context for evaluation
            validate_attributes: Whether to validate attributes
            track_metrics: Whether to track evaluation metrics

        Returns:
            Tuple of (matched_rule, evaluation_metrics)
        """
        start_time = time.time()
        matched_rule = None
        metrics = None

        try:
            # Validate user context if requested
            if validate_attributes:
                validation_result = self.validate_user_context(user_context, targeting_rules)
                if not validation_result.is_valid:
                    logger.warning(f"User context validation failed: {validation_result.error_message}")
                    if track_metrics:
                        metrics = RuleEvaluationMetrics(
                            rule_id="validation_failed",
                            evaluation_time_ms=(time.time() - start_time) * 1000,
                            matched=False,
                            error=validation_result.error_message,
                        )
                    return None, metrics

            # Evaluate rules with enhanced operators
            matched_rule = self._evaluate_targeting_rules_enhanced(targeting_rules, user_context)

            # Track metrics if requested
            if track_metrics:
                evaluation_time = (time.time() - start_time) * 1000
                complexity = self._calculate_rule_complexity(targeting_rules)

                metrics = RuleEvaluationMetrics(
                    rule_id=matched_rule.id if matched_rule else "no_match",
                    evaluation_time_ms=evaluation_time,
                    matched=matched_rule is not None,
                    complexity_score=complexity,
                    attribute_count=len(user_context),
                )

                self.evaluation_metrics.append(metrics)
                self.performance_stats['evaluation_time'].append(evaluation_time)

        except Exception as e:
            logger.error(f"Error evaluating rules: {str(e)}")
            self.error_counts['evaluation_error'] += 1

            if track_metrics:
                metrics = RuleEvaluationMetrics(
                    rule_id="error",
                    evaluation_time_ms=(time.time() - start_time) * 1000,
                    matched=False,
                    error=str(e),
                )

        return matched_rule, metrics

    def validate_user_context(
        self, user_context: UserContext, targeting_rules: TargetingRules
    ) -> AttributeValidationResult:
        """
        Validate user context against rule requirements.

        Args:
            user_context: User context to validate
            targeting_rules: Rules to extract validation requirements from

        Returns:
            AttributeValidationResult with validation status
        """
        try:
            # Extract all attributes used in rules
            required_attributes = self._extract_required_attributes(targeting_rules)

            # Validate each attribute
            for attr_name, attr_info in required_attributes.items():
                if attr_name not in user_context:
                    # Check if attribute is required
                    if attr_info.get('required', False):
                        return AttributeValidationResult(
                            is_valid=False,
                            error_message=f"Required attribute '{attr_name}' not found in user context",
                        )
                    continue

                # Validate attribute type and value
                attr_value = user_context[attr_name]
                attr_type = attr_info.get('type')

                if attr_type:
                    validation_result = self._validate_attribute_value(attr_name, attr_value, attr_type)
                    if not validation_result.is_valid:
                        return validation_result

            return AttributeValidationResult(is_valid=True)

        except Exception as e:
            return AttributeValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}",
            )

    def _validate_attribute_value(
        self, attr_name: str, attr_value: Any, attr_type: AttributeType
    ) -> AttributeValidationResult:
        """Validate an individual attribute value against its type."""
        try:
            if attr_type == AttributeType.STRING:
                if not isinstance(attr_value, str):
                    return AttributeValidationResult(
                        is_valid=False,
                        error_message=f"Attribute '{attr_name}' must be a string",
                    )

            elif attr_type == AttributeType.NUMBER:
                if not isinstance(attr_value, (int, float)):
                    try:
                        float(attr_value)
                    except (ValueError, TypeError):
                        return AttributeValidationResult(
                            is_valid=False,
                            error_message=f"Attribute '{attr_name}' must be a number",
                        )

            elif attr_type == AttributeType.BOOLEAN:
                if not isinstance(attr_value, bool):
                    return AttributeValidationResult(
                        is_valid=False,
                        error_message=f"Attribute '{attr_name}' must be a boolean",
                    )

            elif attr_type == AttributeType.ARRAY:
                if not isinstance(attr_value, (list, tuple)):
                    return AttributeValidationResult(
                        is_valid=False,
                        error_message=f"Attribute '{attr_name}' must be an array",
                    )

            elif attr_type == AttributeType.DATE:
                if isinstance(attr_value, str):
                    try:
                        datetime.fromisoformat(attr_value.replace('Z', '+00:00'))
                    except ValueError:
                        return AttributeValidationResult(
                            is_valid=False,
                            error_message=f"Attribute '{attr_name}' must be a valid ISO date string",
                        )
                elif not isinstance(attr_value, (datetime, int, float)):
                    return AttributeValidationResult(
                        is_valid=False,
                        error_message=f"Attribute '{attr_name}' must be a date, timestamp, or ISO string",
                    )

            elif attr_type == AttributeType.GEO_COORDINATE:
                if not isinstance(attr_value, (list, tuple)) or len(attr_value) != 2:
                    return AttributeValidationResult(
                        is_valid=False,
                        error_message=f"Attribute '{attr_name}' must be [latitude, longitude]",
                    )
                try:
                    lat, lon = float(attr_value[0]), float(attr_value[1])
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        return AttributeValidationResult(
                            is_valid=False,
                            error_message=f"Attribute '{attr_name}' coordinates out of valid range",
                        )
                except (ValueError, TypeError):
                    return AttributeValidationResult(
                        is_valid=False,
                        error_message=f"Attribute '{attr_name}' coordinates must be numeric",
                    )

            elif attr_type == AttributeType.SEMANTIC_VERSION:
                if not isinstance(attr_value, str):
                    return AttributeValidationResult(
                        is_valid=False,
                        error_message=f"Attribute '{attr_name}' must be a semantic version string",
                    )
                semver_pattern = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
                if not re.match(semver_pattern, attr_value):
                    return AttributeValidationResult(
                        is_valid=False,
                        error_message=f"Attribute '{attr_name}' must be a valid semantic version (e.g., 1.2.3)",
                    )

            return AttributeValidationResult(is_valid=True)

        except Exception as e:
            return AttributeValidationResult(
                is_valid=False,
                error_message=f"Validation error for attribute '{attr_name}': {str(e)}",
            )

    def _evaluate_targeting_rules_enhanced(
        self, targeting_rules: TargetingRules, user_context: UserContext
    ) -> Optional[TargetingRule]:
        """Evaluate targeting rules with enhanced operators."""
        if not targeting_rules or not targeting_rules.rules:
            return targeting_rules.default_rule

        # Sort rules by priority (lower number = higher priority)
        sorted_rules = sorted(targeting_rules.rules, key=lambda r: r.priority)

        for rule in sorted_rules:
            # Check if rule matches with enhanced evaluation
            if self._evaluate_rule_enhanced(rule, user_context):
                # Check rollout percentage (use base implementation)
                from backend.app.core.rules_engine import should_include_in_rollout
                if should_include_in_rollout(rule, user_context):
                    return rule

        return targeting_rules.default_rule

    def _evaluate_rule_enhanced(self, rule: TargetingRule, user_context: UserContext) -> bool:
        """Evaluate a rule with enhanced operators."""
        return self._evaluate_rule_group_enhanced(rule.rule, user_context)

    def _evaluate_rule_group_enhanced(self, rule_group: RuleGroup, user_context: UserContext) -> bool:
        """Evaluate a rule group with enhanced operators."""
        operator = rule_group.operator

        # Evaluate conditions with enhanced operators
        condition_results = [
            self._evaluate_condition_enhanced(condition, user_context)
            for condition in rule_group.conditions
        ]

        # Evaluate nested groups
        if rule_group.groups:
            group_results = [
                self._evaluate_rule_group_enhanced(group, user_context)
                for group in rule_group.groups
            ]
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
            if len(all_results) == 1:
                return not all_results[0]
            else:
                return not all(all_results)

        # Default fallback
        logger.warning(f"Unknown logical operator: {operator}")
        return False

    def _evaluate_condition_enhanced(self, condition: Condition, user_context: UserContext) -> bool:
        """Evaluate a condition with enhanced operators."""
        attribute = condition.attribute
        operator = condition.operator
        expected_value = condition.value
        additional_value = condition.additional_value

        # Get actual value from user context
        if attribute not in user_context:
            logger.debug(f"Attribute {attribute} not found in user context")
            return False

        actual_value = user_context[attribute]

        # Use enhanced operator application
        return self._apply_operator_enhanced(operator, actual_value, expected_value, additional_value)

    def _apply_operator_enhanced(
        self,
        operator: OperatorType,
        actual_value: Any,
        expected_value: Any,
        additional_value: Optional[Any] = None,
    ) -> bool:
        """Apply enhanced operators including new custom attribute operators."""

        # Handle new custom operators
        if operator == OperatorType.SEMANTIC_VERSION:
            return self._compare_semantic_versions(actual_value, expected_value)
        elif operator == OperatorType.GEO_DISTANCE:
            return self._evaluate_geo_distance(actual_value, expected_value, additional_value)
        elif operator == OperatorType.TIME_WINDOW:
            return self._evaluate_time_window(actual_value, expected_value)
        elif operator == OperatorType.PERCENTAGE_BUCKET:
            return self._evaluate_percentage_bucket(actual_value, expected_value)
        elif operator == OperatorType.JSON_PATH:
            return self._evaluate_json_path(actual_value, expected_value, additional_value)
        elif operator == OperatorType.ARRAY_LENGTH:
            return self._evaluate_array_length(actual_value, expected_value)

        # Fall back to base implementation for standard operators
        return base_apply_operator(operator, actual_value, expected_value, additional_value)

    def _compare_semantic_versions(self, actual_version: str, expected_version: str) -> bool:
        """Compare semantic versions."""
        try:
            def parse_version(version: str) -> Tuple[int, int, int]:
                # Simple semantic version parsing
                parts = version.split('-')[0].split('+')[0].split('.')
                return tuple(int(x) for x in parts[:3])

            actual_parts = parse_version(str(actual_version))
            expected_parts = parse_version(str(expected_version))

            return actual_parts >= expected_parts
        except (ValueError, TypeError):
            logger.warning(f"Failed to compare semantic versions: {actual_version} and {expected_version}")
            return False

    def _evaluate_geo_distance(self, actual_coords: Any, target_coords: Any, max_distance_km: Any) -> bool:
        """Evaluate if coordinates are within distance."""
        try:
            if not isinstance(actual_coords, (list, tuple)) or len(actual_coords) != 2:
                return False
            if not isinstance(target_coords, (list, tuple)) or len(target_coords) != 2:
                return False

            lat1, lon1 = float(actual_coords[0]), float(actual_coords[1])
            lat2, lon2 = float(target_coords[0]), float(target_coords[1])
            max_dist = float(max_distance_km)

            # Haversine formula for distance calculation
            R = 6371  # Earth's radius in kilometers

            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)

            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                 math.sin(dlon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = R * c

            return distance <= max_dist

        except (ValueError, TypeError):
            logger.warning(f"Failed to evaluate geo distance")
            return False

    def _evaluate_time_window(self, actual_time: Any, time_window: Any) -> bool:
        """Evaluate if time falls within window."""
        try:
            if not isinstance(time_window, dict):
                return False

            start_time = time_window.get('start')
            end_time = time_window.get('end')

            if isinstance(actual_time, str):
                actual_dt = datetime.fromisoformat(actual_time.replace('Z', '+00:00'))
            elif isinstance(actual_time, (int, float)):
                actual_dt = datetime.fromtimestamp(actual_time)
            elif isinstance(actual_time, datetime):
                actual_dt = actual_time
            else:
                return False

            # Parse time window bounds
            if isinstance(start_time, str):
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                start_dt = datetime.fromtimestamp(start_time)

            if isinstance(end_time, str):
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            else:
                end_dt = datetime.fromtimestamp(end_time)

            return start_dt <= actual_dt <= end_dt

        except (ValueError, TypeError):
            logger.warning(f"Failed to evaluate time window")
            return False

    def _evaluate_percentage_bucket(self, user_id: Any, percentage: Any) -> bool:
        """Evaluate if user falls within percentage bucket."""
        try:
            # Create deterministic hash
            hash_input = str(user_id)
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            bucket = hash_value % 100

            return bucket < float(percentage)

        except (ValueError, TypeError):
            logger.warning(f"Failed to evaluate percentage bucket")
            return False

    def _evaluate_json_path(self, json_data: Any, json_path: str, expected_value: Any) -> bool:
        """Evaluate JSONPath expression."""
        try:
            # Parse JSON string if needed
            if isinstance(json_data, str):
                try:
                    json_data = json.loads(json_data)
                except json.JSONDecodeError:
                    return False

            # Ensure we have a dict or list to work with
            if not isinstance(json_data, (dict, list)):
                return False

            # Handle simple paths like $.field or $.field.subfield
            path_parts = json_path[2:].split('.')  # Remove '$.'

            current = json_data
            for part in path_parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                elif isinstance(current, list) and part.isdigit():
                    current = current[int(part)]
                else:
                    return False

            return current == expected_value

        except (ValueError, TypeError, json.JSONDecodeError, IndexError, KeyError):
            logger.warning(f"Failed to evaluate JSON path: {json_path}")
            return False

    def _evaluate_array_length(self, array_value: Any, expected_length: Any) -> bool:
        """Evaluate array length."""
        try:
            if not isinstance(array_value, (list, tuple)):
                return False

            return len(array_value) == int(expected_length)

        except (ValueError, TypeError):
            logger.warning(f"Failed to evaluate array length")
            return False

    def _extract_required_attributes(self, targeting_rules: TargetingRules) -> Dict[str, Dict[str, Any]]:
        """Extract all attributes used in targeting rules."""
        attributes = {}

        def extract_from_group(group: RuleGroup):
            for condition in group.conditions:
                attributes[condition.attribute] = {
                    'type': condition.attribute_type,
                    'required': True,  # All attributes in conditions are considered required
                }

            if group.groups:
                for nested_group in group.groups:
                    extract_from_group(nested_group)

        for rule in targeting_rules.rules:
            extract_from_group(rule.rule)

        if targeting_rules.default_rule:
            extract_from_group(targeting_rules.default_rule.rule)

        return attributes

    def _calculate_rule_complexity(self, targeting_rules: TargetingRules) -> int:
        """Calculate complexity score for rules."""
        complexity = 0

        def calculate_group_complexity(group: RuleGroup) -> int:
            score = len(group.conditions)
            if group.groups:
                score += sum(calculate_group_complexity(g) for g in group.groups)
                score += len(group.groups)  # Add complexity for nesting
            return score

        for rule in targeting_rules.rules:
            complexity += calculate_group_complexity(rule.rule)

        if targeting_rules.default_rule:
            complexity += calculate_group_complexity(targeting_rules.default_rule.rule)

        return complexity

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.evaluation_metrics:
            return {}

        evaluation_times = [m.evaluation_time_ms for m in self.evaluation_metrics]

        return {
            'total_evaluations': len(self.evaluation_metrics),
            'avg_evaluation_time_ms': sum(evaluation_times) / len(evaluation_times),
            'min_evaluation_time_ms': min(evaluation_times),
            'max_evaluation_time_ms': max(evaluation_times),
            'error_count': sum(1 for m in self.evaluation_metrics if m.error),
            'match_rate': sum(1 for m in self.evaluation_metrics if m.matched) / len(self.evaluation_metrics),
            'avg_complexity_score': sum(m.complexity_score for m in self.evaluation_metrics) / len(self.evaluation_metrics),
            'error_breakdown': dict(self.error_counts),
        }

    def clear_metrics(self):
        """Clear collected metrics."""
        self.evaluation_metrics.clear()
        self.error_counts.clear()
        self.performance_stats.clear()
        self.attribute_cache.clear()