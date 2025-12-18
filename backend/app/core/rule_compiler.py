"""
Rule compiler for targeting rules.

This module provides compilation and validation of targeting rules, including:
- Syntax validation
- Operator-value compatibility checking
- Redundancy and contradiction detection
- Metadata extraction
- Compilation result caching
"""

import hashlib
import json
import logging
from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import OrderedDict

from backend.app.schemas.targeting_rule import (
    TargetingRule,
    RuleGroup,
    Condition,
    OperatorType,
    LogicalOperator
)

logger = logging.getLogger(__name__)


class RuleValidationError(Exception):
    """Raised when rule validation fails."""
    pass


@dataclass
class CompiledRule:
    """Compiled and validated targeting rule."""

    rule_id: str
    rule_hash: str
    compiled_at: datetime
    is_valid: bool
    validation_errors: List[str] = field(default_factory=list)

    # Metadata
    condition_count: int = 0
    max_depth: int = 0
    required_attributes: Set[str] = field(default_factory=set)
    operator_types: Set[OperatorType] = field(default_factory=set)

    # Optimization flags
    has_redundancy: bool = False
    has_contradiction: bool = False
    can_ever_match: bool = True

    # Original rule for reference
    original_rule: Optional[TargetingRule] = None


class RuleCompiler:
    """
    Compiles and validates targeting rules with caching.

    Provides:
    - Rule validation
    - Metadata extraction
    - Optimization hints
    - LRU caching of compiled rules
    """

    def __init__(self, max_depth: int = 50, cache_max_size: int = 1000):
        """
        Initialize rule compiler.

        Args:
            max_depth: Maximum allowed rule nesting depth
            cache_max_size: Maximum number of compiled rules to cache
        """
        self.max_depth = max_depth
        self.cache_max_size = cache_max_size

        # LRU cache for compiled rules
        self._cache: OrderedDict[str, CompiledRule] = OrderedDict()
        self._cache_hits = 0
        self._cache_misses = 0

    @property
    def cache_hits(self) -> int:
        """Get number of cache hits."""
        return self._cache_hits

    @property
    def cache_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def compile(self, rule: TargetingRule, force_recompile: bool = False) -> CompiledRule:
        """
        Compile and validate a targeting rule.

        Args:
            rule: The targeting rule to compile
            force_recompile: Force recompilation even if cached

        Returns:
            Compiled rule with validation results and metadata
        """
        # Generate hash of rule for caching
        rule_hash = self._hash_rule(rule)
        cache_key = f"{rule.id}:{rule_hash}"

        # Check cache
        if not force_recompile and cache_key in self._cache:
            self._cache_hits += 1
            # Move to end (mark as recently used)
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        self._cache_misses += 1

        # Compile rule
        compiled = self._compile_rule(rule, rule_hash)

        # Add to cache
        self._cache[cache_key] = compiled
        self._cache.move_to_end(cache_key)

        # Evict oldest if cache too large
        if len(self._cache) > self.cache_max_size:
            self._cache.popitem(last=False)

        return compiled

    def clear_cache(self):
        """Clear the compilation cache."""
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def _hash_rule(self, rule: TargetingRule) -> str:
        """
        Generate hash of rule for cache key.

        Args:
            rule: The targeting rule

        Returns:
            Hash string
        """
        # Create a deterministic representation of the rule
        rule_dict = {
            "id": rule.id,
            "rule": self._serialize_rule_group(rule.rule),
            "rollout_percentage": rule.rollout_percentage,
            "priority": rule.priority
        }

        rule_json = json.dumps(rule_dict, sort_keys=True)
        return hashlib.md5(rule_json.encode()).hexdigest()

    def _serialize_rule_group(self, group: RuleGroup) -> Dict[str, Any]:
        """Serialize rule group for hashing."""
        return {
            "operator": group.operator.value,
            "conditions": [self._serialize_condition(c) for c in group.conditions],
            "groups": [self._serialize_rule_group(g) for g in (group.groups or [])]
        }

    def _serialize_condition(self, condition: Condition) -> Dict[str, Any]:
        """Serialize condition for hashing."""
        return {
            "attribute": condition.attribute,
            "operator": condition.operator.value,
            "value": str(condition.value),  # Convert to string for consistent hashing
            "additional_value": str(condition.additional_value) if condition.additional_value else None
        }

    def _compile_rule(self, rule: TargetingRule, rule_hash: str) -> CompiledRule:
        """
        Perform actual rule compilation.

        Args:
            rule: The targeting rule
            rule_hash: Pre-computed hash

        Returns:
            Compiled rule
        """
        compiled = CompiledRule(
            rule_id=rule.id,
            rule_hash=rule_hash,
            compiled_at=datetime.now(),
            is_valid=True,  # Assume valid until proven otherwise
            original_rule=rule
        )

        # Validate and extract metadata
        try:
            self._analyze_rule_group(rule.rule, compiled, depth=1)
        except Exception as e:
            compiled.is_valid = False
            compiled.validation_errors.append(f"Compilation error: {str(e)}")
            logger.error(f"Error compiling rule {rule.id}: {e}")

        # Check for contradictions
        self._check_contradictions(rule.rule, compiled)

        return compiled

    def _analyze_rule_group(
        self,
        group: RuleGroup,
        compiled: CompiledRule,
        depth: int
    ):
        """
        Recursively analyze a rule group.

        Args:
            group: The rule group to analyze
            compiled: The compiled rule to update
            depth: Current nesting depth
        """
        # Update max depth
        compiled.max_depth = max(compiled.max_depth, depth)

        # Check depth limit
        if depth > self.max_depth:
            compiled.is_valid = False
            compiled.validation_errors.append(
                f"Rule nesting exceeds maximum depth of {self.max_depth}"
            )
            return

        # Analyze conditions
        for condition in group.conditions:
            compiled.condition_count += 1
            self._analyze_condition(condition, compiled)

        # Analyze nested groups
        for nested_group in (group.groups or []):
            self._analyze_rule_group(nested_group, compiled, depth + 1)

    def _analyze_condition(self, condition: Condition, compiled: CompiledRule):
        """
        Analyze a single condition.

        Args:
            condition: The condition to analyze
            compiled: The compiled rule to update
        """
        # Extract metadata
        compiled.required_attributes.add(condition.attribute)
        compiled.operator_types.add(condition.operator)

        # Validate operator-value compatibility
        errors = self._validate_condition(condition)
        if errors:
            compiled.is_valid = False
            compiled.validation_errors.extend(errors)

    def _validate_condition(self, condition: Condition) -> List[str]:
        """
        Validate a condition for operator-value compatibility.

        Args:
            condition: The condition to validate

        Returns:
            List of validation error messages
        """
        errors = []
        operator = condition.operator
        value = condition.value
        additional_value = condition.additional_value

        # IN and NOT_IN require list/array values
        if operator in (OperatorType.IN, OperatorType.NOT_IN):
            if not isinstance(value, (list, tuple, set)):
                errors.append(
                    f"IN/NOT_IN operator requires array value for attribute '{condition.attribute}', "
                    f"got {type(value).__name__}"
                )

        # BETWEEN requires additional_value
        elif operator == OperatorType.BETWEEN:
            if additional_value is None:
                errors.append(
                    f"BETWEEN operator requires additional_value for upper bound "
                    f"on attribute '{condition.attribute}'"
                )

        # GEO_DISTANCE - Pydantic validates format, just check additional_value
        elif operator == OperatorType.GEO_DISTANCE:
            if additional_value is None:
                errors.append(
                    f"GEO_DISTANCE operator requires additional_value (radius) for attribute '{condition.attribute}'"
                )

        # TIME_WINDOW requires dict
        elif operator == OperatorType.TIME_WINDOW:
            if not isinstance(value, dict):
                errors.append(
                    f"TIME_WINDOW operator requires dict value for attribute '{condition.attribute}'"
                )

        # SEMANTIC_VERSION requires string values
        elif operator == OperatorType.SEMANTIC_VERSION:
            if not isinstance(value, str):
                errors.append(
                    f"SEMANTIC_VERSION operator requires string value for attribute '{condition.attribute}'"
                )

        return errors

    def _check_contradictions(self, group: RuleGroup, compiled: CompiledRule):
        """
        Check for contradictory conditions.

        Args:
            group: The rule group to check
            compiled: The compiled rule to update
        """
        # Check for duplicate conditions (redundancy)
        condition_signatures = []
        for condition in group.conditions:
            sig = (condition.attribute, condition.operator, str(condition.value))
            if sig in condition_signatures:
                compiled.has_redundancy = True
            condition_signatures.append(sig)

        # Check for contradictions (same attribute, conflicting values with AND)
        if group.operator == LogicalOperator.AND:
            attr_values = {}
            for condition in group.conditions:
                if condition.operator == OperatorType.EQUALS:
                    attr = condition.attribute
                    if attr in attr_values:
                        # Same attribute with different values in AND = contradiction
                        if attr_values[attr] != condition.value:
                            compiled.has_contradiction = True
                            compiled.can_ever_match = False
                    else:
                        attr_values[attr] = condition.value

        # Recursively check nested groups
        for nested_group in (group.groups or []):
            self._check_contradictions(nested_group, compiled)
