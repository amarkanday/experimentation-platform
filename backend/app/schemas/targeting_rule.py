"""
Targeting rule schema models for validation and serialization.

This module defines Pydantic models for targeting rule-related data structures.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


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
    # Advanced operators for custom attributes
    SEMANTIC_VERSION = "semantic_version"  # Compare semantic versions (e.g., 1.2.3)
    GEO_DISTANCE = "geo_distance"  # Distance from a geographic point
    TIME_WINDOW = "time_window"  # Within a time window (e.g., business hours)
    PERCENTAGE_BUCKET = "percentage_bucket"  # User falls within percentage bucket
    JSON_PATH = "json_path"  # Extract and compare JSON path value
    ARRAY_LENGTH = "array_length"  # Compare array length


class AttributeType(str, Enum):
    """Types of user attributes for validation."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    DATE = "date"
    JSON = "json"
    GEO_COORDINATE = "geo_coordinate"
    SEMANTIC_VERSION = "semantic_version"


class Condition(BaseModel):
    """A single condition to evaluate against a user attribute."""
    attribute: str = Field(..., description="User attribute to evaluate")
    operator: OperatorType = Field(..., description="Operator to apply")
    value: Any = Field(..., description="Value to compare against")
    additional_value: Optional[Any] = Field(None, description="Additional value for operators that need two values (e.g., between)")
    attribute_type: Optional[AttributeType] = Field(None, description="Type of the attribute for validation")
    validation_schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for validating the attribute value")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "attribute": "country",
                "operator": "in",
                "value": ["US", "CA"],
                "attribute_type": "string"
            }
        }
    )

    @field_validator('attribute')
    @classmethod
    def validate_attribute_name(cls, v):
        """Validate attribute name follows naming conventions."""
        if not v or not isinstance(v, str):
            raise ValueError("Attribute name must be a non-empty string")

        if not v.replace('_', '').replace('.', '').isalnum():
            raise ValueError("Attribute name must contain only alphanumeric characters, underscores, and dots")

        if len(v) > 100:
            raise ValueError("Attribute name must be 100 characters or less")

        return v

    @model_validator(mode='after')
    def validate_operator_value_compatibility(self):
        """Validate that operator and value are compatible."""
        operator = self.operator
        value = self.value
        additional_value = self.additional_value

        # Validate operators that require collections
        if operator in [OperatorType.IN, OperatorType.NOT_IN, OperatorType.CONTAINS_ALL, OperatorType.CONTAINS_ANY]:
            if not isinstance(value, (list, tuple, set)):
                raise ValueError(f"Operator {operator} requires a collection (list/array) as value")

        # Validate operators that require additional_value
        if operator in [OperatorType.BETWEEN, OperatorType.GEO_DISTANCE]:
            if additional_value is None:
                raise ValueError(f"Operator {operator} requires additional_value")

        # Validate geo coordinates for GEO_DISTANCE
        if operator == OperatorType.GEO_DISTANCE:
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError("GEO_DISTANCE operator requires value as [latitude, longitude]")
            try:
                lat, lon = float(value[0]), float(value[1])
                if not (-90 <= lat <= 90):
                    raise ValueError(f"Invalid latitude: {lat} (must be -90 to 90)")
                if not (-180 <= lon <= 180):
                    raise ValueError(f"Invalid longitude: {lon} (must be -180 to 180)")
            except (ValueError, TypeError):
                raise ValueError("GEO_DISTANCE coordinates must be numeric")

        # Validate semantic version format
        if operator == OperatorType.SEMANTIC_VERSION:
            import re
            semver_pattern = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
            if not isinstance(value, str) or not re.match(semver_pattern, value):
                raise ValueError("SEMANTIC_VERSION operator requires value in semantic version format (e.g., '1.2.3')")

        # Validate JSON path format
        if operator == OperatorType.JSON_PATH:
            if not isinstance(value, str) or not value.startswith('$.'):
                raise ValueError("JSON_PATH operator requires value as JSONPath string starting with '$.'")

        # Validate time window format
        if operator == OperatorType.TIME_WINDOW:
            if not isinstance(value, dict) or 'start' not in value or 'end' not in value:
                raise ValueError("TIME_WINDOW operator requires value as dict with 'start' and 'end' keys")

        return self


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
