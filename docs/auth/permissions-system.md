# Permissions System Documentation

## Overview
This document describes the role-based access control (RBAC) system implemented in the experimentation platform.

## Core Components

### Roles
- **ADMIN**: Full system access with all permissions
- **USER**: Standard user with limited permissions
- **VIEWER**: Read-only access to all resources

### Resource Types
- **EXPERIMENT**: Experiment-related resources
- **FEATURE_FLAG**: Feature flag resources
- **USER**: User-related resources

### Actions
- **CREATE**: Create new resources
- **READ**: View existing resources
- **UPDATE**: Modify existing resources
- **DELETE**: Remove resources
- **MANAGE**: Special administrative actions

## Permission Matrix

| Role   | Experiment                    | Feature Flag                   | User                          |
|--------|------------------------------|-------------------------------|-------------------------------|
| ADMIN  | CREATE, READ, UPDATE, DELETE, MANAGE | CREATE, READ, UPDATE, DELETE, MANAGE | CREATE, READ, UPDATE, DELETE, MANAGE |
| USER   | CREATE, READ, UPDATE         | CREATE, READ, UPDATE          | READ                         |
| VIEWER | READ                        | READ                         | READ                         |

## Implementation Details

### Core Functions

1. `get_role_permissions(role: UserRole) -> dict`
   - Returns all permissions for a given role
   - Returns empty dict for undefined roles
   - Used internally by permission checking system

2. `has_permission(role: UserRole, resource: ResourceType, action: Action) -> bool`
   - Checks if a role can perform an action on a resource
   - Returns True if role has explicit permission or MANAGE access
   - Main function used by API endpoints for permission checks

3. `get_required_permissions(resource: ResourceType, action: Action) -> List[Action]`
   - Returns list of permissions needed for an action
   - MANAGE permission is always sufficient
   - Used for permission requirement documentation

### Usage Example

```python
from backend.app.core.permissions import has_permission, UserRole, ResourceType, Action

def update_experiment(user, experiment_id):
    # Check if user has permission to update experiments
    if not has_permission(user.role, ResourceType.EXPERIMENT, Action.UPDATE):
        raise HTTPException(
            status_code=403,
            detail="Permission denied: Cannot update experiments"
        )
    # Proceed with update...
```

## Testing

### Role Permission Tests
- ✅ Admin has full system access
- ✅ User has limited create/read/update permissions
- ✅ Viewer has read-only access
- ✅ Undefined roles have no permissions

### Permission Check Tests
- ✅ Admin can perform all actions
- ✅ User permissions are properly limited
- ✅ Viewer can only read resources
- ✅ Permission requirements are correctly calculated

### Edge Cases
- ✅ Roles not in permission mapping have no access
- ✅ MANAGE permission grants full access
- ✅ Permission checks handle missing role definitions

## Implementation Notes

1. The system uses Python's Enum for type safety
2. Permissions are defined in a centralized dictionary
3. The implementation is stateless and efficient
4. Type hints are used throughout for better IDE support
5. Tests cover both positive and negative cases

## Integration with Cognito

The permission system integrates with AWS Cognito:
- Roles are mapped to Cognito groups
- Role information is included in JWT tokens
- The `get_current_user` dependency extracts roles from tokens

## Future Enhancements

Potential improvements to consider:
1. Dynamic permission management through admin interface
2. Custom role creation
3. Resource-level permissions
4. Permission inheritance
5. Audit logging for permission changes
