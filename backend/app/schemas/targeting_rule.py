"""
Targeting rule schema models for validation and serialization.

This module defines Pydantic models for targeting rule-related data structures.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions."""
    AND = "and"
    OR = "or"
    NOT = "not"


class OperatorType(str, Enum):
    """Operators for condition evaluation."""
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    BEFORE = "before"  # Date comparison
    AFTER = "after"  # Date comparison
    BETWEEN = "between"  # Date or number range
    CONTAINS_ALL = "contains_all"  # Array contains all elements
    CONTAINS_ANY = "contains_any"  # Array contains any element
    MATCH_REGEX = "match_regex"  # String matches regex pattern

    # Advanced string operators
    LOWERCASE_EQUALS = "lowercase_eq"  # Case-insensitive equality
    UPPERCASE_EQUALS = "uppercase_eq"  # Uppercase equality
    FORMAT_MATCHES = "format_matches"  # Match a specific format (like email, phone)

    # Advanced date operators
    IS_WEEKDAY = "is_weekday"  # Check if a date is a weekday (Mon-Fri)
    IS_WEEKEND = "is_weekend"  # Check if a date is a weekend (Sat-Sun)
    IS_BUSINESS_HOURS = "is_business_hours"  # Check if time is within business hours
    DAYS_SINCE = "days_since"  # Days elapsed since a reference date
    MONTHS_SINCE = "months_since"  # Months elapsed since a reference date

    # Geolocation operators
    WITHIN_RADIUS = "within_radius"  # Check if point is within radius of another point
    IN_COUNTRY = "in_country"  # Check if coordinates are in a country
    IN_TIMEZONE = "in_timezone"  # Check if coordinates are in a timezone

    # Path-based operators
    PATH_EXISTS = "path_exists"  # Check if a path exists in the context
    PATH_EQUALS = "path_eq"  # Check if a nested path equals a value
    PATH_CONTAINS = "path_contains"  # Check if a nested path contains a value

    # Behavioral operators
    FREQUENCY_EXCEEDS = "frequency_exceeds"  # Action performed more than X times
    RECENCY_WITHIN = "recency_within"  # Action performed within recent time period


class Condition(BaseModel):
    """A single condition to evaluate against a user attribute."""
    attribute: str = Field(..., description="User attribute to evaluate")
    operator: OperatorType = Field(..., description="Operator to apply")
    value: Any = Field(..., description="Value to compare against")
    additional_value: Optional[Any] = Field(None, description="Additional value for operators that need two values (e.g., between)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "attribute": "country",
                "operator": "in",
                "value": ["US", "CA"]
            }
        }
    )


class RuleGroup(BaseModel):
    """A group of conditions combined with a logical operator."""
    operator: LogicalOperator = Field(LogicalOperator.AND, description="Logical operator to combine conditions")
    conditions: List[Condition] = Field(default_factory=list, description="List of conditions in this group")
    groups: Optional[List["RuleGroup"]] = Field(default_factory=list, description="Nested rule groups for complex rules")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operator": "and",
                "conditions": [
                    {
                        "attribute": "country",
                        "operator": "in",
                        "value": ["US", "CA"]
                    },
                    {
                        "attribute": "subscription_tier",
                        "operator": "eq",
                        "value": "premium"
                    }
                ]
            }
        }
    )


# Support for recursive definitions
RuleGroup.model_rebuild()


class TargetingRule(BaseModel):
    """A targeting rule with conditions and rollout configuration."""
    id: str = Field(..., description="Unique identifier for the rule")
    name: Optional[str] = Field(None, description="Human-readable name for the rule")
    description: Optional[str] = Field(None, description="Description of the rule's purpose")
    rule: RuleGroup = Field(..., description="Rule conditions")
    rollout_percentage: int = Field(100, ge=0, le=100, description="Percentage of users who match conditions to include")
    priority: int = Field(0, description="Priority of the rule (lower number = higher priority)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "premium_us_users",
                "name": "Premium US Users",
                "description": "Users with premium subscription in the US",
                "rule": {
                    "operator": "and",
                    "conditions": [
                        {
                            "attribute": "country",
                            "operator": "eq",
                            "value": "US"
                        },
                        {
                            "attribute": "subscription_tier",
                            "operator": "eq",
                            "value": "premium"
                        }
                    ]
                },
                "rollout_percentage": 100,
                "priority": 1
            }
        }
    )


class TargetingRules(BaseModel):
    """Complete targeting rules configuration."""
    version: str = Field("1.0", description="Schema version")
    rules: List[TargetingRule] = Field(default_factory=list, description="List of targeting rules")
    default_rule: Optional[TargetingRule] = Field(None, description="Default rule if no others match")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "1.0",
                "rules": [
                    {
                        "id": "premium_us_users",
                        "name": "Premium US Users",
                        "description": "Users with premium subscription in the US",
                        "rule": {
                            "operator": "and",
                            "conditions": [
                                {
                                    "attribute": "country",
                                    "operator": "eq",
                                    "value": "US"
                                },
                                {
                                    "attribute": "subscription_tier",
                                    "operator": "eq",
                                    "value": "premium"
                                }
                            ]
                        },
                        "rollout_percentage": 100,
                        "priority": 1
                    }
                ],
                "default_rule": {
                    "id": "default",
                    "rule": {
                        "operator": "and",
                        "conditions": [
                            {
                                "attribute": "registered_user",
                                "operator": "eq",
                                "value": True
                            }
                        ]
                    },
                    "rollout_percentage": 10,
                    "priority": 999
                }
            }
        }
    )
