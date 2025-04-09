from enum import Enum
from typing import List, Dict, Any

class UserRole(str, Enum):
    """User roles in the system."""
    SUPERUSER = "superuser"
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class ResourceType(str, Enum):
    """Types of resources that can be protected."""
    EXPERIMENT = "experiment"
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"

class Action(str, Enum):
    """Actions that can be performed on resources."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"

# Role-based access control (RBAC) permissions mapping
ROLE_PERMISSIONS: Dict[UserRole, Dict[ResourceType, List[Action]]] = {
    UserRole.SUPERUSER: {
        ResourceType.EXPERIMENT: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
        ResourceType.USER: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
        ResourceType.ROLE: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
        ResourceType.PERMISSION: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
    },
    UserRole.ADMIN: {
        ResourceType.EXPERIMENT: [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.LIST],
        ResourceType.USER: [Action.READ, Action.LIST],
        ResourceType.ROLE: [Action.READ, Action.LIST],
        ResourceType.PERMISSION: [Action.READ, Action.LIST],
    },
    UserRole.USER: {
        ResourceType.EXPERIMENT: [Action.CREATE, Action.READ, Action.UPDATE, Action.LIST],
        ResourceType.USER: [Action.READ],
        ResourceType.ROLE: [Action.READ],
        ResourceType.PERMISSION: [Action.READ],
    },
    UserRole.VIEWER: {
        ResourceType.EXPERIMENT: [Action.READ, Action.LIST],
        ResourceType.USER: [Action.READ],
        ResourceType.ROLE: [Action.READ],
        ResourceType.PERMISSION: [Action.READ],
    },
}

def has_permission(role: UserRole, resource: ResourceType, action: Action) -> bool:
    """Check if a role has permission to perform an action on a resource."""
    if role not in ROLE_PERMISSIONS:
        return False
    if resource not in ROLE_PERMISSIONS[role]:
        return False
    return action in ROLE_PERMISSIONS[role][resource]
