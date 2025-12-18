"""
Performance benchmarks for rules engine optimizations.

Measures the performance impact of:
- Rule compilation
- Evaluation caching
- Operator execution
"""

import pytest
import time
from datetime import datetime

from backend.app.core.rules_engine import evaluate_targeting_rules, apply_operator
from backend.app.core.rule_compiler import RuleCompiler
from backend.app.core.evaluation_cache import EvaluationCache
from backend.app.schemas.targeting_rule import (
    TargetingRule,
    TargetingRules,
    RuleGroup,
    Condition,
    LogicalOperator,
    OperatorType
)


class TestOperatorPerformance:
    """Benchmark individual operator performance."""

    def test_simple_equality_performance(self):
        """Benchmark simple equality operator."""
        iterations = 10000

        start = time.time()
        for _ in range(iterations):
            apply_operator(OperatorType.EQUALS, "US", "US")
        duration = time.time() - start

        # Should be very fast (< 10ms for 10k operations)
        assert duration < 0.01
        ops_per_second = iterations / duration
        assert ops_per_second > 100000  # > 100k ops/sec

    def test_string_contains_performance(self):
        """Benchmark string contains operator."""
        iterations = 10000

        start = time.time()
        for _ in range(iterations):
            apply_operator(OperatorType.CONTAINS, "hello world", "world")
        duration = time.time() - start

        # Should be fast
        assert duration < 0.05
        ops_per_second = iterations / duration
        assert ops_per_second > 20000  # > 20k ops/sec

    def test_semantic_version_performance(self):
        """Benchmark semantic version comparison."""
        iterations = 1000  # Fewer iterations for complex operation

        start = time.time()
        for _ in range(iterations):
            apply_operator(
                OperatorType.SEMANTIC_VERSION,
                "1.2.3",
                "1.0.0",
                additional_value="gt"
            )
        duration = time.time() - start

        # Should be reasonably fast
        assert duration < 0.1  # < 100ms for 1k operations
        ops_per_second = iterations / duration
        assert ops_per_second > 1000  # > 1k ops/sec

    def test_geo_distance_performance(self):
        """Benchmark geographic distance calculation."""
        iterations = 1000

        start = time.time()
        for _ in range(iterations):
            apply_operator(
                OperatorType.GEO_DISTANCE,
                {"lat": 37.7749, "lon": -122.4194},
                {"lat": 37.8044, "lon": -122.2712, "radius": 15, "unit": "miles"}
            )
        duration = time.time() - start

        # Should be reasonably fast despite math operations
        assert duration < 0.2  # < 200ms for 1k operations
        ops_per_second = iterations / duration
        assert ops_per_second > 500  # > 500 ops/sec

    def test_time_window_performance(self):
        """Benchmark time window operator."""
        iterations = 1000

        dt = datetime(2024, 1, 2, 10, 0, 0)

        start = time.time()
        for _ in range(iterations):
            apply_operator(
                OperatorType.TIME_WINDOW,
                dt,
                {
                    "days": [0, 1, 2, 3, 4],  # Weekdays
                    "start_time": "09:00",
                    "end_time": "17:00"
                }
            )
        duration = time.time() - start

        # Should be fast
        assert duration < 0.1
        ops_per_second = iterations / duration
        assert ops_per_second > 1000  # > 1k ops/sec


class TestRuleCompilationPerformance:
    """Benchmark rule compilation performance."""

    def test_simple_rule_compilation(self):
        """Benchmark compiling simple rules."""
        compiler = RuleCompiler()
        iterations = 1000

        rule = TargetingRule(
            id="test_rule",
            rule=RuleGroup(
                operator=LogicalOperator.AND,
                conditions=[
                    Condition(attribute="country", operator=OperatorType.EQUALS, value="US")
                ],
                groups=[]
            ),
            priority=1,
            rollout_percentage=100
        )

        start = time.time()
        for i in range(iterations):
            # Modify rule slightly to avoid cache
            rule.rollout_percentage = 50 + (i % 51)
            compiler.compile(rule, force_recompile=True)
        duration = time.time() - start

        # Should be very fast
        assert duration < 1.0  # < 1s for 1k compilations
        compilations_per_second = iterations / duration
        assert compilations_per_second > 100  # > 100 compilations/sec

    def test_complex_rule_compilation(self):
        """Benchmark compiling complex rules with nesting."""
        compiler = RuleCompiler()
        iterations = 100  # Fewer iterations for complex rules

        # Create a complex nested rule
        inner_group = RuleGroup(
            operator=LogicalOperator.OR,
            conditions=[
                Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=18),
                Condition(attribute="verified", operator=OperatorType.EQUALS, value=True),
                Condition(attribute="premium", operator=OperatorType.EQUALS, value=True),
            ],
            groups=[]
        )

        outer_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA", "UK"]),
                Condition(attribute="active", operator=OperatorType.EQUALS, value=True),
            ],
            groups=[inner_group]
        )

        rule = TargetingRule(
            id="complex_rule",
            rule=outer_group,
            priority=1,
            rollout_percentage=100
        )

        start = time.time()
        for _ in range(iterations):
            compiler.compile(rule, force_recompile=True)
        duration = time.time() - start

        # Should still be reasonably fast
        assert duration < 1.0  # < 1s for 100 complex compilations
        compilations_per_second = iterations / duration
        assert compilations_per_second > 10  # > 10 compilations/sec

    def test_compilation_cache_speedup(self):
        """Measure cache speedup for compilation."""
        compiler = RuleCompiler()

        # Create a more complex rule to make compilation overhead more significant
        inner_group = RuleGroup(
            operator=LogicalOperator.OR,
            conditions=[
                Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=18),
                Condition(attribute="verified", operator=OperatorType.EQUALS, value=True),
                Condition(attribute="premium", operator=OperatorType.EQUALS, value=True),
            ],
            groups=[]
        )

        outer_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA", "UK"]),
                Condition(attribute="active", operator=OperatorType.EQUALS, value=True),
            ],
            groups=[inner_group]
        )

        rule = TargetingRule(
            id="cache_test",
            rule=outer_group,
            priority=1,
            rollout_percentage=100
        )

        # Time uncached compilation
        start = time.time()
        for _ in range(1000):
            compiler.compile(rule, force_recompile=True)
        uncached_duration = time.time() - start

        # Clear cache and compile once
        compiler.clear_cache()
        compiler.compile(rule)

        # Time cached compilation
        start = time.time()
        for _ in range(1000):
            compiler.compile(rule)
        cached_duration = time.time() - start

        # Cached should be faster (at least 1.3x)
        # Note: Speedup is modest because compilation is already very fast,
        # and cache lookup has its own overhead (hashing, dict access)
        speedup = uncached_duration / cached_duration
        assert speedup > 1.3
        assert compiler.cache_hits >= 1000

        # Verify cached compilation is still very fast (< 50ms total for 1000 lookups)
        assert cached_duration < 0.05


class TestEvaluationCachePerformance:
    """Benchmark evaluation caching performance."""

    def test_cache_lookup_performance(self):
        """Benchmark cache lookup speed."""
        cache = EvaluationCache()
        iterations = 10000

        # Pre-populate cache
        for i in range(100):
            cache.set(f"rule_{i}", {"user_id": f"user_{i}"}, True)

        # Benchmark lookups
        start = time.time()
        for i in range(iterations):
            cache.get(f"rule_{i % 100}", {"user_id": f"user_{i % 100}"})
        duration = time.time() - start

        # Should be very fast
        assert duration < 0.1  # < 100ms for 10k lookups
        lookups_per_second = iterations / duration
        assert lookups_per_second > 10000  # > 10k lookups/sec

    def test_cache_write_performance(self):
        """Benchmark cache write speed."""
        cache = EvaluationCache()
        iterations = 10000

        start = time.time()
        for i in range(iterations):
            cache.set(f"rule_{i % 100}", {"user_id": f"user_{i}"}, True)
        duration = time.time() - start

        # Should be fast
        assert duration < 0.5  # < 500ms for 10k writes
        writes_per_second = iterations / duration
        assert writes_per_second > 1000  # > 1k writes/sec


class TestEndToEndPerformance:
    """Benchmark end-to-end rule evaluation performance."""

    def test_evaluation_without_cache(self):
        """Benchmark rule evaluation without caching."""
        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="rule_1",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(attribute="country", operator=OperatorType.EQUALS, value="US"),
                            Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=18),
                        ],
                        groups=[]
                    ),
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        user_context = {
            "user_id": "user_123",
            "country": "US",
            "age": 25
        }

        iterations = 1000

        start = time.time()
        for _ in range(iterations):
            evaluate_targeting_rules(rules, user_context)
        duration = time.time() - start

        # Should be fast
        assert duration < 1.0  # < 1s for 1k evaluations
        evaluations_per_second = iterations / duration
        assert evaluations_per_second > 100  # > 100 evaluations/sec

    def test_complex_multi_rule_evaluation(self):
        """Benchmark evaluation with multiple complex rules."""
        # Create 10 rules with various conditions
        rule_list = []
        for i in range(10):
            rule_list.append(
                TargetingRule(
                    id=f"rule_{i}",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA", "UK"]),
                            Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=18 + i),
                            Condition(attribute="verified", operator=OperatorType.EQUALS, value=True),
                        ],
                        groups=[]
                    ),
                    priority=i,
                    rollout_percentage=100
                )
            )

        rules = TargetingRules(rules=rule_list, default_rule=None)

        user_context = {
            "user_id": "user_123",
            "country": "US",
            "age": 25,
            "verified": True
        }

        iterations = 100

        start = time.time()
        for _ in range(iterations):
            evaluate_targeting_rules(rules, user_context)
        duration = time.time() - start

        # Should still be reasonably fast
        assert duration < 1.0  # < 1s for 100 complex evaluations
        evaluations_per_second = iterations / duration
        assert evaluations_per_second > 10  # > 10 complex evaluations/sec


class TestPerformanceComparison:
    """Compare performance with and without optimizations."""

    def test_cache_hit_vs_miss(self):
        """Compare cache hit vs miss performance."""
        cache = EvaluationCache()

        user_context = {"user_id": "user_123", "country": "US"}
        rule_id = "test_rule"

        # Measure cache miss (first lookup)
        start = time.time()
        for _ in range(1000):
            result = cache.get(rule_id, user_context)
            assert result is None
        miss_duration = time.time() - start

        # Store result
        cache.set(rule_id, user_context, True)

        # Measure cache hit
        start = time.time()
        for _ in range(1000):
            result = cache.get(rule_id, user_context)
            assert result is True
        hit_duration = time.time() - start

        # Cache hits should be similar speed or faster (due to no re-evaluation)
        # Both should be very fast
        assert hit_duration < 0.1
        assert miss_duration < 0.1

    def test_compiled_vs_uncompiled_validation(self):
        """Compare validation performance: compiled vs on-the-fly."""
        compiler = RuleCompiler()

        rule = TargetingRule(
            id="perf_test",
            rule=RuleGroup(
                operator=LogicalOperator.AND,
                conditions=[
                    Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA"]),
                    Condition(attribute="age", operator=OperatorType.BETWEEN, value=18, additional_value=65),
                ],
                groups=[]
            ),
            priority=1,
            rollout_percentage=100
        )

        # Compile rule
        compiled = compiler.compile(rule)

        # Verify compilation succeeded and metadata is extracted
        assert compiled.is_valid
        assert compiled.condition_count == 2
        assert "country" in compiled.required_attributes
        assert "age" in compiled.required_attributes

        # This benchmark verifies that compilation is fast enough
        # to be useful (< 1ms per rule)
        start = time.time()
        for _ in range(1000):
            compiler.compile(rule)  # Uses cache
        duration = time.time() - start

        assert duration < 0.1  # Cached compilation is very fast
