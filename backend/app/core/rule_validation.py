"""
Rule validation framework for targeting rules.

This module provides comprehensive validation for targeting rules including:
- Schema validation
- Performance impact analysis
- Logical consistency checks
- Best practice recommendations
"""

import logging
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from backend.app.schemas.targeting_rule import (
    TargetingRule,
    TargetingRules,
    Condition,
    RuleGroup,
    OperatorType,
    AttributeType,
    LogicalOperator,
)

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A validation issue found in rules."""
    severity: ValidationSeverity
    message: str
    rule_id: Optional[str] = None
    condition_path: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of rule validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    complexity_score: int
    performance_warnings: List[str]


class RuleValidator:
    """Comprehensive rule validation framework."""

    def __init__(self):
        """Initialize the validator."""
        self.max_complexity_score = 100
        self.max_rule_depth = 10
        self.max_conditions_per_group = 20

    def validate_targeting_rules(self, targeting_rules: TargetingRules) -> ValidationResult:
        """
        Validate complete targeting rules configuration.

        Args:
            targeting_rules: The targeting rules to validate

        Returns:
            ValidationResult with validation status and issues
        """
        issues = []
        complexity_score = 0
        performance_warnings = []

        try:
            # Validate schema structure
            schema_issues = self._validate_schema_structure(targeting_rules)
            issues.extend(schema_issues)

            # Validate individual rules
            for rule in targeting_rules.rules:
                rule_issues, rule_complexity = self._validate_targeting_rule(rule)
                issues.extend(rule_issues)
                complexity_score += rule_complexity

            # Validate default rule if present
            if targeting_rules.default_rule:
                default_issues, default_complexity = self._validate_targeting_rule(
                    targeting_rules.default_rule
                )
                issues.extend(default_issues)
                complexity_score += default_complexity

            # Check for rule conflicts and overlaps
            conflict_issues = self._check_rule_conflicts(targeting_rules)
            issues.extend(conflict_issues)

            # Performance analysis
            performance_warnings = self._analyze_performance_impact(targeting_rules, complexity_score)

            # Overall complexity check
            if complexity_score > self.max_complexity_score:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"High complexity score ({complexity_score}). Consider simplifying rules.",
                    suggestion="Break complex rules into simpler ones or reduce nesting depth."
                ))

            # Determine overall validity
            has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
            is_valid = not has_errors

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Validation failed: {str(e)}"
            ))
            is_valid = False

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            complexity_score=complexity_score,
            performance_warnings=performance_warnings
        )

    def _validate_schema_structure(self, targeting_rules: TargetingRules) -> List[ValidationIssue]:
        """Validate basic schema structure."""
        issues = []

        # Check for empty rules
        if not targeting_rules.rules and not targeting_rules.default_rule:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="No rules or default rule defined",
                suggestion="Add at least one rule or a default rule"
            ))

        # Check for duplicate rule IDs
        rule_ids = [rule.id for rule in targeting_rules.rules]
        if targeting_rules.default_rule:
            rule_ids.append(targeting_rules.default_rule.id)

        duplicate_ids = set([x for x in rule_ids if rule_ids.count(x) > 1])
        if duplicate_ids:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Duplicate rule IDs found: {', '.join(duplicate_ids)}",
                suggestion="Ensure all rule IDs are unique"
            ))

        # Check version format
        if not targeting_rules.version or not re.match(r'^\d+\.\d+$', targeting_rules.version):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Invalid or missing version format",
                suggestion="Use semantic versioning format (e.g., '1.0')"
            ))

        return issues

    def _validate_targeting_rule(self, rule: TargetingRule) -> Tuple[List[ValidationIssue], int]:
        """Validate an individual targeting rule."""
        issues = []
        complexity_score = 0

        # Validate rule metadata
        if not rule.id:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Rule ID is required",
                rule_id=rule.id
            ))

        if len(rule.id) > 100:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Rule ID is very long (>100 characters)",
                rule_id=rule.id,
                suggestion="Use shorter, descriptive rule IDs"
            ))

        # Validate rollout percentage
        if not (0 <= rule.rollout_percentage <= 100):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Invalid rollout percentage: {rule.rollout_percentage}",
                rule_id=rule.id,
                suggestion="Rollout percentage must be between 0 and 100"
            ))

        # Validate priority
        if rule.priority < 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"Negative priority value: {rule.priority}",
                rule_id=rule.id,
                suggestion="Use non-negative priority values"
            ))

        # Validate rule group
        group_issues, group_complexity = self._validate_rule_group(rule.rule, rule.id)
        issues.extend(group_issues)
        complexity_score += group_complexity

        return issues, complexity_score

    def _validate_rule_group(
        self, rule_group: RuleGroup, rule_id: str, path: str = "", depth: int = 0
    ) -> Tuple[List[ValidationIssue], int]:
        """Validate a rule group recursively."""
        issues = []
        complexity_score = 1  # Base complexity for the group

        # Check maximum depth
        if depth > self.max_rule_depth:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Rule nesting too deep (>{self.max_rule_depth})",
                rule_id=rule_id,
                condition_path=path,
                suggestion="Reduce nesting depth or split into multiple rules"
            ))

        # Check conditions count
        if len(rule_group.conditions) > self.max_conditions_per_group:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"Too many conditions in group ({len(rule_group.conditions)})",
                rule_id=rule_id,
                condition_path=path,
                suggestion="Consider splitting into multiple groups"
            ))

        # Validate individual conditions
        for i, condition in enumerate(rule_group.conditions):
            condition_path = f"{path}.conditions[{i}]" if path else f"conditions[{i}]"
            condition_issues = self._validate_condition(condition, rule_id, condition_path)
            issues.extend(condition_issues)
            complexity_score += 1

        # Validate nested groups
        if rule_group.groups:
            for i, nested_group in enumerate(rule_group.groups):
                nested_path = f"{path}.groups[{i}]" if path else f"groups[{i}]"
                nested_issues, nested_complexity = self._validate_rule_group(
                    nested_group, rule_id, nested_path, depth + 1
                )
                issues.extend(nested_issues)
                complexity_score += nested_complexity

        # Check for empty groups
        if not rule_group.conditions and not rule_group.groups:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="Empty rule group",
                rule_id=rule_id,
                condition_path=path,
                suggestion="Add conditions or remove empty group"
            ))

        # Validate logical operator usage
        if rule_group.operator == LogicalOperator.NOT and len(rule_group.conditions) + len(rule_group.groups or []) > 1:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message="NOT operator with multiple conditions/groups may be confusing",
                rule_id=rule_id,
                condition_path=path,
                suggestion="Consider using De Morgan's laws to simplify"
            ))

        return issues, complexity_score

    def _validate_condition(self, condition: Condition, rule_id: str, path: str) -> List[ValidationIssue]:
        """Validate an individual condition."""
        issues = []

        # Validate attribute name
        if not condition.attribute:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message="Condition attribute is required",
                rule_id=rule_id,
                condition_path=path
            ))
        elif not re.match(r'^[a-zA-Z][a-zA-Z0-9_\.]*$', condition.attribute):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                message=f"Attribute name '{condition.attribute}' doesn't follow conventions",
                rule_id=rule_id,
                condition_path=path,
                suggestion="Use alphanumeric characters, underscores, and dots only"
            ))

        # Validate operator and value compatibility
        operator_issues = self._validate_operator_compatibility(condition, rule_id, path)
        issues.extend(operator_issues)

        # Performance warnings for expensive operations
        performance_issues = self._check_condition_performance(condition, rule_id, path)
        issues.extend(performance_issues)

        return issues

    def _validate_operator_compatibility(
        self, condition: Condition, rule_id: str, path: str
    ) -> List[ValidationIssue]:
        """Validate operator and value compatibility."""
        issues = []
        operator = condition.operator
        value = condition.value
        additional_value = condition.additional_value

        try:
            # Collection operators
            if operator in [OperatorType.IN, OperatorType.NOT_IN, OperatorType.CONTAINS_ALL, OperatorType.CONTAINS_ANY]:
                if not isinstance(value, (list, tuple)):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Operator {operator} requires array value",
                        rule_id=rule_id,
                        condition_path=path
                    ))
                elif len(value) == 0:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Empty array for operator {operator}",
                        rule_id=rule_id,
                        condition_path=path
                    ))

            # Operators requiring additional_value
            if operator in [OperatorType.BETWEEN, OperatorType.GEO_DISTANCE] and additional_value is None:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Operator {operator} requires additional_value",
                    rule_id=rule_id,
                    condition_path=path
                ))

            # Regex validation
            if operator == OperatorType.MATCH_REGEX:
                try:
                    re.compile(value)
                except re.error as e:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid regex pattern: {e}",
                        rule_id=rule_id,
                        condition_path=path
                    ))

            # Semantic version validation
            if operator == OperatorType.SEMANTIC_VERSION:
                semver_pattern = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
                if not isinstance(value, str) or not re.match(semver_pattern, value):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message="Invalid semantic version format",
                        rule_id=rule_id,
                        condition_path=path,
                        suggestion="Use format like '1.2.3'"
                    ))

            # Geographic coordinates validation
            if operator == OperatorType.GEO_DISTANCE:
                if not isinstance(value, (list, tuple)) or len(value) != 2:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message="GEO_DISTANCE requires [latitude, longitude] array",
                        rule_id=rule_id,
                        condition_path=path
                    ))
                else:
                    try:
                        lat, lon = float(value[0]), float(value[1])
                        if not (-90 <= lat <= 90):
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                message=f"Invalid latitude: {lat} (must be -90 to 90)",
                                rule_id=rule_id,
                                condition_path=path
                            ))
                        if not (-180 <= lon <= 180):
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                message=f"Invalid longitude: {lon} (must be -180 to 180)",
                                rule_id=rule_id,
                                condition_path=path
                            ))
                    except (ValueError, TypeError):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message="Coordinates must be numeric",
                            rule_id=rule_id,
                            condition_path=path
                        ))

        except Exception as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                message=f"Validation error: {str(e)}",
                rule_id=rule_id,
                condition_path=path
            ))

        return issues

    def _check_condition_performance(
        self, condition: Condition, rule_id: str, path: str
    ) -> List[ValidationIssue]:
        """Check for potential performance issues in conditions."""
        issues = []
        operator = condition.operator
        value = condition.value

        # Expensive operators
        if operator == OperatorType.MATCH_REGEX:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="Regex operations can be expensive",
                rule_id=rule_id,
                condition_path=path,
                suggestion="Consider simpler string operations if possible"
            ))

        # Large arrays
        if operator in [OperatorType.IN, OperatorType.NOT_IN] and isinstance(value, (list, tuple)):
            if len(value) > 100:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Large array ({len(value)} items) may impact performance",
                    rule_id=rule_id,
                    condition_path=path,
                    suggestion="Consider using ranges or other operators"
                ))

        # JSON path operations
        if operator == OperatorType.JSON_PATH:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="JSON path evaluation can be expensive for complex documents",
                rule_id=rule_id,
                condition_path=path
            ))

        return issues

    def _check_rule_conflicts(self, targeting_rules: TargetingRules) -> List[ValidationIssue]:
        """Check for conflicts and overlaps between rules."""
        issues = []

        # Check for unreachable rules
        rule_priorities = [(rule.priority, rule.id) for rule in targeting_rules.rules]
        rule_priorities.sort()

        # Look for rules with same priority
        priority_groups = {}
        for priority, rule_id in rule_priorities:
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(rule_id)

        for priority, rule_ids in priority_groups.items():
            if len(rule_ids) > 1:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Multiple rules with same priority {priority}: {', '.join(rule_ids)}",
                    suggestion="Use unique priorities to ensure deterministic rule evaluation"
                ))

        # Check for unreachable default rule
        if targeting_rules.default_rule and targeting_rules.rules:
            # If any rule has 100% rollout and catches all users, default rule is unreachable
            for rule in targeting_rules.rules:
                if rule.rollout_percentage == 100 and self._rule_catches_all_users(rule):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Rule '{rule.id}' with 100% rollout may make default rule unreachable",
                        rule_id=rule.id,
                        suggestion="Review rule conditions and rollout percentages"
                    ))

        return issues

    def _rule_catches_all_users(self, rule: TargetingRule) -> bool:
        """Check if a rule potentially matches all users."""
        # Simple heuristic: check if rule has no conditions or only trivial conditions
        return self._group_catches_all_users(rule.rule)

    def _group_catches_all_users(self, group: RuleGroup) -> bool:
        """Check if a rule group potentially matches all users."""
        # If no conditions and no nested groups, it matches all
        if not group.conditions and not group.groups:
            return True

        # If only trivial conditions (like registered_user = true), it might match all
        if (len(group.conditions) == 1 and not group.groups and
            group.conditions[0].attribute in ['registered_user', 'active_user'] and
            group.conditions[0].value is True):
            return True

        return False

    def _analyze_performance_impact(
        self, targeting_rules: TargetingRules, complexity_score: int
    ) -> List[str]:
        """Analyze potential performance impact of rules."""
        warnings = []

        # High complexity warning
        if complexity_score > 50:
            warnings.append(f"High complexity score ({complexity_score}) may impact evaluation performance")

        # Too many rules
        if len(targeting_rules.rules) > 20:
            warnings.append(f"Large number of rules ({len(targeting_rules.rules)}) may slow evaluation")

        # Deep nesting detection
        max_depth = self._calculate_max_depth(targeting_rules)
        if max_depth > 5:
            warnings.append(f"Deep rule nesting (depth {max_depth}) may impact performance")

        return warnings

    def _calculate_max_depth(self, targeting_rules: TargetingRules) -> int:
        """Calculate maximum nesting depth in rules."""
        max_depth = 0

        def calculate_group_depth(group: RuleGroup, current_depth: int = 0) -> int:
            depth = current_depth
            if group.groups:
                for nested_group in group.groups:
                    nested_depth = calculate_group_depth(nested_group, current_depth + 1)
                    depth = max(depth, nested_depth)
            return depth

        for rule in targeting_rules.rules:
            rule_depth = calculate_group_depth(rule.rule)
            max_depth = max(max_depth, rule_depth)

        if targeting_rules.default_rule:
            default_depth = calculate_group_depth(targeting_rules.default_rule.rule)
            max_depth = max(max_depth, default_depth)

        return max_depth