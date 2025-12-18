"""
Test cases for array_length operator in rules engine.

Tests array length comparison functionality for targeting rules.
"""

import pytest
from backend.app.core.rules_engine import apply_operator
from backend.app.schemas.targeting_rule import OperatorType


class TestArrayLengthEquals:
    """Test array length equality operator."""

    def test_length_equals_exact(self):
        """Test that array length equals exact number."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            3,
            additional_value="eq"
        )
        assert result is True

    def test_length_equals_zero(self):
        """Test that empty array has length zero."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [],
            0,
            additional_value="eq"
        )
        assert result is True

    def test_length_not_equals(self):
        """Test that array length does not equal wrong number."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            5,
            additional_value="eq"
        )
        assert result is False

    def test_length_equals_string_array(self):
        """Test array length with string elements."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            ["a", "b", "c", "d"],
            4,
            additional_value="eq"
        )
        assert result is True

    def test_length_equals_mixed_array(self):
        """Test array length with mixed type elements."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, "two", 3.0, None, True],
            5,
            additional_value="eq"
        )
        assert result is True


class TestArrayLengthGreaterThan:
    """Test array length greater than operator."""

    def test_length_greater_than(self):
        """Test that array length is greater than threshold."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3, 4],
            3,
            additional_value="gt"
        )
        assert result is True

    def test_length_not_greater_when_equal(self):
        """Test that equal length is not greater."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            3,
            additional_value="gt"
        )
        assert result is False

    def test_length_not_greater_when_less(self):
        """Test that smaller length is not greater."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2],
            3,
            additional_value="gt"
        )
        assert result is False

    def test_length_greater_than_zero(self):
        """Test that non-empty array has length greater than zero."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1],
            0,
            additional_value="gt"
        )
        assert result is True


class TestArrayLengthLessThan:
    """Test array length less than operator."""

    def test_length_less_than(self):
        """Test that array length is less than threshold."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2],
            3,
            additional_value="lt"
        )
        assert result is True

    def test_length_not_less_when_equal(self):
        """Test that equal length is not less."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            3,
            additional_value="lt"
        )
        assert result is False

    def test_length_not_less_when_greater(self):
        """Test that larger length is not less."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3, 4],
            3,
            additional_value="lt"
        )
        assert result is False

    def test_empty_array_less_than_one(self):
        """Test that empty array has length less than one."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [],
            1,
            additional_value="lt"
        )
        assert result is True


class TestArrayLengthGreaterThanOrEqual:
    """Test array length greater than or equal operator."""

    def test_length_gte_when_greater(self):
        """Test GTE when array length is greater."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3, 4],
            3,
            additional_value="gte"
        )
        assert result is True

    def test_length_gte_when_equal(self):
        """Test GTE when array length is equal."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            3,
            additional_value="gte"
        )
        assert result is True

    def test_length_gte_when_less(self):
        """Test GTE when array length is less."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2],
            3,
            additional_value="gte"
        )
        assert result is False


class TestArrayLengthLessThanOrEqual:
    """Test array length less than or equal operator."""

    def test_length_lte_when_less(self):
        """Test LTE when array length is less."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2],
            3,
            additional_value="lte"
        )
        assert result is True

    def test_length_lte_when_equal(self):
        """Test LTE when array length is equal."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            3,
            additional_value="lte"
        )
        assert result is True

    def test_length_lte_when_greater(self):
        """Test LTE when array length is greater."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3, 4],
            3,
            additional_value="lte"
        )
        assert result is False


class TestArrayLengthBetween:
    """Test array length between range operator."""

    def test_length_between_inclusive(self):
        """Test that array length is within range (inclusive)."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            2,  # minimum
            additional_value=5  # maximum (this becomes the range check)
        )
        # For between, we need to handle it differently
        # Let's use a dict for additional_value
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            {"min": 2, "max": 5},
            additional_value="between"
        )
        assert result is True

    def test_length_between_at_min(self):
        """Test that array length at minimum is included."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2],
            {"min": 2, "max": 5},
            additional_value="between"
        )
        assert result is True

    def test_length_between_at_max(self):
        """Test that array length at maximum is included."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3, 4, 5],
            {"min": 2, "max": 5},
            additional_value="between"
        )
        assert result is True

    def test_length_not_between_too_small(self):
        """Test that array length below minimum is not between."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1],
            {"min": 2, "max": 5},
            additional_value="between"
        )
        assert result is False

    def test_length_not_between_too_large(self):
        """Test that array length above maximum is not between."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3, 4, 5, 6],
            {"min": 2, "max": 5},
            additional_value="between"
        )
        assert result is False


class TestArrayLengthInvalidInputs:
    """Test array length operator with invalid inputs."""

    def test_non_array_value_none(self):
        """Test handling of None value."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            None,
            3,
            additional_value="eq"
        )
        assert result is False

    def test_non_array_value_string(self):
        """Test that string is treated as array-like (has length)."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            "hello",
            5,
            additional_value="eq"
        )
        # Strings have length, so this should work
        assert result is True

    def test_non_array_value_number(self):
        """Test handling of number value (no length)."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            42,
            1,
            additional_value="eq"
        )
        # Numbers don't have length
        assert result is False

    def test_non_array_value_dict(self):
        """Test handling of dict value (has length)."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            {"a": 1, "b": 2, "c": 3},
            3,
            additional_value="eq"
        )
        # Dicts have length (number of keys)
        assert result is True

    def test_tuple_as_array(self):
        """Test that tuples are handled as arrays."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            (1, 2, 3, 4),
            4,
            additional_value="eq"
        )
        assert result is True

    def test_set_as_array(self):
        """Test that sets are handled as arrays."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            {1, 2, 3},
            3,
            additional_value="eq"
        )
        assert result is True

    def test_invalid_comparison_type(self):
        """Test handling of invalid comparison type."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            3,
            additional_value="invalid"
        )
        assert result is False

    def test_negative_expected_length(self):
        """Test handling of negative expected length."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            -1,
            additional_value="eq"
        )
        # Length can never be negative
        assert result is False

    def test_expected_value_not_number(self):
        """Test handling of non-numeric expected value."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            "three",
            additional_value="eq"
        )
        assert result is False


class TestArrayLengthEdgeCases:
    """Test edge cases for array length operator."""

    def test_very_large_array(self):
        """Test with very large array."""
        large_array = list(range(10000))
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            large_array,
            10000,
            additional_value="eq"
        )
        assert result is True

    def test_nested_arrays(self):
        """Test that nested arrays count as single elements."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [[1, 2], [3, 4], [5, 6]],
            3,  # 3 elements, each happens to be an array
            additional_value="eq"
        )
        assert result is True

    def test_array_with_none_elements(self):
        """Test array containing None elements."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, None, 3, None, 5],
            5,
            additional_value="eq"
        )
        assert result is True

    def test_default_comparison_without_additional_value(self):
        """Test that without additional_value, defaults to equality."""
        result = apply_operator(
            OperatorType.ARRAY_LENGTH,
            [1, 2, 3],
            3
        )
        # Should default to "eq" if no additional_value provided
        assert result is True
