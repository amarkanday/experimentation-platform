"""
Unit tests for the enhanced rules engine.

This module tests the functionality of the enhanced rules engine for feature flag targeting.
"""
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from backend.app.schemas.targeting_rule import (
    Condition,
    RuleGroup,
    TargetingRule,
    TargetingRules,
    LogicalOperator,
    OperatorType
)
from backend.app.core.rules_engine import (
    evaluate_targeting_rules,
    evaluate_rule,
    evaluate_rule_group,
    evaluate_condition,
    apply_operator,
    should_include_in_rollout,
    get_stable_user_id,
)

# Test Data
USER_ID = "test-user-123"
PREMIUM_USER_CONTEXT = {
    "user_id": "test-user-123",
    "country": "US",
    "subscription_tier": "premium",
    "age": 30,
    "registered_user": True,
    "signup_date": datetime.now().isoformat(),
    "tags": ["beta", "early-adopter"],
    "permissions": ["read", "write", "admin"]
}

NON_PREMIUM_USER_CONTEXT = {
    "user_id": "test-user-123",
    "country": "UK",
    "subscription_tier": "basic",
    "age": 25,
    "registered_user": True,
    "signup_date": (datetime.now() - timedelta(days=30)).isoformat(),
    "tags": ["free-tier"],
    "permissions": ["read"]
}


class TestConditionEvaluation:
    """Tests for individual condition evaluation."""

    def test_equals_operator(self):
        """Test the equals operator."""
        condition = Condition(
            attribute="subscription_tier",
            operator=OperatorType.EQUALS,
            value="premium"
        )

        # Test with matching value
        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is True

        # Test with non-matching value
        assert evaluate_condition(condition, NON_PREMIUM_USER_CONTEXT) is False

    def test_not_equals_operator(self):
        """Test the not equals operator."""
        condition = Condition(
            attribute="subscription_tier",
            operator=OperatorType.NOT_EQUALS,
            value="basic"
        )

        # Test with non-matching value (should be true)
        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is True

        # Test with matching value (should be false)
        assert evaluate_condition(condition, NON_PREMIUM_USER_CONTEXT) is False

    def test_in_operator(self):
        """Test the in operator."""
        condition = Condition(
            attribute="country",
            operator=OperatorType.IN,
            value=["US", "CA", "MX"]
        )

        # Test with value in the list
        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is True

        # Test with value not in the list
        assert evaluate_condition(condition, NON_PREMIUM_USER_CONTEXT) is False

    def test_contains_operator(self):
        """Test the contains operator for arrays and strings."""
        # Test array contains
        condition = Condition(
            attribute="tags",
            operator=OperatorType.CONTAINS,
            value="beta"
        )

        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is True

        # Test string contains
        condition = Condition(
            attribute="subscription_tier",
            operator=OperatorType.CONTAINS,
            value="premium"
        )

        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is True

        # Test not contains
        condition = Condition(
            attribute="tags",
            operator=OperatorType.CONTAINS,
            value="non-existent"
        )

        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is False

    def test_greater_than_operator(self):
        """Test the greater than operator."""
        condition = Condition(
            attribute="age",
            operator=OperatorType.GREATER_THAN,
            value=25
        )

        # Test with greater value
        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is True

        # Test with equal value
        assert evaluate_condition(condition, NON_PREMIUM_USER_CONTEXT) is False

    def test_date_operators(self):
        """Test date comparison operators."""
        now = datetime.now()
        yesterday = (now - timedelta(days=1)).isoformat()
        tomorrow = (now + timedelta(days=1)).isoformat()
        two_months_ago = (now - timedelta(days=60)).isoformat()

        # Test before
        condition = Condition(
            attribute="signup_date",
            operator=OperatorType.BEFORE,
            value=tomorrow
        )

        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is True

        # Test after
        condition = Condition(
            attribute="signup_date",
            operator=OperatorType.AFTER,
            value=yesterday
        )

        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is True

        # Test between
        condition = Condition(
            attribute="signup_date",
            operator=OperatorType.BETWEEN,
            value=two_months_ago,
            additional_value=tomorrow
        )

        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is True

    def test_array_operators(self):
        """Test array operators."""
        # Test contains_all
        condition = Condition(
            attribute="permissions",
            operator=OperatorType.CONTAINS_ALL,
            value=["read", "write"]
        )

        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is True

        # Test contains_any
        condition = Condition(
            attribute="permissions",
            operator=OperatorType.CONTAINS_ANY,
            value=["admin", "superuser"]
        )

        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is True

        # Test non-match
        condition = Condition(
            attribute="permissions",
            operator=OperatorType.CONTAINS_ALL,
            value=["read", "write", "delete"]
        )

        assert evaluate_condition(condition, PREMIUM_USER_CONTEXT) is False

class TestRuleGroupEvaluation:
    """Tests for rule group evaluation with different logical operators."""

    def test_and_operator(self):
        """Test AND logical operator."""
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    attribute="country",
                    operator=OperatorType.EQUALS,
                    value="US"
                ),
                Condition(
                    attribute="subscription_tier",
                    operator=OperatorType.EQUALS,
                    value="premium"
                )
            ]
        )

        # Test with all conditions met
        assert evaluate_rule_group(rule_group, PREMIUM_USER_CONTEXT) is True

        # Test with one condition not met
        assert evaluate_rule_group(rule_group, NON_PREMIUM_USER_CONTEXT) is False

    def test_or_operator(self):
        """Test OR logical operator."""
        rule_group = RuleGroup(
            operator=LogicalOperator.OR,
            conditions=[
                Condition(
                    attribute="country",
                    operator=OperatorType.EQUALS,
                    value="US"
                ),
                Condition(
                    attribute="subscription_tier",
                    operator=OperatorType.EQUALS,
                    value="basic"
                )
            ]
        )

        # Test with one condition met
        assert evaluate_rule_group(rule_group, PREMIUM_USER_CONTEXT) is True

        # Test with different condition met
        assert evaluate_rule_group(rule_group, NON_PREMIUM_USER_CONTEXT) is True

        # Test with no conditions met
        different_context = {
            "country": "AU",
            "subscription_tier": "enterprise"
        }
        assert evaluate_rule_group(rule_group, different_context) is False

    def test_not_operator(self):
        """Test NOT logical operator."""
        rule_group = RuleGroup(
            operator=LogicalOperator.NOT,
            conditions=[
                Condition(
                    attribute="country",
                    operator=OperatorType.EQUALS,
                    value="UK"
                )
            ]
        )

        # Test with condition not met (should be true after NOT)
        assert evaluate_rule_group(rule_group, PREMIUM_USER_CONTEXT) is True

        # Test with condition met (should be false after NOT)
        assert evaluate_rule_group(rule_group, NON_PREMIUM_USER_CONTEXT) is False

    def test_nested_groups(self):
        """Test nested rule groups."""
        inner_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    attribute="age",
                    operator=OperatorType.GREATER_THAN,
                    value=20
                ),
                Condition(
                    attribute="registered_user",
                    operator=OperatorType.EQUALS,
                    value=True
                )
            ]
        )

        outer_group = RuleGroup(
            operator=LogicalOperator.OR,
            conditions=[
                Condition(
                    attribute="subscription_tier",
                    operator=OperatorType.EQUALS,
                    value="premium"
                )
            ],
            groups=[inner_group]
        )

        # Test with premium user
        assert evaluate_rule_group(outer_group, PREMIUM_USER_CONTEXT) is True

        # Test with non-premium user that matches inner group
        assert evaluate_rule_group(outer_group, NON_PREMIUM_USER_CONTEXT) is True

        # Test with no matches
        different_context = {
            "subscription_tier": "free",
            "age": 18,
            "registered_user": True
        }
        assert evaluate_rule_group(outer_group, different_context) is False

class TestCompleteTargetingRules:
    """Tests for complete targeting rules evaluation."""

    def test_basic_targeting_rules(self):
        """Test simple targeting rules with default."""
        targeting_rules = TargetingRules(
            version="1.0",
            rules=[
                TargetingRule(
                    id="premium_users",
                    name="Premium Users",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(
                                attribute="subscription_tier",
                                operator=OperatorType.EQUALS,
                                value="premium"
                            )
                        ]
                    ),
                    rollout_percentage=100,
                    priority=10
                ),
                TargetingRule(
                    id="basic_us_users",
                    name="Basic US Users",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(
                                attribute="subscription_tier",
                                operator=OperatorType.EQUALS,
                                value="basic"
                            ),
                            Condition(
                                attribute="country",
                                operator=OperatorType.EQUALS,
                                value="US"
                            )
                        ]
                    ),
                    rollout_percentage=50,  # 50% rollout for this rule
                    priority=20
                )
            ],
            default_rule=None
        )

        # Test premium user - should match first rule
        result = evaluate_targeting_rules(targeting_rules, PREMIUM_USER_CONTEXT)

        assert result is not None
        assert result.id == "premium_users"

        # Test basic US user - should depend on rollout percentage
        basic_us_context = {
            "user_id": "user_that_should_be_in_rollout",
            "subscription_tier": "basic",
            "country": "US",
            "registered_user": True
        }

        result = evaluate_targeting_rules(targeting_rules, basic_us_context)

        # This will depend on the hash, so hard to assert exactly
        # Just check that a result is returned
        assert result is not None

        # Test unmatched user with default rule
        result = evaluate_targeting_rules(targeting_rules, {"registered_user": False})

        assert result is None

    def test_rule_priority_ordering(self):
        """Test that rules are evaluated in priority order."""
        targeting_rules = TargetingRules(
            version="1.0",
            rules=[
                TargetingRule(
                    id="low_priority",
                    name="Low Priority Rule",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(
                                attribute="registered_user",
                                operator=OperatorType.EQUALS,
                                value=True
                            )
                        ]
                    ),
                    rollout_percentage=100,
                    priority=100
                ),
                TargetingRule(
                    id="high_priority",
                    name="High Priority Rule",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(
                                attribute="registered_user",
                                operator=OperatorType.EQUALS,
                                value=True
                            )
                        ]
                    ),
                    rollout_percentage=100,
                    priority=1
                )
            ],
            default_rule=None
        )

        # Both rules would match, but high_priority should be chosen
        context = {"user_id": USER_ID, "registered_user": True}
        result = evaluate_targeting_rules(targeting_rules, context)

        assert result is not None
        assert result.id == "high_priority"

class TestBackwardCompatibility:
    """Tests for backward compatibility with legacy rule formats."""

    def test_legacy_user_id_targeting(self):
        """Test backward compatibility with legacy user ID targeting."""
        # Create a context with user_id
        context = {"user_id": USER_ID}

        # Create targeting rules
        legacy_rules = TargetingRules(
            version="1.0",
            rules=[
                TargetingRule(
                    id=USER_ID,
                    name="User ID Match",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(
                                attribute="user_id",
                                operator=OperatorType.EQUALS,
                                value=USER_ID
                            )
                        ]
                    ),
                    rollout_percentage=100,
                    priority=1
                )
            ],
            default_rule=None
        )

        # Test with matching user ID
        result = evaluate_targeting_rules(legacy_rules, context)

        assert result is not None
        assert result.id == USER_ID

        # Test with non-matching user ID
        non_matching_context = {"user_id": "non-matching-user"}
        result = evaluate_targeting_rules(legacy_rules, non_matching_context)

        assert result is None

    def test_legacy_attribute_targeting(self):
        """Test backward compatibility with legacy attribute targeting."""
        legacy_rules = TargetingRules(
            version="1.0",
            rules=[
                TargetingRule(
                    id="premium_users",
                    name="Premium Users",
                    rule=RuleGroup(
                        operator=LogicalOperator.AND,
                        conditions=[
                            Condition(
                                attribute="subscription_tier",
                                operator=OperatorType.EQUALS,
                                value="premium"
                            )
                        ]
                    ),
                    rollout_percentage=100,
                    priority=1
                )
            ],
            default_rule=None
        )

        # Test with matching attributes
        result = evaluate_targeting_rules(legacy_rules, PREMIUM_USER_CONTEXT)

        assert result is not None
        assert result.id == "premium_users"

        # Test with non-matching attributes
        result = evaluate_targeting_rules(legacy_rules, NON_PREMIUM_USER_CONTEXT)

        assert result is None

class TestRulesEngine:
    """Tests for the rules engine implementation."""

    def test_simple_condition_evaluation(self):
        """Test evaluation of simple conditions."""
        user_context = {"age": 25, "country": "US", "plan": "premium"}

        # Test EQUALS
        condition = Condition(attribute="age", operator=OperatorType.EQUALS, value=25)
        assert evaluate_condition(condition, user_context) is True

        # Test NOT_EQUALS
        condition = Condition(attribute="age", operator=OperatorType.NOT_EQUALS, value=30)
        assert evaluate_condition(condition, user_context) is True

        # Test GREATER_THAN
        condition = Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=20)
        assert evaluate_condition(condition, user_context) is True

        # Test LESS_THAN
        condition = Condition(attribute="age", operator=OperatorType.LESS_THAN, value=30)
        assert evaluate_condition(condition, user_context) is True

        # Test IN
        condition = Condition(attribute="country", operator=OperatorType.IN, value=["US", "CA", "UK"])
        assert evaluate_condition(condition, user_context) is True

        # Test NOT_IN
        condition = Condition(attribute="country", operator=OperatorType.NOT_IN, value=["CA", "UK"])
        assert evaluate_condition(condition, user_context) is True

        # Test attribute not found
        condition = Condition(attribute="missing", operator=OperatorType.EQUALS, value="something")
        assert evaluate_condition(condition, user_context) is False

    def test_string_operator_evaluation(self):
        """Test evaluation of string operators."""
        user_context = {"email": "user@example.com", "description": "Premium user from New York"}

        # Test CONTAINS
        condition = Condition(attribute="email", operator=OperatorType.CONTAINS, value="example")
        assert evaluate_condition(condition, user_context) is True

        # Test NOT_CONTAINS
        condition = Condition(attribute="email", operator=OperatorType.NOT_CONTAINS, value="gmail")
        assert evaluate_condition(condition, user_context) is True

        # Test STARTS_WITH
        condition = Condition(attribute="email", operator=OperatorType.STARTS_WITH, value="user")
        assert evaluate_condition(condition, user_context) is True

        # Test ENDS_WITH
        condition = Condition(attribute="email", operator=OperatorType.ENDS_WITH, value=".com")
        assert evaluate_condition(condition, user_context) is True

        # Test MATCH_REGEX
        condition = Condition(attribute="email", operator=OperatorType.MATCH_REGEX, value=r"^user@.*\.com$")
        assert evaluate_condition(condition, user_context) is True

    def test_date_operator_evaluation(self):
        """Test evaluation of date operators."""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        user_context = {
            "created_at": now.isoformat(),
            "last_login": yesterday.timestamp(),
            "subscription_expiry": tomorrow,
        }

        # Test BEFORE
        condition = Condition(attribute="last_login", operator=OperatorType.BEFORE, value=now.timestamp())
        assert evaluate_condition(condition, user_context) is True

        # Test AFTER
        condition = Condition(attribute="subscription_expiry", operator=OperatorType.AFTER, value=now)
        assert evaluate_condition(condition, user_context) is True

        # Test BETWEEN with dates
        condition = Condition(
            attribute="created_at",
            operator=OperatorType.BETWEEN,
            value=yesterday.isoformat(),
            additional_value=tomorrow.isoformat(),
        )
        assert evaluate_condition(condition, user_context) is True

    def test_rule_group_evaluation(self):
        """Test evaluation of rule groups with different logical operators."""
        user_context = {"age": 25, "country": "US", "plan": "premium"}

        # Test AND operator
        rule_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=20),
                Condition(attribute="country", operator=OperatorType.EQUALS, value="US"),
            ],
        )
        assert evaluate_rule_group(rule_group, user_context) is True

        # Test OR operator
        rule_group = RuleGroup(
            operator=LogicalOperator.OR,
            conditions=[
                Condition(attribute="age", operator=OperatorType.EQUALS, value=30),  # False
                Condition(attribute="plan", operator=OperatorType.EQUALS, value="premium"),  # True
            ],
        )
        assert evaluate_rule_group(rule_group, user_context) is True

        # Test NOT operator
        rule_group = RuleGroup(
            operator=LogicalOperator.NOT,
            conditions=[
                Condition(attribute="country", operator=OperatorType.EQUALS, value="CA"),
            ],
        )
        assert evaluate_rule_group(rule_group, user_context) is True

        # Test nested groups
        nested_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="age", operator=OperatorType.GREATER_THAN, value=20),
                Condition(attribute="age", operator=OperatorType.LESS_THAN, value=30),
            ],
        )

        parent_group = RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(attribute="country", operator=OperatorType.EQUALS, value="US"),
            ],
            groups=[nested_group],
        )

        assert evaluate_rule_group(parent_group, user_context) is True

    def test_targeting_rule_evaluation(self):
        """Test evaluation of complete targeting rules."""
        user_context = {"age": 25, "country": "US", "plan": "premium"}

        # Create a targeting rule
        rule = TargetingRule(
            id="rule1",
            name="US Premium Users",
            description="Users from the US with a premium plan",
            priority=1,
            rollout_percentage=100,
            rule=RuleGroup(
                operator=LogicalOperator.AND,
                conditions=[
                    Condition(attribute="country", operator=OperatorType.EQUALS, value="US"),
                    Condition(attribute="plan", operator=OperatorType.EQUALS, value="premium"),
                ],
            ),
        )

        assert evaluate_rule(rule, user_context) is True

        # Test with a non-matching rule
        rule.rule.conditions[1].value = "basic"
        assert evaluate_rule(rule, user_context) is False

    def test_targeting_rules_evaluation(self):
        """Test evaluation of multiple targeting rules with priorities."""
        user_context = {"age": 25, "country": "US", "plan": "premium"}

        rule1 = TargetingRule(
            id="rule1",
            name="All Premium Users",
            description="All users with a premium plan",
            priority=2,  # Lower priority
            rollout_percentage=100,
            rule=RuleGroup(
                operator=LogicalOperator.AND,
                conditions=[
                    Condition(attribute="plan", operator=OperatorType.EQUALS, value="premium"),
                ],
            ),
        )

        rule2 = TargetingRule(
            id="rule2",
            name="US Premium Users",
            description="US users with a premium plan",
            priority=1,  # Higher priority
            rollout_percentage=100,
            rule=RuleGroup(
                operator=LogicalOperator.AND,
                conditions=[
                    Condition(attribute="country", operator=OperatorType.EQUALS, value="US"),
                    Condition(attribute="plan", operator=OperatorType.EQUALS, value="premium"),
                ],
            ),
        )

        default_rule = TargetingRule(
            id="default",
            name="Default Rule",
            description="Default rule for all users",
            priority=999,
            rollout_percentage=100,
            rule=RuleGroup(
                operator=LogicalOperator.AND,
                conditions=[],
            ),
        )

        targeting_rules = TargetingRules(
            rules=[rule1, rule2],
            default_rule=default_rule,
        )

        # Should match the highest priority rule (rule2)
        matched_rule = evaluate_targeting_rules(targeting_rules, user_context)
        assert matched_rule.id == "rule2"

        # Change the context so it doesn't match rule2
        user_context["country"] = "CA"
        matched_rule = evaluate_targeting_rules(targeting_rules, user_context)
        assert matched_rule.id == "rule1"

        # Change the context so it doesn't match any rule
        user_context["plan"] = "basic"
        matched_rule = evaluate_targeting_rules(targeting_rules, user_context)
        assert matched_rule.id == "default"

    def test_rollout_percentage(self):
        """Test the rollout percentage functionality."""
        user_context = {"user_id": "12345", "email": "user@example.com"}

        rule = TargetingRule(
            id="rule1",
            name="Test Rule",
            description="Test rule for rollout",
            priority=1,
            rollout_percentage=0,  # 0% rollout
            rule=RuleGroup(
                operator=LogicalOperator.AND,
                conditions=[
                    Condition(attribute="email", operator=OperatorType.CONTAINS, value="example.com"),
                ],
            ),
        )

        # 0% rollout should always return False
        assert should_include_in_rollout(rule, user_context) is False

        # 100% rollout should always return True
        rule.rollout_percentage = 100
        assert should_include_in_rollout(rule, user_context) is True

        # Test with a specific percentage
        rule.rollout_percentage = 50
        # The result is deterministic based on the hash, so we can't assert
        # a specific value, but we can ensure consistency
        result1 = should_include_in_rollout(rule, user_context)
        result2 = should_include_in_rollout(rule, user_context)
        assert result1 == result2  # Should be deterministic

        # Different users should get different results potentially
        user_context2 = {"user_id": "67890", "email": "other@example.com"}
        # Again, can't assert specific value but can test the function runs
        should_include_in_rollout(rule, user_context2)

    def test_get_stable_user_id(self):
        """Test the extraction of stable user IDs from context."""
        # Test with user_id
        context = {"user_id": "12345", "email": "user@example.com"}
        assert get_stable_user_id(context) == "12345"

        # Test with email when user_id is missing
        context = {"email": "user@example.com"}
        assert get_stable_user_id(context) == "user@example.com"

        # Test with empty context
        context = {}
        # Should return a hash of sorted items (empty string in this case)
        assert len(get_stable_user_id(context)) > 0  # Should return a hash, not empty string

    def test_array_operators(self):
        """Test the array operators."""
        user_context = {
            "tags": ["premium", "beta", "early-adopter"],
            "permissions": ["read", "write"],
        }

        # Test CONTAINS_ALL
        condition = Condition(
            attribute="tags",
            operator=OperatorType.CONTAINS_ALL,
            value=["premium", "beta"],
        )
        assert evaluate_condition(condition, user_context) is True

        # Test CONTAINS_ANY
        condition = Condition(
            attribute="permissions",
            operator=OperatorType.CONTAINS_ANY,
            value=["admin", "write"],
        )
        assert evaluate_condition(condition, user_context) is True

        # Test CONTAINS_ALL with non-matching
        condition = Condition(
            attribute="tags",
            operator=OperatorType.CONTAINS_ALL,
            value=["premium", "admin"],
        )
        assert evaluate_condition(condition, user_context) is False

        # Test CONTAINS_ANY with non-matching
        condition = Condition(
            attribute="permissions",
            operator=OperatorType.CONTAINS_ANY,
            value=["admin", "delete"],
        )
        assert evaluate_condition(condition, user_context) is False
