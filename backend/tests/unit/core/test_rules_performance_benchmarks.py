"""
Performance benchmarks for the enhanced rules engine.

This module provides performance tests and benchmarks for the targeting rules
evaluation system to ensure scalability and acceptable response times.
"""

import pytest
import time
import random
import string
from typing import Dict, Any, List
from statistics import mean, median, stdev
from datetime import datetime

from backend.app.schemas.targeting_rule import (
    Condition,
    RuleGroup,
    TargetingRule,
    TargetingRules,
    LogicalOperator,
    OperatorType,
    AttributeType,
)
from backend.app.services.rules_evaluation_service import RulesEvaluationService
from backend.app.core.rule_validation import RuleValidator


class TestRulesPerformanceBenchmarks:
    """Performance benchmarks for rules evaluation."""

    def setup_method(self):
        """Setup test data and benchmarking infrastructure."""
        self.service = RulesEvaluationService()
        self.validator = RuleValidator()
        self.performance_results = {}

    def generate_random_user_context(self, include_advanced_attrs: bool = False) -> Dict[str, Any]:
        """Generate a random user context for testing."""
        countries = ["US", "CA", "UK", "DE", "FR", "JP", "AU", "BR"]
        tiers = ["basic", "premium", "enterprise"]

        context = {
            "user_id": f"user-{''.join(random.choices(string.ascii_lowercase, k=8))}",
            "country": random.choice(countries),
            "subscription_tier": random.choice(tiers),
            "age": random.randint(18, 80),
            "registered_user": random.choice([True, False]),
            "signup_date": datetime.now().isoformat(),
            "tags": random.choices(["beta", "early-adopter", "power-user", "mobile"], k=random.randint(0, 3)),
            "permissions": random.choices(["read", "write", "admin", "delete"], k=random.randint(1, 4))
        }

        if include_advanced_attrs:
            # Add advanced attributes for complex operator testing
            context.update({
                "app_version": f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}",
                "location": [
                    round(random.uniform(-90, 90), 6),  # latitude
                    round(random.uniform(-180, 180), 6)  # longitude
                ],
                "device_info": {
                    "os": random.choice(["iOS", "Android", "Windows"]),
                    "version": f"{random.randint(1,15)}.{random.randint(0,9)}"
                },
                "user_preferences": {
                    "theme": random.choice(["light", "dark"]),
                    "notifications": random.choice([True, False])
                }
            })

        return context

    def create_simple_rule(self, rule_id: str, priority: int = 1) -> TargetingRule:
        """Create a simple targeting rule for benchmarking."""
        condition = Condition(
            attribute="country",
            operator=OperatorType.EQUALS,
            value="US"
        )

        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[condition]
        )

        return TargetingRule(
            id=rule_id,
            rule=rule_group,
            rollout_percentage=100,
            priority=priority
        )

    def create_complex_rule(self, rule_id: str, priority: int = 1) -> TargetingRule:
        """Create a complex targeting rule with nested groups and advanced operators."""
        # First group: Basic demographics
        demo_conditions = [
            Condition(
                attribute="country",
                operator=OperatorType.IN,
                value=["US", "CA", "UK"]
            ),
            Condition(
                attribute="subscription_tier",
                operator=OperatorType.EQUALS,
                value="premium"
            ),
            Condition(
                attribute="age",
                operator=OperatorType.GREATER_THAN_OR_EQUAL,
                value=21
            )
        ]

        demo_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=demo_conditions
        )

        # Second group: Advanced attributes
        advanced_conditions = [
            Condition(
                attribute="app_version",
                operator=OperatorType.SEMANTIC_VERSION,
                value="1.2.0",
                attribute_type=AttributeType.SEMANTIC_VERSION
            ),
            Condition(
                attribute="location",
                operator=OperatorType.GEO_DISTANCE,
                value=[40.7128, -74.0060],  # NYC coordinates
                additional_value=100  # 100km radius
            )
        ]

        advanced_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=advanced_conditions
        )

        # Third group: User behavior
        behavior_conditions = [
            Condition(
                attribute="tags",
                operator=OperatorType.CONTAINS_ANY,
                value=["beta", "early-adopter"]
            ),
            Condition(
                attribute="permissions",
                operator=OperatorType.CONTAINS_ALL,
                value=["read", "write"]
            )
        ]

        behavior_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=behavior_conditions
        )

        # Main group: OR of all groups
        main_group = RuleGroup(
            operator=LogicalOperator.OR,
            groups=[demo_group, advanced_group, behavior_group]
        )

        return TargetingRule(
            id=rule_id,
            rule=main_group,
            rollout_percentage=100,
            priority=priority
        )

    def benchmark_evaluation_time(
        self,
        targeting_rules: TargetingRules,
        user_contexts: List[Dict[str, Any]],
        iterations: int = 1
    ) -> Dict[str, float]:
        """Benchmark rule evaluation time."""
        times = []

        for _ in range(iterations):
            for user_context in user_contexts:
                start_time = time.perf_counter()

                matched_rule, metrics = self.service.evaluate_rules_with_validation(
                    targeting_rules=targeting_rules,
                    user_context=user_context,
                    validate_attributes=True,
                    track_metrics=True
                )

                end_time = time.perf_counter()
                evaluation_time = (end_time - start_time) * 1000  # Convert to milliseconds
                times.append(evaluation_time)

        return {
            "avg_time_ms": mean(times),
            "median_time_ms": median(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "std_dev_ms": stdev(times) if len(times) > 1 else 0,
            "total_evaluations": len(times)
        }

    def test_single_rule_performance(self):
        """Benchmark performance with a single simple rule."""
        rule = self.create_simple_rule("simple_rule")
        targeting_rules = TargetingRules(version="1.0", rules=[rule])

        # Generate test user contexts
        user_contexts = [self.generate_random_user_context() for _ in range(100)]

        # Benchmark evaluation
        results = self.benchmark_evaluation_time(targeting_rules, user_contexts)

        # Performance assertions
        assert results["avg_time_ms"] < 1.0, f"Average evaluation time too high: {results['avg_time_ms']}ms"
        assert results["max_time_ms"] < 5.0, f"Maximum evaluation time too high: {results['max_time_ms']}ms"

        self.performance_results["single_simple_rule"] = results

    def test_multiple_simple_rules_performance(self):
        """Benchmark performance with multiple simple rules."""
        rules = [self.create_simple_rule(f"rule_{i}", priority=i) for i in range(10)]
        targeting_rules = TargetingRules(version="1.0", rules=rules)

        # Generate test user contexts
        user_contexts = [self.generate_random_user_context() for _ in range(100)]

        # Benchmark evaluation
        results = self.benchmark_evaluation_time(targeting_rules, user_contexts)

        # Performance assertions (should scale linearly)
        assert results["avg_time_ms"] < 5.0, f"Average evaluation time too high: {results['avg_time_ms']}ms"
        assert results["max_time_ms"] < 20.0, f"Maximum evaluation time too high: {results['max_time_ms']}ms"

        self.performance_results["multiple_simple_rules"] = results

    def test_complex_rule_performance(self):
        """Benchmark performance with complex nested rules."""
        rule = self.create_complex_rule("complex_rule")
        targeting_rules = TargetingRules(version="1.0", rules=[rule])

        # Generate test user contexts with advanced attributes
        user_contexts = [self.generate_random_user_context(include_advanced_attrs=True) for _ in range(100)]

        # Benchmark evaluation
        results = self.benchmark_evaluation_time(targeting_rules, user_contexts)

        # Performance assertions (complex rules should still be fast)
        assert results["avg_time_ms"] < 10.0, f"Average evaluation time too high: {results['avg_time_ms']}ms"
        assert results["max_time_ms"] < 50.0, f"Maximum evaluation time too high: {results['max_time_ms']}ms"

        self.performance_results["single_complex_rule"] = results

    def test_multiple_complex_rules_performance(self):
        """Benchmark performance with multiple complex rules."""
        rules = [self.create_complex_rule(f"complex_rule_{i}", priority=i) for i in range(5)]
        targeting_rules = TargetingRules(version="1.0", rules=rules)

        # Generate test user contexts with advanced attributes
        user_contexts = [self.generate_random_user_context(include_advanced_attrs=True) for _ in range(50)]

        # Benchmark evaluation
        results = self.benchmark_evaluation_time(targeting_rules, user_contexts)

        # Performance assertions
        assert results["avg_time_ms"] < 25.0, f"Average evaluation time too high: {results['avg_time_ms']}ms"
        assert results["max_time_ms"] < 100.0, f"Maximum evaluation time too high: {results['max_time_ms']}ms"

        self.performance_results["multiple_complex_rules"] = results

    def test_large_scale_rules_performance(self):
        """Benchmark performance with a large number of rules (stress test)."""
        # Mix of simple and complex rules
        rules = []
        for i in range(20):
            if i % 3 == 0:
                rules.append(self.create_complex_rule(f"complex_rule_{i}", priority=i))
            else:
                rules.append(self.create_simple_rule(f"simple_rule_{i}", priority=i))

        targeting_rules = TargetingRules(version="1.0", rules=rules)

        # Generate test user contexts
        user_contexts = [self.generate_random_user_context(include_advanced_attrs=True) for _ in range(50)]

        # Benchmark evaluation
        results = self.benchmark_evaluation_time(targeting_rules, user_contexts)

        # Performance assertions for stress test
        assert results["avg_time_ms"] < 50.0, f"Average evaluation time too high under stress: {results['avg_time_ms']}ms"
        assert results["max_time_ms"] < 200.0, f"Maximum evaluation time too high under stress: {results['max_time_ms']}ms"

        self.performance_results["large_scale_rules"] = results

    def test_validation_performance(self):
        """Benchmark rule validation performance."""
        # Create a complex rule set for validation
        rules = []
        for i in range(10):
            rules.append(self.create_complex_rule(f"complex_rule_{i}", priority=i))

        targeting_rules = TargetingRules(version="1.0", rules=rules)

        # Benchmark validation
        start_time = time.perf_counter()
        result = self.validator.validate_targeting_rules(targeting_rules)
        end_time = time.perf_counter()

        validation_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Performance assertions
        assert validation_time < 100.0, f"Validation time too high: {validation_time}ms"
        assert result.is_valid, "Complex rules should be valid"

        self.performance_results["validation"] = {
            "time_ms": validation_time,
            "is_valid": result.is_valid,
            "issues_count": len(result.issues),
            "complexity_score": result.complexity_score
        }

    def test_memory_usage_scaling(self):
        """Test memory usage doesn't grow excessively with rule evaluations."""
        import tracemalloc

        rule = self.create_complex_rule("memory_test_rule")
        targeting_rules = TargetingRules(version="1.0", rules=[rule])

        # Start memory tracking
        tracemalloc.start()

        # Perform many evaluations
        for i in range(1000):
            user_context = self.generate_random_user_context(include_advanced_attrs=True)
            self.service.evaluate_rules_with_validation(
                targeting_rules=targeting_rules,
                user_context=user_context,
                validate_attributes=True,
                track_metrics=True
            )

            # Clear metrics periodically to prevent unbounded growth
            if i % 100 == 0:
                self.service.clear_metrics()

        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory usage should be reasonable (less than 10MB for this test)
        assert peak < 10 * 1024 * 1024, f"Peak memory usage too high: {peak / 1024 / 1024:.2f} MB"

        self.performance_results["memory_usage"] = {
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024
        }

    def test_concurrent_evaluation_performance(self):
        """Test performance under concurrent evaluation scenarios."""
        import threading
        import queue

        rule = self.create_complex_rule("concurrent_test_rule")
        targeting_rules = TargetingRules(version="1.0", rules=[rule])

        # Results queue for collecting timing data
        results_queue = queue.Queue()

        def evaluate_rules_worker(worker_id: int, num_evaluations: int):
            """Worker function for concurrent evaluations."""
            worker_times = []

            for i in range(num_evaluations):
                user_context = self.generate_random_user_context(include_advanced_attrs=True)
                user_context["user_id"] = f"worker_{worker_id}_user_{i}"

                start_time = time.perf_counter()

                # Create separate service instance for each worker to avoid conflicts
                worker_service = RulesEvaluationService()
                matched_rule, metrics = worker_service.evaluate_rules_with_validation(
                    targeting_rules=targeting_rules,
                    user_context=user_context,
                    validate_attributes=True,
                    track_metrics=True
                )

                end_time = time.perf_counter()
                evaluation_time = (end_time - start_time) * 1000
                worker_times.append(evaluation_time)

            results_queue.put(worker_times)

        # Start multiple worker threads
        num_workers = 4
        evaluations_per_worker = 25
        threads = []

        start_time = time.perf_counter()

        for worker_id in range(num_workers):
            thread = threading.Thread(
                target=evaluate_rules_worker,
                args=(worker_id, evaluations_per_worker)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000

        # Collect all timing results
        all_times = []
        while not results_queue.empty():
            worker_times = results_queue.get()
            all_times.extend(worker_times)

        # Calculate performance metrics
        concurrent_results = {
            "total_time_ms": total_time,
            "total_evaluations": len(all_times),
            "avg_time_ms": mean(all_times),
            "median_time_ms": median(all_times),
            "max_time_ms": max(all_times),
            "evaluations_per_second": len(all_times) / (total_time / 1000)
        }

        # Performance assertions for concurrent execution
        assert concurrent_results["avg_time_ms"] < 15.0, f"Concurrent avg time too high: {concurrent_results['avg_time_ms']}ms"
        assert concurrent_results["evaluations_per_second"] > 50, f"Throughput too low: {concurrent_results['evaluations_per_second']} eval/sec"

        self.performance_results["concurrent_evaluation"] = concurrent_results

    def test_operator_specific_performance(self):
        """Benchmark performance of different operators."""
        operator_results = {}

        # Test different operators
        operators_to_test = [
            (OperatorType.EQUALS, "US"),
            (OperatorType.IN, ["US", "CA", "UK", "DE"]),
            (OperatorType.CONTAINS, "premium"),
            (OperatorType.MATCH_REGEX, r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
            (OperatorType.GREATER_THAN, 25),
            (OperatorType.SEMANTIC_VERSION, "1.2.0"),
            (OperatorType.GEO_DISTANCE, [40.7128, -74.0060]),
            (OperatorType.JSON_PATH, "premium"),
        ]

        for operator, value in operators_to_test:
            condition = Condition(
                attribute="test_attr",
                operator=operator,
                value=value,
                additional_value=10 if operator == OperatorType.GEO_DISTANCE else None
            )

            rule_group = RuleGroup(
                operator=LogicalOperator.AND,
                conditions=[condition]
            )

            targeting_rule = TargetingRule(
                id=f"test_{operator}",
                rule=rule_group,
                rollout_percentage=100,
                priority=1
            )

            targeting_rules = TargetingRules(version="1.0", rules=[targeting_rule])

            # Generate appropriate user contexts for each operator
            user_contexts = []
            for _ in range(100):
                context = self.generate_random_user_context(include_advanced_attrs=True)

                # Set appropriate test attribute based on operator
                if operator == OperatorType.SEMANTIC_VERSION:
                    context["test_attr"] = f"{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}"
                elif operator == OperatorType.GEO_DISTANCE:
                    context["test_attr"] = [
                        round(random.uniform(40, 41), 6),
                        round(random.uniform(-75, -73), 6)
                    ]
                elif operator == OperatorType.JSON_PATH:
                    context["test_attr"] = {"user": {"tier": random.choice(["basic", "premium"])}}
                else:
                    context["test_attr"] = random.choice(["US", "premium", "test@example.com", 30])

                user_contexts.append(context)

            # Benchmark this operator
            results = self.benchmark_evaluation_time(targeting_rules, user_contexts)
            operator_results[operator] = results

        # Store operator-specific performance results
        self.performance_results["operator_performance"] = operator_results

        # Verify no operator is excessively slow
        for operator, results in operator_results.items():
            assert results["avg_time_ms"] < 5.0, f"Operator {operator} too slow: {results['avg_time_ms']}ms"

    def teardown_method(self):
        """Print performance results summary."""
        print("\n" + "="*80)
        print("RULES ENGINE PERFORMANCE BENCHMARK RESULTS")
        print("="*80)

        for test_name, results in self.performance_results.items():
            print(f"\n{test_name.upper().replace('_', ' ')}:")
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, float):
                        print(f"  {key}: {value:.3f}")
                    else:
                        print(f"  {key}: {value}")

        print("\n" + "="*80)