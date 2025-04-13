"""
Tests for Cognito integration.

This module tests the functionality of mapping Cognito groups to user roles.
"""

import pytest
from unittest.mock import patch, MagicMock

from backend.app.core.cognito import map_cognito_groups_to_role, should_be_superuser
from backend.app.models.user import UserRole


def test_map_cognito_groups_to_role_admin():
    """Test mapping Admin group to ADMIN role."""
    with patch("backend.app.core.cognito.settings") as mock_settings:
        mock_settings.COGNITO_GROUP_ROLE_MAPPING = {"Admins": "admin", "Developers": "developer"}
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins"]

        # Test with admin group
        role = map_cognito_groups_to_role(["Admins"])
        assert role == UserRole.ADMIN


def test_map_cognito_groups_to_role_developer():
    """Test mapping Developer group to DEVELOPER role."""
    with patch("backend.app.core.cognito.settings") as mock_settings:
        mock_settings.COGNITO_GROUP_ROLE_MAPPING = {"Admins": "admin", "Developers": "developer"}
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins"]

        # Test with developer group
        role = map_cognito_groups_to_role(["Developers"])
        assert role == UserRole.DEVELOPER


def test_map_cognito_groups_to_role_multiple_groups():
    """Test mapping multiple groups to highest privilege role."""
    with patch("backend.app.core.cognito.settings") as mock_settings:
        mock_settings.COGNITO_GROUP_ROLE_MAPPING = {
            "Admins": "admin",
            "Developers": "developer",
            "Analysts": "analyst",
            "Viewers": "viewer"
        }
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins"]

        # Test with multiple groups - should get highest privilege (Developers)
        role = map_cognito_groups_to_role(["Viewers", "Analysts", "Developers"])
        assert role == UserRole.DEVELOPER


def test_map_cognito_groups_to_role_default_to_viewer():
    """Test default to VIEWER role if no matching groups."""
    with patch("backend.app.core.cognito.settings") as mock_settings:
        mock_settings.COGNITO_GROUP_ROLE_MAPPING = {"Admins": "admin", "Developers": "developer"}
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins"]

        # Test with no matching groups
        role = map_cognito_groups_to_role(["SomeOtherGroup"])
        assert role == UserRole.VIEWER


def test_map_cognito_groups_to_role_admin_groups_override():
    """Test that admin groups always map to ADMIN role."""
    with patch("backend.app.core.cognito.settings") as mock_settings:
        mock_settings.COGNITO_GROUP_ROLE_MAPPING = {
            "Admins": "admin",
            "SuperUsers": "developer",  # Even though mapped as developer
            "Developers": "developer"
        }
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins", "SuperUsers"]

        # SuperUsers is in admin groups, should get ADMIN role despite mapping
        role = map_cognito_groups_to_role(["SuperUsers"])
        assert role == UserRole.ADMIN


def test_should_be_superuser_true():
    """Test detecting superuser from admin groups."""
    with patch("backend.app.core.cognito.settings") as mock_settings:
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins", "SuperUsers"]

        # User in admin group
        assert should_be_superuser(["SuperUsers"]) is True


def test_should_be_superuser_false():
    """Test detecting non-superuser."""
    with patch("backend.app.core.cognito.settings") as mock_settings:
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins", "SuperUsers"]

        # User not in admin groups
        assert should_be_superuser(["Developers", "Analysts"]) is False


def test_should_be_superuser_multiple_groups():
    """Test detecting superuser from multiple groups."""
    with patch("backend.app.core.cognito.settings") as mock_settings:
        mock_settings.COGNITO_ADMIN_GROUPS = ["Admins", "SuperUsers"]

        # One of the groups is admin
        assert should_be_superuser(["Developers", "Analysts", "SuperUsers"]) is True
