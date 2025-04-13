from enum import Enum
from typing import List, Dict, Any, Optional, Union

from backend.app.models.user import UserRole

class ResourceType(str, Enum):
    """Types of resources that can be protected."""
    EXPERIMENT = "experiment"
    FEATURE_FLAG = "feature_flag"
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    REPORT = "report"

class Action(str, Enum):
    """Actions that can be performed on resources."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"

# Role-based access control (RBAC) permissions mapping
ROLE_PERMISSIONS: Dict[UserRole, Dict[ResourceType, List[Action]]] = {
    UserRole.ADMIN: {
        ResourceType.EXPERIMENT: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
        ResourceType.FEATURE_FLAG: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
        ResourceType.USER: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
        ResourceType.ROLE: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
        ResourceType.PERMISSION: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
        ResourceType.REPORT: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
    },
    UserRole.DEVELOPER: {
        ResourceType.EXPERIMENT: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
        ResourceType.FEATURE_FLAG: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
        ResourceType.USER: [Action.READ, Action.LIST],
        ResourceType.ROLE: [Action.READ, Action.LIST],
        ResourceType.PERMISSION: [Action.READ],
        ResourceType.REPORT: [Action.READ, Action.LIST],
    },
    UserRole.ANALYST: {
        ResourceType.EXPERIMENT: [Action.READ, Action.LIST],
        ResourceType.FEATURE_FLAG: [Action.READ, Action.LIST],
        ResourceType.USER: [Action.READ],
        ResourceType.ROLE: [Action.READ],
        ResourceType.PERMISSION: [Action.READ],
        ResourceType.REPORT: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
    },
    UserRole.VIEWER: {
        ResourceType.EXPERIMENT: [Action.READ, Action.LIST],
        ResourceType.FEATURE_FLAG: [Action.READ, Action.LIST],
        ResourceType.USER: [Action.READ],
        ResourceType.ROLE: [Action.READ],
        ResourceType.PERMISSION: [Action.READ],
        ResourceType.REPORT: [Action.READ, Action.LIST],
    },
}

def has_permission(role: UserRole, resource: ResourceType, action: Action) -> bool:
    """Check if a role has permission to perform an action on a resource."""
    if role not in ROLE_PERMISSIONS:
        return False
    if resource not in ROLE_PERMISSIONS[role]:
        return False
    return action in ROLE_PERMISSIONS[role][resource]

def check_permission(user: Any, resource: ResourceType, action: Action) -> bool:
    """
    Check if a user has permission to perform an action on a resource.

    Args:
        user: The user to check permissions for
        resource: The resource type being accessed
        action: The action being performed

    Returns:
        bool: True if the user has permission, False otherwise
    """
    # Superusers always have all permissions
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return True

    # Get user's role
    try:
        role = getattr(user, 'role', UserRole.VIEWER)
    except (AttributeError, TypeError):
        # Default to Viewer role if there's any issue
        role = UserRole.VIEWER

    # Check role permissions
    return has_permission(role, resource, action)

def check_ownership(user: Any, resource_obj: Any) -> bool:
    """
    Check if a user owns a resource.

    Args:
        user: The user to check ownership for
        resource_obj: The specific resource instance

    Returns:
        bool: True if the user owns the resource, False otherwise
    """
    # Check if the resource has an owner_id attribute
    if hasattr(resource_obj, 'owner_id') and hasattr(user, 'id'):
        return str(resource_obj.owner_id) == str(user.id)
    return False

def get_permission_error_message(resource: ResourceType, action: Action) -> str:
    """
    Get a user-friendly error message for permission denial.

    Args:
        resource: The resource being accessed
        action: The action being performed

    Returns:
        str: A formatted error message
    """
    action_names = {
        Action.CREATE: "create",
        Action.READ: "view",
        Action.UPDATE: "update",
        Action.DELETE: "delete",
        Action.LIST: "list",
    }

    resource_names = {
        ResourceType.EXPERIMENT: "experiments",
        ResourceType.FEATURE_FLAG: "feature flags",
        ResourceType.USER: "users",
        ResourceType.ROLE: "roles",
        ResourceType.PERMISSION: "permissions",
        ResourceType.REPORT: "reports",
    }

    action_name = action_names.get(action, str(action))
    resource_name = resource_names.get(resource, str(resource))

    return f"You don't have permission to {action_name} {resource_name}"

def get_required_role(resource: ResourceType, action: Action) -> Optional[UserRole]:
    """
    Determine the minimum role required for an action on a resource.

    Args:
        resource: The resource being accessed
        action: The action being performed

    Returns:
        UserRole: The minimum role required or None if no role has permission
    """
    for role in [UserRole.VIEWER, UserRole.ANALYST, UserRole.DEVELOPER, UserRole.ADMIN]:
        if has_permission(role, resource, action):
            return role

    # If no role has permission
    return None
