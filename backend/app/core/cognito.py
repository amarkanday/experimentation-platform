"""
Cognito group to role mapping utility functions.

This module provides utility functions to map Cognito groups to user roles
in the experimentation platform.
"""

import logging
from typing import List, Optional

from backend.app.models.user import UserRole
from backend.app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


def map_cognito_groups_to_role(groups: List[str]) -> UserRole:
    """
    Map Cognito groups to a UserRole enum value.
    If user belongs to multiple groups, the highest privilege role wins.

    Args:
        groups: List of Cognito group names

    Returns:
        UserRole: The highest privilege role from the user's groups
    """
    # Define role hierarchy (highest privilege first)
    role_hierarchy = [UserRole.ADMIN, UserRole.DEVELOPER, UserRole.ANALYST, UserRole.VIEWER]

    # Get group-to-role mapping from settings
    group_role_mapping = {
        group: UserRole(role)
        for group, role in settings.COGNITO_GROUP_ROLE_MAPPING.items()
    }

    # Log all mapped groups for debugging
    logger.debug(f"Mapping Cognito groups {groups} to roles using mapping: {group_role_mapping}")

    # Find all matching roles based on groups
    matching_roles = []
    for group in groups:
        if group in group_role_mapping:
            matching_roles.append(group_role_mapping[group])
            logger.debug(f"Matched group {group} to role {group_role_mapping[group]}")

    # If user is in admin groups, automatically assign ADMIN role
    if should_be_superuser(groups):
        logger.debug(f"User is in admin groups {settings.COGNITO_ADMIN_GROUPS}, assigning ADMIN role")
        return UserRole.ADMIN

    # Return highest privilege role if any matches found
    for role in role_hierarchy:
        if role in matching_roles:
            logger.debug(f"Selected highest privilege role: {role}")
            return role

    # Default to VIEWER if no matches
    logger.debug("No matching roles found, defaulting to VIEWER")
    return UserRole.VIEWER


def should_be_superuser(groups: List[str]) -> bool:
    """
    Determine if user should be a superuser based on group membership.

    Args:
        groups: List of Cognito group names

    Returns:
        bool: True if the user is in any admin groups, False otherwise
    """
    is_superuser = any(group in settings.COGNITO_ADMIN_GROUPS for group in groups)

    if is_superuser:
        admin_groups = [group for group in groups if group in settings.COGNITO_ADMIN_GROUPS]
        logger.debug(f"User is in admin groups: {admin_groups}")

    return is_superuser
