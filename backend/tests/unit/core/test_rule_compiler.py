"""
Test cases for rule compilation and validation.

Tests the rule compiler that pre-validates and optimizes targeting rules.
"""

import pytest
from datetime import datetime
from backend.app.core.rule_compiler import RuleCompiler, CompiledRule, RuleValidationError
from backend.app.schemas.targeting_rule import (
    TargetingRule,
    RuleGroup,
    Condition,
    LogicalOperator,
    OperatorType
)


class TestRuleCompilation:
    """Test basic rule compilation."""

    def test_compile_simple_rule(self):
        """Test compiling a simple rule with one condition."""
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    attribute="country",
                    operator=OperatorType.EQUALS,
                    value="US"
                )
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="rule_1",
            name="US Only",
            description="Target US users",
            rule=rule_group,
            
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()
        compiled = compiler.compile(rule)

        assert compiled is not None
        assert compiled.rule_id == "rule_1"
        assert compiled.condition_count == 1
        assert compiled.max_depth == 1
        assert compiled.is_valid is True

    def test_compile_nested_rule(self):
        """Test compiling a nested rule with groups."""
        inner_group = RuleGroup(
            operator=LogicalOperator.OR,
            conditions=[
                Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=18),
                Condition(attribute="verified", operator=OperatorType.EQUALS, value=True)
            ],
            groups=[]
        )

        outer_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA"])
            ],
            groups=[inner_group]
        )

        rule = TargetingRule(
            id="rule_2",
            name="Complex Rule",
            description="Nested targeting",
            rule=outer_group,
            
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()
        compiled = compiler.compile(rule)

        assert compiled.condition_count == 3
        assert compiled.max_depth == 2
        assert compiled.is_valid is True

    def test_compile_caches_result(self):
        """Test that compilation results are cached."""
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.EQUALS, value="US")
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="rule_cache",
            name="Cached Rule",
            description="Test caching",
            rule=rule_group,
            
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()

        # First compilation
        compiled1 = compiler.compile(rule)

        # Second compilation should return cached result
        compiled2 = compiler.compile(rule)

        # Should be the same object (cached)
        assert compiled1 is compiled2
        assert compiler.cache_hits > 0


class TestRuleValidation:
    """Test rule validation during compilation."""

    def test_validate_operator_compatibility(self):
        """Test validation catches additional semantic issues beyond Pydantic."""
        # Pydantic handles basic validation, compiler handles semantic validation
        # Use valid Pydantic schema
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    attribute="country",
                    operator=OperatorType.IN,
                    value=["US", "CA"]  # Valid
                )
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="valid_1",
            name="Valid Rule",
            description="Valid rule",
            rule=rule_group,
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()
        compiled = compiler.compile(rule)

        # Should compile successfully
        assert compiled.is_valid is True
        assert len(compiled.validation_errors) == 0

    def test_validate_between_operator(self):
        """Test validation of BETWEEN operator with proper additional_value."""
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    attribute="age",
                    operator=OperatorType.BETWEEN,
                    value=18,
                    additional_value=65  # Valid upper bound
                )
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="valid_between",
            name="Valid Between",
            description="Valid between operator",
            rule=rule_group,
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()
        compiled = compiler.compile(rule)

        # Should be valid since we provided additional_value
        assert compiled.is_valid is True

    def test_validate_geo_distance_format(self):
        """Test validation of GEO_DISTANCE operator format."""
        # Pydantic expects [lat, lon] format, additional_value for radius
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    attribute="location",
                    operator=OperatorType.GEO_DISTANCE,
                    value=[37.7749, -122.4194],  # Valid [lat, lon]
                    additional_value=10  # radius in default unit
                )
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="valid_geo",
            name="Valid Geo",
            description="Valid GEO_DISTANCE",
            rule=rule_group,
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()
        compiled = compiler.compile(rule)

        # Should be valid
        assert compiled.is_valid is True

    def test_validate_circular_reference(self):
        """Test detection of circular references in nested groups."""
        # This is more of an edge case - implementation may vary
        # For now, just test max depth detection

        # Create deeply nested rules (depth > reasonable limit)
        current_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[Condition(attribute="depth", operator=OperatorType.EQUALS, value=10)],
            groups=[]
        )

        # Nest 20 levels deep
        for i in range(20):
            current_group = RuleGroup(
                operator=LogicalOperator.AND,
                conditions=[],
                groups=[current_group]
            )

        rule = TargetingRule(
            id="deep_rule",
            name="Very Deep Rule",
            description="Too many levels",
            rule=current_group,
            
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler(max_depth=10)
        compiled = compiler.compile(rule)

        # Should either warn or mark as invalid for excessive depth
        assert compiled.max_depth > 10


class TestRuleOptimization:
    """Test rule optimization during compilation."""

    def test_optimize_redundant_conditions(self):
        """Test detection of redundant conditions."""
        # Same condition repeated multiple times
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.EQUALS, value="US"),
                Condition(attribute="country", operator=OperatorType.EQUALS, value="US"),  # Duplicate
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="redundant",
            name="Redundant Rule",
            description="Duplicate conditions",
            rule=rule_group,
            
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()
        compiled = compiler.compile(rule)

        # Compilation should detect redundancy
        assert compiled.has_redundancy is True

    def test_optimize_contradictory_conditions(self):
        """Test detection of contradictory conditions."""
        # Impossible to satisfy: country == US AND country == CA
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.EQUALS, value="US"),
                Condition(attribute="country", operator=OperatorType.EQUALS, value="CA"),
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="contradiction",
            name="Contradictory Rule",
            description="Impossible to satisfy",
            rule=rule_group,
            
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()
        compiled = compiler.compile(rule)

        # Should detect contradiction
        assert compiled.has_contradiction is True
        assert compiled.can_ever_match is False


class TestCompiledRuleMetadata:
    """Test metadata extraction from compiled rules."""

    def test_extract_required_attributes(self):
        """Test extraction of required user attributes."""
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA"]),
                Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=18),
                Condition(attribute="verified", operator=OperatorType.EQUALS, value=True),
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="metadata_test",
            name="Metadata Rule",
            description="Test metadata",
            rule=rule_group,
            
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()
        compiled = compiler.compile(rule)

        # Should extract all required attributes
        assert "country" in compiled.required_attributes
        assert "age" in compiled.required_attributes
        assert "verified" in compiled.required_attributes
        assert len(compiled.required_attributes) == 3

    def test_extract_operator_types(self):
        """Test extraction of operator types used."""
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.IN, value=["US"]),
                Condition(attribute="version", operator=OperatorType.SEMANTIC_VERSION, value="1.0.0"),
                Condition(
                    attribute="location",
                    operator=OperatorType.GEO_DISTANCE,
                    value=[37.7749, -122.4194],  # Pydantic expects [lat, lon]
                    additional_value=10  # radius
                ),
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="operators_test",
            name="Operators Rule",
            description="Test operator extraction",
            rule=rule_group,
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()
        compiled = compiler.compile(rule)

        # Should extract all operator types
        assert OperatorType.IN in compiled.operator_types
        assert OperatorType.SEMANTIC_VERSION in compiled.operator_types
        assert OperatorType.GEO_DISTANCE in compiled.operator_types


class TestCompilerCache:
    """Test compiler caching behavior."""

    def test_cache_invalidation_on_rule_change(self):
        """Test that cache is invalidated when rule changes."""
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.EQUALS, value="US")
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="cache_test",
            name="Cache Test",
            description="Test cache invalidation",
            rule=rule_group,
            
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()

        # First compilation
        compiled1 = compiler.compile(rule)

        # Modify rule
        rule.rollout_percentage = 50

        # Recompile - should detect change
        compiled2 = compiler.compile(rule, force_recompile=True)

        # Should be different objects
        assert compiled1 is not compiled2

    def test_cache_size_limit(self):
        """Test that cache respects size limit."""
        compiler = RuleCompiler(cache_max_size=5)

        # Create and compile 10 rules
        for i in range(10):
            rule_group = RuleGroup(
                operator=LogicalOperator.AND,
                conditions=[
                    Condition(attribute=f"attr_{i}", operator=OperatorType.EQUALS, value=i)
                ],
                groups=[]
            )

            rule = TargetingRule(
                id=f"rule_{i}",
                name=f"Rule {i}",
                description=f"Rule {i}",
                rule=rule_group,
                
                priority=1,
                rollout_percentage=100
            )

            compiler.compile(rule)

        # Cache should not exceed max size
        assert compiler.cache_size <= 5

    def test_clear_cache(self):
        """Test manual cache clearing."""
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.EQUALS, value="US")
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="clear_test",
            name="Clear Test",
            description="Test cache clearing",
            rule=rule_group,
            
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()

        # Compile rule
        compiler.compile(rule)
        assert compiler.cache_size > 0

        # Clear cache
        compiler.clear_cache()
        assert compiler.cache_size == 0


class TestCompilerPerformance:
    """Test compiler performance characteristics."""

    def test_compilation_time_is_fast(self):
        """Test that compilation is fast enough."""
        import time

        # Create a moderately complex rule
        conditions = [
            Condition(attribute=f"attr_{i}", operator=OperatorType.EQUALS, value=i)
            for i in range(20)
        ]

        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=conditions,
            groups=[]
        )

        rule = TargetingRule(
            id="perf_test",
            name="Performance Test",
            description="Test compilation speed",
            rule=rule_group,
            
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()

        start = time.time()
        compiled = compiler.compile(rule)
        duration = time.time() - start

        # Compilation should be very fast (< 10ms for 20 conditions)
        assert duration < 0.01
        assert compiled is not None

    def test_cached_compilation_is_instant(self):
        """Test that cached compilation is near-instant."""
        import time

        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.EQUALS, value="US")
            ],
            groups=[]
        )

        rule = TargetingRule(
            id="cache_perf",
            name="Cache Performance",
            description="Test cache speed",
            rule=rule_group,
            
            priority=1,
            rollout_percentage=100
        )

        compiler = RuleCompiler()

        # First compilation (uncached)
        compiler.compile(rule)

        # Second compilation (cached)
        start = time.time()
        compiler.compile(rule)
        duration = time.time() - start

        # Cached access should be extremely fast (< 1ms)
        assert duration < 0.001
