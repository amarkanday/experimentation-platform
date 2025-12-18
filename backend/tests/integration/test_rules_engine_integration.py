"""
Integration tests for the Enhanced Rules Engine.

Tests complex, real-world scenarios combining multiple features:
- Complex nested rule structures
- Real-world targeting use cases
- Backward compatibility
- Performance under realistic loads
"""

import pytest
import time
from datetime import datetime
from typing import Dict, Any

from backend.app.services.rules_evaluation_service import RulesEvaluationService
from backend.app.schemas.targeting_rule import (
    TargetingRule,
    TargetingRules,
    RuleGroup,
    Condition,
    LogicalOperator,
    OperatorType
)


class TestComplexNestedRules:
    """Test complex nested rule structures."""

    def test_three_level_nesting(self):
        """Test evaluation with 3 levels of nesting."""
        service = RulesEvaluationService()

        # Level 3 (deepest)
        level_3_group = RuleGroup(
            operator=LogicalOperator.OR,
            conditions=[
                Condition(attribute="premium", operator=OperatorType.EQUALS, value=True),
                Condition(attribute="lifetime_value", operator=OperatorType.GREATER_THAN, value=1000)
            ],
            groups=[]
        )

        # Level 2
        level_2_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="age", operator=OperatorType.BETWEEN, value=18, additional_value=65),
                Condition(attribute="verified", operator=OperatorType.EQUALS, value=True)
            ],
            groups=[level_3_group]
        )

        # Level 1 (top)
        level_1_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA", "UK"])
            ],
            groups=[level_2_group]
        )

        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="complex_nested",
                    rule=level_1_group,
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        # User that matches all conditions
        matching_user = {
            "user_id": "user_123",
            "country": "US",
            "age": 30,
            "verified": True,
            "premium": True,
            "lifetime_value": 5000
        }

        result = service.evaluate(rules, matching_user)
        assert result.matched is True
        assert result.matched_rule_id == "complex_nested"

        # User that fails at level 3
        non_matching_user = {
            "user_id": "user_456",
            "country": "US",
            "age": 30,
            "verified": True,
            "premium": False,
            "lifetime_value": 500
        }

        result2 = service.evaluate(rules, non_matching_user)
        assert result2.matched is False

    def test_mixed_logical_operators(self):
        """Test complex rules with mixed AND/OR/NOT operators."""
        service = RulesEvaluationService()

        # (country=US AND age>18) OR (country=CA AND verified=True)
        group1 = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.EQUALS, value="US"),
                Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=18)
            ],
            groups=[]
        )

        group2 = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.EQUALS, value="CA"),
                Condition(attribute="verified", operator=OperatorType.EQUALS, value=True)
            ],
            groups=[]
        )

        top_group = RuleGroup(
            operator=LogicalOperator.OR,
            conditions=[],
            groups=[group1, group2]
        )

        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="mixed_operators",
                    rule=top_group,
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        # Matches first group (US, age > 18)
        user1 = {"user_id": "user_1", "country": "US", "age": 25, "verified": False}
        assert service.evaluate(rules, user1).matched is True

        # Matches second group (CA, verified)
        user2 = {"user_id": "user_2", "country": "CA", "age": 15, "verified": True}
        assert service.evaluate(rules, user2).matched is True

        # Matches neither
        user3 = {"user_id": "user_3", "country": "UK", "age": 30, "verified": True}
        assert service.evaluate(rules, user3).matched is False


class TestRealWorldScenarios:
    """Test real-world targeting use cases."""

    def test_premium_user_targeting(self):
        """Test targeting premium users in specific regions during business hours."""
        service = RulesEvaluationService()

        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="premium_users",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            # Geographic targeting
                            Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA", "UK"]),
                            # Premium status
                            Condition(attribute="subscription_tier", operator=OperatorType.IN, value=["premium", "enterprise"]),
                            # Active in last 7 days
                            Condition(attribute="days_since_active", operator=OperatorType.LESS_THAN, value=7),
                            # High engagement
                            Condition(attribute="session_count", operator=OperatorType.GREATER_THAN, value=10)
                        ],
                        groups=[]
                    ),
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        # Matching premium user
        premium_user = {
            "user_id": "premium_123",
            "country": "US",
            "subscription_tier": "premium",
            "days_since_active": 2,
            "session_count": 25
        }

        result = service.evaluate(rules, premium_user)
        assert result.matched is True

        # Non-matching user (free tier)
        free_user = {
            "user_id": "free_456",
            "country": "US",
            "subscription_tier": "free",
            "days_since_active": 1,
            "session_count": 30
        }

        result2 = service.evaluate(rules, free_user)
        assert result2.matched is False

    def test_mobile_users_ios_15_plus(self):
        """Test targeting mobile users on iOS 15+ in specific regions."""
        service = RulesEvaluationService()

        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="mobile_ios_15",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            # Platform
                            Condition(attribute="platform", operator=OperatorType.EQUALS, value="iOS"),
                            # Version (using semantic versioning)
                            Condition(attribute="os_version", operator=OperatorType.SEMANTIC_VERSION, value="15.0.0", additional_value="gte"),
                            # Device type
                            Condition(attribute="device_type", operator=OperatorType.IN, value=["iPhone", "iPad"]),
                            # Geographic
                            Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA"])
                        ],
                        groups=[]
                    ),
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        # Matching user
        ios_user = {
            "user_id": "ios_user_123",
            "platform": "iOS",
            "os_version": "16.2.0",
            "device_type": "iPhone",
            "country": "US"
        }

        result = service.evaluate(rules, ios_user)
        assert result.matched is True

        # Non-matching (old iOS version)
        old_ios_user = {
            "user_id": "ios_user_456",
            "platform": "iOS",
            "os_version": "14.5.0",
            "device_type": "iPhone",
            "country": "US"
        }

        result2 = service.evaluate(rules, old_ios_user)
        assert result2.matched is False

    def test_geographic_proximity_targeting(self):
        """Test targeting users near specific locations."""
        service = RulesEvaluationService()

        # San Francisco coordinates
        sf_coords = [37.7749, -122.4194]

        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="sf_proximity",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            # Within 20km of San Francisco (~12 miles)
                            Condition(
                                attribute="location",
                                operator=OperatorType.GEO_DISTANCE,
                                value=sf_coords,
                                additional_value=20  # radius in kilometers
                            ),
                            # Active user
                            Condition(attribute="active", operator=OperatorType.EQUALS, value=True)
                        ],
                        groups=[]
                    ),
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        # User near San Francisco (Oakland - ~16km away)
        nearby_user = {
            "user_id": "nearby_123",
            "location": [37.8044, -122.2712],  # Oakland coords
            "active": True
        }

        result = service.evaluate(rules, nearby_user)
        assert result.matched is True

        # User far from San Francisco (Los Angeles - ~560km away)
        far_user = {
            "user_id": "far_456",
            "location": [34.0522, -118.2437],  # LA coords
            "active": True
        }

        result2 = service.evaluate(rules, far_user)
        assert result2.matched is False

    def test_time_based_targeting(self):
        """Test targeting based on time windows."""
        service = RulesEvaluationService()

        # Define a time window (Jan 1 9am to Jan 5 5pm)
        start_time = datetime(2024, 1, 1, 9, 0, 0)
        end_time = datetime(2024, 1, 5, 17, 0, 0)

        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="time_window",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            # Within time window
                            Condition(
                                attribute="current_time",
                                operator=OperatorType.TIME_WINDOW,
                                value={
                                    "start": start_time.isoformat(),
                                    "end": end_time.isoformat()
                                }
                            ),
                            # Active subscription
                            Condition(attribute="has_subscription", operator=OperatorType.EQUALS, value=True)
                        ],
                        groups=[]
                    ),
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        # Jan 2 at 10am (within window)
        within_window_time = datetime(2024, 1, 2, 10, 0, 0)
        user1 = {
            "user_id": "user_1",
            "current_time": within_window_time.isoformat(),  # Convert to string for caching
            "has_subscription": True
        }

        result1 = service.evaluate(rules, user1)
        assert result1.matched is True

        # Jan 7 at 10am (outside window)
        outside_window_time = datetime(2024, 1, 7, 10, 0, 0)
        user2 = {
            "user_id": "user_2",
            "current_time": outside_window_time.isoformat(),  # Convert to string for caching
            "has_subscription": True
        }

        result2 = service.evaluate(rules, user2)
        assert result2.matched is False


class TestBackwardCompatibility:
    """Test backward compatibility with existing rule structures."""

    def test_simple_rules_still_work(self):
        """Test that simple rules from before enhancements still work."""
        service = RulesEvaluationService()

        # Old-style simple rule
        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="simple_rule",
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
            ],
            default_rule=None
        )

        user = {"user_id": "user_123", "country": "US"}
        result = service.evaluate(rules, user)

        assert result.matched is True
        assert result.matched_rule_id == "simple_rule"

    def test_basic_operators_unchanged(self):
        """Test that basic operators (eq, neq, gt, lt, in) still work as before."""
        service = RulesEvaluationService()

        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="basic_operators",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(attribute="country", operator=OperatorType.EQUALS, value="US"),
                            Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=18),
                            Condition(attribute="role", operator=OperatorType.IN, value=["admin", "user"]),
                            Condition(attribute="banned", operator=OperatorType.NOT_EQUALS, value=True)
                        ],
                        groups=[]
                    ),
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        user = {
            "user_id": "user_123",
            "country": "US",
            "age": 25,
            "role": "user",
            "banned": False
        }

        result = service.evaluate(rules, user)
        assert result.matched is True

    def test_rollout_percentage_still_works(self):
        """Test that rollout percentage functionality is preserved."""
        service = RulesEvaluationService()

        # Rule with 0% rollout - should never match
        rules_0_percent = TargetingRules(
            rules=[
                TargetingRule(
                    id="zero_rollout",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(attribute="country", operator=OperatorType.EQUALS, value="US")
                        ],
                        groups=[]
                    ),
                    priority=1,
                    rollout_percentage=0
                )
            ],
            default_rule=None
        )

        user = {"user_id": "user_123", "country": "US"}
        result = service.evaluate(rules_0_percent, user)
        assert result.matched is False

        # Rule with 100% rollout - should always match for matching conditions
        rules_100_percent = TargetingRules(
            rules=[
                TargetingRule(
                    id="full_rollout",
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
            ],
            default_rule=None
        )

        result2 = service.evaluate(rules_100_percent, user)
        assert result2.matched is True


class TestPerformanceIntegration:
    """Test performance with realistic loads."""

    def test_evaluate_1000_users_quickly(self):
        """Test evaluating 1000 users with complex rules completes quickly."""
        service = RulesEvaluationService()

        # Complex rule with multiple conditions
        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="complex_rule",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA", "UK"]),
                            Condition(attribute="age", operator=OperatorType.BETWEEN, value=18, additional_value=65),
                            Condition(attribute="verified", operator=OperatorType.EQUALS, value=True),
                            Condition(attribute="premium", operator=OperatorType.EQUALS, value=True)
                        ],
                        groups=[]
                    ),
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        # Generate 1000 user contexts
        users = [
            {
                "user_id": f"user_{i}",
                "country": ["US", "CA", "UK"][i % 3],
                "age": 20 + (i % 45),
                "verified": i % 2 == 0,
                "premium": i % 3 == 0
            }
            for i in range(1000)
        ]

        # Time the batch evaluation
        start = time.time()
        results = service.batch_evaluate(rules, users)
        duration = time.time() - start

        assert len(results) == 1000
        # Should complete in under 5 seconds (target: < 1s)
        assert duration < 5.0

    def test_caching_improves_repeated_evaluations(self):
        """Test that caching significantly improves repeated evaluations."""
        service = RulesEvaluationService()

        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="cached_rule",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA", "UK"]),
                            Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=18),
                            Condition(attribute="verified", operator=OperatorType.EQUALS, value=True)
                        ],
                        groups=[]
                    ),
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        user = {
            "user_id": "user_123",
            "country": "US",
            "age": 25,
            "verified": True
        }

        # First 100 evaluations (building cache)
        start1 = time.time()
        for _ in range(100):
            service.evaluate(rules, user)
        duration1 = time.time() - start1

        # Clear metrics but keep cache
        service.reset_metrics()

        # Next 100 evaluations (all cache hits)
        start2 = time.time()
        for _ in range(100):
            service.evaluate(rules, user)
        duration2 = time.time() - start2

        # Cached evaluations should be faster
        assert duration2 < duration1

        # Check cache hit rate
        metrics = service.get_metrics()
        assert metrics.cache_hits > 90  # Most should be cache hits

    def test_multiple_rules_evaluated_efficiently(self):
        """Test evaluation with multiple competing rules is efficient."""
        service = RulesEvaluationService()

        # Create 10 rules with different priorities
        rule_list = []
        for i in range(10):
            rule_list.append(
                TargetingRule(
                    id=f"rule_{i}",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(attribute="score", operator=OperatorType.GREATER_THAN, value=i * 10)
                        ],
                        groups=[]
                    ),
                    priority=i,
                    rollout_percentage=100
                )
            )

        rules = TargetingRules(rules=rule_list, default_rule=None)

        # Test with various users
        users = [{"user_id": f"user_{i}", "score": i * 5} for i in range(100)]

        start = time.time()
        results = service.batch_evaluate(rules, users)
        duration = time.time() - start

        assert len(results) == 100
        # Should be fast even with 10 rules
        assert duration < 2.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_user_context(self):
        """Test evaluation with empty user context."""
        service = RulesEvaluationService()

        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="requires_country",
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
            ],
            default_rule=None
        )

        empty_context = {}
        result = service.evaluate(rules, empty_context)

        assert result.matched is False

    def test_null_attribute_values(self):
        """Test handling of null attribute values."""
        service = RulesEvaluationService()

        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="check_premium",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(attribute="premium", operator=OperatorType.EQUALS, value=True)
                        ],
                        groups=[]
                    ),
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        user_with_null = {"user_id": "user_123", "premium": None}
        result = service.evaluate(rules, user_with_null)

        # Should handle gracefully (not match)
        assert result.matched is False

    def test_very_large_array_values(self):
        """Test handling of large arrays in IN conditions."""
        service = RulesEvaluationService()

        # Very large list of countries
        large_country_list = [f"COUNTRY_{i}" for i in range(1000)]
        large_country_list.append("US")

        rules = TargetingRules(
            rules=[
                TargetingRule(
                    id="large_list",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(attribute="country", operator=OperatorType.IN, value=large_country_list)
                        ],
                        groups=[]
                    ),
                    priority=1,
                    rollout_percentage=100
                )
            ],
            default_rule=None
        )

        user = {"user_id": "user_123", "country": "US"}
        result = service.evaluate(rules, user)

        assert result.matched is True
