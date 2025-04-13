# AWS Cognito Integration

This document explains how the Experimentation Platform integrates with AWS Cognito for authentication and role-based access control.

## Overview

The platform uses AWS Cognito for user authentication and leverages Cognito groups to automatically assign user roles within the application. This integration provides the following features:

1. Users are automatically created in the system database upon first authentication via Cognito
2. User roles are automatically set based on Cognito group membership
3. Changes to Cognito groups are reflected in user roles on next login
4. Superusers (with full admin privileges) are automatically identified based on membership in designated admin groups

## Configuration

The following settings in `backend/app/core/config.py` control the Cognito integration:

```python
# Cognito settings
COGNITO_GROUP_ROLE_MAPPING: Dict[str, str] = {
    "Admins": "admin",
    "Developers": "developer",
    "Analysts": "analyst",
    "Viewers": "viewer"
}
COGNITO_ADMIN_GROUPS: List[str] = ["Admins", "SuperUsers"]
SYNC_ROLES_ON_LOGIN: bool = True
```

- `COGNITO_GROUP_ROLE_MAPPING`: Maps Cognito group names to application roles
- `COGNITO_ADMIN_GROUPS`: Lists Cognito groups whose members are automatically given superuser status
- `SYNC_ROLES_ON_LOGIN`: When `True`, user roles are updated on each login to match Cognito groups

## User Roles

The application defines the following user roles, in order of decreasing privilege:

1. **ADMIN**: Full access to all features and data
2. **DEVELOPER**: Can create and manage experiments and feature flags
3. **ANALYST**: Can view all data but cannot create or modify experiments/flags
4. **VIEWER**: Read-only access to approved resources

## Role Assignment Logic

When a user authenticates via Cognito, the following logic determines their role:

1. The user's Cognito groups are retrieved via the Cognito API
2. If the user belongs to any group listed in `COGNITO_ADMIN_GROUPS`, they are:
   - Assigned superuser status (`is_superuser = True`)
   - Given the `ADMIN` role regardless of other group mappings
3. Otherwise, their role is determined by the highest-privilege role mapped from their Cognito groups
4. If the user doesn't belong to any mapped group, they default to the `VIEWER` role

## Role Precedence

If a user belongs to multiple Cognito groups that map to different roles, the highest-privilege role wins:

- `ADMIN` takes precedence over `DEVELOPER`
- `DEVELOPER` takes precedence over `ANALYST`
- `ANALYST` takes precedence over `VIEWER`

## Example

A user who belongs to both the "Developers" and "Analysts" Cognito groups will be assigned the `DEVELOPER` role in the application.

A user who belongs to the "SuperUsers" group (which is in `COGNITO_ADMIN_GROUPS`) will automatically be assigned the `ADMIN` role and given superuser status, even if "SuperUsers" is mapped to a different role in `COGNITO_GROUP_ROLE_MAPPING`.

## Implementation Details

The Cognito integration is implemented in the following files:

- `backend/app/core/cognito.py`: Contains utility functions for mapping Cognito groups to roles
- `backend/app/api/deps.py`: Implements the `get_current_user` dependency which handles role assignment
- `backend/app/services/auth_service.py`: Provides the interface to Cognito API

## Testing

To test the Cognito integration:

1. Configure your AWS Cognito User Pool with the appropriate groups
2. Set the required environment variables for Cognito connection
3. Create users and assign them to different groups in Cognito
4. Verify that users receive the expected roles when they log in to the application
