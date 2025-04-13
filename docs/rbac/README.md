# Role-Based Access Control (RBAC) System

## Overview

The Experimentation Platform implements a robust Role-Based Access Control (RBAC) system to manage permissions across different resources. This document explains the permission architecture and how to use it in the application.

## User Roles

Users in the system can have one of the following roles:

- **Admin**: Full access to all features and resources
- **Developer**: Can create and manage experiments and feature flags
- **Analyst**: Can view experiments and create analytics reports
- **Viewer**: Read-only access to approved resources

Each role has a specific set of permissions that determine what actions they can perform on various resources.

## Resources and Actions

Permissions are defined as combinations of resources and actions:

### Resources

- **Experiment**: A/B tests and experiments
- **FeatureFlag**: Feature flags and toggles
- **User**: User accounts
- **Role**: User roles
- **Permission**: Permission assignments
- **Report**: Analytics reports and dashboards

### Actions

- **CREATE**: Create new resources
- **READ**: View existing resources
- **UPDATE**: Modify existing resources
- **DELETE**: Remove resources
- **LIST**: Retrieve lists of resources

## Permission Matrix

The following table shows which roles can perform which actions on which resources:

| Role      | Experiment                 | Feature Flag               | User          | Report                    |
|-----------|----------------------------|----------------------------|---------------|---------------------------|
| Admin     | Create, Read, Update, Delete | Create, Read, Update, Delete | Create, Read, Update, Delete | Create, Read, Update, Delete |
| Developer | Create, Read, Update, Delete | Create, Read, Update, Delete | Read         | Read                      |
| Analyst   | Read                       | Read                       | Read         | Create, Read, Update, Delete |
| Viewer    | Read                       | Read                       | Read         | Read                      |

## Ownership-Based Access

In addition to role-based permissions, the system also supports ownership-based access:

- Users who create a resource automatically become its owner
- Owners have full access to their own resources regardless of their role
- Non-owners can only access resources based on their role permissions

## Usage in Code

### Checking Permissions

To check if a user has permission to perform an action:

```python
from backend.app.core.permissions import check_permission, ResourceType, Action

# Check if user can create an experiment
if check_permission(current_user, ResourceType.EXPERIMENT, Action.CREATE):
    # Allow the user to create an experiment
else:
    # Return permission denied error
```

### Checking Ownership

To check if a user owns a specific resource:

```python
from backend.app.core.permissions import check_ownership

# Check if user owns an experiment
if check_ownership(current_user, experiment):
    # Allow special operations for owners
```

### Getting Error Messages

To generate standardized error messages:

```python
from backend.app.core.permissions import get_permission_error_message

message = get_permission_error_message(ResourceType.EXPERIMENT, Action.CREATE)
# Returns: "You don't have permission to create experiments"
```

### Determining Required Roles

To determine what role is needed for a specific action:

```python
from backend.app.core.permissions import get_required_role

role = get_required_role(ResourceType.REPORT, Action.CREATE)
# Returns: UserRole.ANALYST
```

## Implementation Details

The permission system is implemented in the following files:

- `backend/app/core/permissions.py`: Core permission checking functions
- `backend/app/models/user.py`: User model with role field
- `backend/app/api/deps.py`: FastAPI dependency functions for permission checks

## Adding New Resources

To add a new resource type to the permission system:

1. Add the resource to the `ResourceType` enum in `permissions.py`
2. Update the `ROLE_PERMISSIONS` mapping to include the new resource
3. Create dependency functions for the new resource in `deps.py`

## Testing Permissions

The permission system includes comprehensive tests in:

- `backend/tests/unit/core/test_permissions.py`: Tests for permission checking functions
- `backend/tests/unit/api/test_permission_deps.py`: Tests for permission dependency functions

## Best Practices

1. Always use the permission checking functions instead of hardcoding role checks
2. Include clear error messages when denying access
3. Test permission checks thoroughly
4. Consider both role-based permissions and ownership when designing endpoints
