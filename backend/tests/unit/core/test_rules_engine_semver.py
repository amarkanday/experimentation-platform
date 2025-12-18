"""
Test cases for semantic version operator in rules engine.

Tests semantic version comparison functionality following SemVer 2.0.0 specification.
"""

import pytest
from backend.app.core.rules_engine import apply_operator
from backend.app.schemas.targeting_rule import OperatorType


class TestSemanticVersionEquals:
    """Test semantic version equality operator."""

    def test_equal_versions(self):
        """Test that identical semantic versions are equal."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2.3",
            "1.2.3"
        )
        assert result is True

    def test_not_equal_versions(self):
        """Test that different semantic versions are not equal."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2.3",
            "1.2.4"
        )
        assert result is False

    def test_equal_with_prerelease(self):
        """Test equality with pre-release versions."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0-alpha",
            "1.0.0-alpha"
        )
        assert result is True

    def test_not_equal_different_prerelease(self):
        """Test inequality with different pre-release versions."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0-alpha",
            "1.0.0-beta"
        )
        assert result is False

    def test_equal_with_build_metadata(self):
        """Test equality with build metadata (should be ignored per SemVer spec)."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0+build.123",
            "1.0.0+build.456"
        )
        assert result is True


class TestSemanticVersionGreaterThan:
    """Test semantic version greater than operator."""

    def test_major_version_greater(self):
        """Test that higher major version is greater."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "2.0.0",
            "1.9.9",
            additional_value="gt"  # operation type
        )
        assert result is True

    def test_minor_version_greater(self):
        """Test that higher minor version is greater (lexicographic issue test)."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.10.0",
            "1.9.0",
            additional_value="gt"
        )
        assert result is True

    def test_patch_version_greater(self):
        """Test that higher patch version is greater."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2.4",
            "1.2.3",
            additional_value="gt"
        )
        assert result is True

    def test_not_greater_when_less(self):
        """Test that lower version is not greater."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2.3",
            "2.0.0",
            additional_value="gt"
        )
        assert result is False

    def test_not_greater_when_equal(self):
        """Test that equal versions are not greater."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2.3",
            "1.2.3",
            additional_value="gt"
        )
        assert result is False

    def test_prerelease_less_than_release(self):
        """Test that pre-release version is less than release version."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0",
            "1.0.0-alpha",
            additional_value="gt"
        )
        assert result is True

    def test_prerelease_ordering(self):
        """Test ordering of pre-release versions."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0-beta.2",
            "1.0.0-beta.1",
            additional_value="gt"
        )
        assert result is True


class TestSemanticVersionLessThan:
    """Test semantic version less than operator."""

    def test_major_version_less(self):
        """Test that lower major version is less."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2.3",
            "2.0.0",
            additional_value="lt"
        )
        assert result is True

    def test_minor_version_less(self):
        """Test that lower minor version is less."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2.0",
            "1.3.0",
            additional_value="lt"
        )
        assert result is True

    def test_patch_version_less(self):
        """Test that lower patch version is less."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2.3",
            "1.2.4",
            additional_value="lt"
        )
        assert result is True

    def test_not_less_when_greater(self):
        """Test that greater version is not less."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "2.0.0",
            "1.2.3",
            additional_value="lt"
        )
        assert result is False

    def test_not_less_when_equal(self):
        """Test that equal versions are not less."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2.3",
            "1.2.3",
            additional_value="lt"
        )
        assert result is False

    def test_prerelease_less_than_release(self):
        """Test that pre-release version is less than release version."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0-rc.1",
            "1.0.0",
            additional_value="lt"
        )
        assert result is True


class TestSemanticVersionInvalidFormat:
    """Test semantic version validation and error handling."""

    def test_invalid_format_two_parts(self):
        """Test that version with only two parts is invalid."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2",
            "1.2.3"
        )
        # Should return False for invalid format (not raise exception)
        assert result is False

    def test_invalid_format_with_v_prefix(self):
        """Test that version with 'v' prefix is handled leniently (stripped)."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "v1.2.3",
            "1.2.3"
        )
        # We're lenient and strip 'v' prefix for better UX (common in Git tags, etc.)
        assert result is True

    def test_invalid_format_non_numeric(self):
        """Test that version with non-numeric parts is invalid."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.x.3",
            "1.2.3"
        )
        assert result is False

    def test_invalid_format_none_value(self):
        """Test handling of None value."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            None,
            "1.2.3"
        )
        assert result is False

    def test_invalid_format_empty_string(self):
        """Test handling of empty string."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "",
            "1.2.3"
        )
        assert result is False


class TestSemanticVersionGreaterThanOrEqual:
    """Test semantic version greater than or equal operator."""

    def test_greater_than_or_equal_when_greater(self):
        """Test GTE when version is greater."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "2.0.0",
            "1.0.0",
            additional_value="gte"
        )
        assert result is True

    def test_greater_than_or_equal_when_equal(self):
        """Test GTE when versions are equal."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2.3",
            "1.2.3",
            additional_value="gte"
        )
        assert result is True

    def test_greater_than_or_equal_when_less(self):
        """Test GTE when version is less."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0",
            "2.0.0",
            additional_value="gte"
        )
        assert result is False


class TestSemanticVersionLessThanOrEqual:
    """Test semantic version less than or equal operator."""

    def test_less_than_or_equal_when_less(self):
        """Test LTE when version is less."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0",
            "2.0.0",
            additional_value="lte"
        )
        assert result is True

    def test_less_than_or_equal_when_equal(self):
        """Test LTE when versions are equal."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.2.3",
            "1.2.3",
            additional_value="lte"
        )
        assert result is True

    def test_less_than_or_equal_when_greater(self):
        """Test LTE when version is greater."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "2.0.0",
            "1.0.0",
            additional_value="lte"
        )
        assert result is False


class TestSemanticVersionComplexPrerelease:
    """Test complex pre-release version scenarios."""

    def test_alpha_less_than_beta(self):
        """Test that alpha < beta < rc < release."""
        # alpha < beta
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0-alpha",
            "1.0.0-beta",
            additional_value="lt"
        )
        assert result is True

    def test_beta_less_than_rc(self):
        """Test that beta < rc."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0-beta",
            "1.0.0-rc.1",
            additional_value="lt"
        )
        assert result is True

    def test_rc_less_than_release(self):
        """Test that rc < release."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0-rc.1",
            "1.0.0",
            additional_value="lt"
        )
        assert result is True

    def test_numeric_prerelease_identifiers(self):
        """Test numeric pre-release identifiers are compared numerically."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0-alpha.10",
            "1.0.0-alpha.2",
            additional_value="gt"
        )
        assert result is True  # 10 > 2 numerically

    def test_alphanumeric_prerelease_identifiers(self):
        """Test alphanumeric pre-release identifiers are compared lexically."""
        result = apply_operator(
            OperatorType.SEMANTIC_VERSION,
            "1.0.0-alpha.b",
            "1.0.0-alpha.a",
            additional_value="gt"
        )
        assert result is True  # 'b' > 'a' lexically
