"""
Performance Benchmark Tests for Feature Flag Lambda (Day 5).

Tests performance characteristics and validates against EP-010 requirements:
- Target P99 latency: < 40ms
- Target throughput: > 1000 evaluations/second
- Cache hit rate: > 95%

Following TDD (Test-Driven Development) - Performance validation phase.
"""

import pytest
import sys
import time
import statistics
from pathlib import Path
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from evaluator import FeatureFlagEvaluator
from models import FeatureFlagConfig, VariantConfig


class TestPerformanceBenchmarks:
    """Performance benchmark tests for feature flag evaluation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.simple_flag = FeatureFlagConfig(
            flag_id="perf_flag_123",
            key="perf_test_flag",
            enabled=True,
            rollout_percentage=100.0
        )

        self.targeted_flag = FeatureFlagConfig(
            flag_id="perf_flag_targeted",
            key="perf_targeted_flag",
            enabled=True,
            rollout_percentage=100.0,
            targeting_rules=[
                {"attribute": "country", "operator": "equals", "value": "US"},
                {"attribute": "age", "operator": "greater_than", "value": 18}
            ]
        )

        self.variant_flag = FeatureFlagConfig(
            flag_id="perf_flag_variant",
            key="perf_variant_flag",
            enabled=True,
            rollout_percentage=100.0,
            default_variant="control",
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

    # ====================================================================
    # Performance Target: < 40ms P99 latency
    # ====================================================================

    def test_single_evaluation_latency_simple_flag(self):
        """Test that simple flag evaluation meets P99 < 40ms target."""
        evaluator = FeatureFlagEvaluator()

        latencies = []
        num_iterations = 1000

        for i in range(num_iterations):
            start = time.perf_counter()
            evaluator.evaluate(
                user_id=f"user_{i}",
                flag_config=self.simple_flag
            )
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms

        # Calculate percentiles
        p50 = statistics.quantiles(latencies, n=100)[49]  # 50th percentile
        p95 = statistics.quantiles(latencies, n=100)[94]  # 95th percentile
        p99 = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        avg = statistics.mean(latencies)

        print(f"\n[Simple Flag] Latencies (ms): avg={avg:.2f}, p50={p50:.2f}, p95={p95:.2f}, p99={p99:.2f}")

        # Validate against targets
        assert p99 < 40, f"P99 latency {p99:.2f}ms exceeds target 40ms"
        assert p95 < 20, f"P95 latency {p95:.2f}ms should be well below P99 target"
        assert avg < 10, f"Average latency {avg:.2f}ms should be very low"

    def test_single_evaluation_latency_with_targeting(self):
        """Test evaluation with targeting rules meets performance targets."""
        evaluator = FeatureFlagEvaluator()
        context = {"country": "US", "age": 25}

        latencies = []
        num_iterations = 1000

        for i in range(num_iterations):
            start = time.perf_counter()
            evaluator.evaluate(
                user_id=f"user_{i}",
                flag_config=self.targeted_flag,
                context=context
            )
            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        p99 = statistics.quantiles(latencies, n=100)[98]
        p95 = statistics.quantiles(latencies, n=100)[94]
        avg = statistics.mean(latencies)

        print(f"\n[Targeted Flag] Latencies (ms): avg={avg:.2f}, p95={p95:.2f}, p99={p99:.2f}")

        # Targeting adds minimal overhead
        assert p99 < 40, f"P99 latency {p99:.2f}ms exceeds target"
        assert avg < 15, f"Average latency {avg:.2f}ms with targeting should be low"

    def test_single_evaluation_latency_with_variants(self):
        """Test evaluation with variants meets performance targets."""
        evaluator = FeatureFlagEvaluator()

        latencies = []
        num_iterations = 1000

        for i in range(num_iterations):
            start = time.perf_counter()
            evaluator.evaluate(
                user_id=f"user_{i}",
                flag_config=self.variant_flag
            )
            end = time.perf_counter()
            latencies.append((end - start) * 1000)

        p99 = statistics.quantiles(latencies, n=100)[98]
        avg = statistics.mean(latencies)

        print(f"\n[Variant Flag] Latencies (ms): avg={avg:.2f}, p99={p99:.2f}")

        assert p99 < 40, f"P99 latency {p99:.2f}ms exceeds target"
        assert avg < 15, f"Average latency {avg:.2f}ms with variants should be low"

    # ====================================================================
    # Performance Target: > 1000 evaluations/second throughput
    # ====================================================================

    def test_throughput_single_threaded(self):
        """Test that single-threaded throughput meets > 1000 eval/s target."""
        evaluator = FeatureFlagEvaluator()

        num_evaluations = 5000
        start = time.perf_counter()

        for i in range(num_evaluations):
            evaluator.evaluate(
                user_id=f"user_{i % 100}",  # Reuse users for realism
                flag_config=self.simple_flag
            )

        end = time.perf_counter()
        duration = end - start
        throughput = num_evaluations / duration

        print(f"\n[Throughput] Single-threaded: {throughput:.0f} eval/s over {duration:.2f}s")

        assert throughput > 1000, \
            f"Throughput {throughput:.0f} eval/s below target 1000 eval/s"

    def test_throughput_concurrent(self):
        """Test concurrent evaluation throughput with multiple threads."""
        evaluator = FeatureFlagEvaluator()

        num_threads = 4
        evaluations_per_thread = 1000

        def evaluate_batch(thread_id):
            """Evaluate a batch of flags."""
            for i in range(evaluations_per_thread):
                evaluator.evaluate(
                    user_id=f"user_{thread_id}_{i}",
                    flag_config=self.simple_flag
                )

        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(evaluate_batch, thread_id)
                for thread_id in range(num_threads)
            ]
            for future in as_completed(futures):
                future.result()

        end = time.perf_counter()
        duration = end - start
        total_evaluations = num_threads * evaluations_per_thread
        throughput = total_evaluations / duration

        print(f"\n[Throughput] Concurrent ({num_threads} threads): {throughput:.0f} eval/s over {duration:.2f}s")

        # Concurrent should still meet target
        assert throughput > 1000, \
            f"Concurrent throughput {throughput:.0f} eval/s below target"

    # ====================================================================
    # Cache Performance: > 95% hit rate
    # ====================================================================

    @patch('evaluator.get_dynamodb_resource')
    def test_cache_hit_rate_with_repeated_flags(self, mock_get_resource):
        """Test cache achieves > 95% hit rate with realistic usage pattern."""
        # Mock DynamoDB
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'cached_flag',
                'key': 'cached_feature',
                'enabled': True,
                'rollout_percentage': 100.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        evaluator = FeatureFlagEvaluator()

        # Simulate realistic pattern: multiple evaluations of same flags
        num_flags = 10
        evaluations_per_flag = 100

        for _ in range(evaluations_per_flag):
            for flag_id in range(num_flags):
                evaluator.get_flag_config_cached(f"flag_{flag_id}")

        total_requests = num_flags * evaluations_per_flag
        # First request for each flag is a miss, rest are hits
        expected_hits = total_requests - num_flags
        expected_hit_rate = expected_hits / total_requests

        actual_hit_rate = evaluator.get_cache_hit_rate()

        print(f"\n[Cache] Hit rate: {actual_hit_rate:.2%} (expected: {expected_hit_rate:.2%})")

        assert actual_hit_rate >= 0.95, \
            f"Cache hit rate {actual_hit_rate:.2%} below target 95%"

        # DynamoDB should only be called once per unique flag
        assert mock_table.get_item.call_count == num_flags, \
            f"Expected {num_flags} DynamoDB calls, got {mock_table.get_item.call_count}"

    @patch('evaluator.get_dynamodb_resource')
    def test_cache_reduces_latency(self, mock_get_resource):
        """Test that caching significantly reduces latency."""
        # Mock DynamoDB with artificial delay
        mock_table = Mock()

        def slow_get_item(**kwargs):
            time.sleep(0.005)  # 5ms DynamoDB delay
            return {
                'Item': {
                    'flag_id': 'slow_flag',
                    'key': 'slow_feature',
                    'enabled': True,
                    'rollout_percentage': 100.0
                }
            }

        mock_table.get_item = Mock(side_effect=slow_get_item)
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        evaluator = FeatureFlagEvaluator()

        # First call - cache miss (with DynamoDB delay)
        start = time.perf_counter()
        evaluator.get_flag_config_cached("slow_feature")
        first_call_time = (time.perf_counter() - start) * 1000

        # Second call - cache hit (no DynamoDB delay)
        start = time.perf_counter()
        evaluator.get_flag_config_cached("slow_feature")
        second_call_time = (time.perf_counter() - start) * 1000

        print(f"\n[Cache Latency] First call: {first_call_time:.2f}ms, Cached call: {second_call_time:.2f}ms")

        # Cached call should be at least 2x faster
        assert second_call_time < first_call_time / 2, \
            "Cache should significantly reduce latency"

        # Cached call should be very fast
        assert second_call_time < 1.0, \
            f"Cached call {second_call_time:.2f}ms should be < 1ms"

    # ====================================================================
    # Batch Evaluation Performance
    # ====================================================================

    def test_batch_evaluation_performance(self):
        """Test batch evaluation of multiple users is efficient."""
        evaluator = FeatureFlagEvaluator()

        num_users = 1000
        users = [f"user_{i}" for i in range(num_users)]

        # Measure batch evaluation time
        start = time.perf_counter()
        for user_id in users:
            evaluator.evaluate(
                user_id=user_id,
                flag_config=self.simple_flag
            )
        end = time.perf_counter()

        duration_ms = (end - start) * 1000
        avg_per_user_ms = duration_ms / num_users

        print(f"\n[Batch] {num_users} users in {duration_ms:.2f}ms (avg {avg_per_user_ms:.3f}ms/user)")

        # Average should be well below P99 target
        assert avg_per_user_ms < 5.0, \
            f"Average per-user latency {avg_per_user_ms:.3f}ms should be < 5ms"

        # Total batch should be fast
        assert duration_ms < 5000, \
            f"Batch of {num_users} users took {duration_ms:.2f}ms, should be < 5s"

    # ====================================================================
    # Memory Efficiency
    # ====================================================================

    def test_memory_efficiency_with_many_evaluations(self):
        """Test that memory usage remains stable with many evaluations."""
        evaluator = FeatureFlagEvaluator()

        # Perform many evaluations
        num_evaluations = 10000

        start = time.perf_counter()
        for i in range(num_evaluations):
            evaluator.evaluate(
                user_id=f"user_{i}",
                flag_config=self.simple_flag
            )
        end = time.perf_counter()

        duration = end - start
        throughput = num_evaluations / duration

        print(f"\n[Memory Test] {num_evaluations} evaluations in {duration:.2f}s ({throughput:.0f} eval/s)")

        # Should maintain high throughput even with many evaluations
        assert throughput > 1000, \
            f"Throughput {throughput:.0f} eval/s dropped below target after many evaluations"

    # ====================================================================
    # Statistical Consistency
    # ====================================================================

    def test_rollout_percentage_accuracy_at_scale(self):
        """Test that rollout percentage remains accurate at scale."""
        partial_rollout_flag = FeatureFlagConfig(
            flag_id="rollout_test",
            key="rollout_50",
            enabled=True,
            rollout_percentage=50.0
        )

        evaluator = FeatureFlagEvaluator()

        # Evaluate large sample
        num_users = 10000
        enabled_count = 0

        start = time.perf_counter()
        for i in range(num_users):
            result = evaluator.evaluate(
                user_id=f"user_{i}",
                flag_config=partial_rollout_flag
            )
            if result["enabled"]:
                enabled_count += 1
        end = time.perf_counter()

        enabled_rate = enabled_count / num_users
        duration = end - start

        print(f"\n[Rollout Accuracy] {enabled_count}/{num_users} = {enabled_rate:.2%} (target: 50%) in {duration:.2f}s")

        # Should be within ±1% of target (with large sample)
        assert 0.49 <= enabled_rate <= 0.51, \
            f"Rollout rate {enabled_rate:.2%} outside ±1% of target 50%"

        # Should maintain good throughput
        throughput = num_users / duration
        assert throughput > 1000, \
            f"Throughput {throughput:.0f} eval/s below target during accuracy test"
