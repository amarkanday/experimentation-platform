# Simplified RBAC Implementation Plan Using Existing Role Structure

## Overview
This document presents a streamlined approach to implementing role-based access control (RBAC) in the experimentation platform without adding new database tables for roles. Instead, it leverages the existing user model and Cognito groups to manage permissions.

## Objectives
1. Utilize existing user model attributes for role assignment
2. Implement permission verification throughout the application
3. Integrate with Cognito groups for role management
4. Ensure minimal database changes while providing robust access control

## Implementation Phases

### Phase 1: Role and Permission Definition (Week 1)
- [ ] Define core user roles using existing `User.is_superuser` field and a new `role` field
- [ ] Map permissions to each role in code (not database)
- [ ] Document authentication flow with simplified RBAC integration

**Deliverable:** Permission matrix document mapping roles to permissions

### Phase 2: User Model Extension (Week 1)
- [ ] Update existing `User` model to add a `role` enum field:
  ```python
  class UserRole(str, Enum):
      ADMIN = "admin"      # existing superusers
      DEVELOPER = "developer"  # can create experiments
      ANALYST = "analyst"   # can analyze data
      VIEWER = "viewer"     # read-only access

  class User(Base):
      # existing fields
      role: UserRole = Column(String, default=UserRole.VIEWER)
  ```
- [ ] Create a simple database migration for the new role field
- [ ] Update user creation/update logic to handle roles

**Deliverable:** Updated user model and migration

### Phase 3: Permission Enforcement (Week 2)
- [ ] Create a permissions utility module:
  ```python
  def has_permission(user, resource, action) -> bool:
      # Define role-based permissions in code
      permissions = {
          UserRole.ADMIN: ["*:*"],  # Admin can do everything
          UserRole.DEVELOPER: ["experiments:*", "feature_flags:*", "users:read"],
          UserRole.ANALYST: ["experiments:read", "analytics:*", "reports:*"],
          UserRole.VIEWER: ["experiments:read", "feature_flags:read", "reports:read"]
      }

      # Check if user has permission
      if user.is_superuser or user.role == UserRole.ADMIN:
          return True

      allowed_permissions = permissions.get(user.role, [])
      for permission in allowed_permissions:
          if permission_matches(permission, f"{resource}:{action}"):
              return True

      return False
  ```
- [ ] Create FastAPI dependencies for permission verification:
  ```python
  def require_permission(resource: str, action: str):
      def dependency(current_user = Depends(get_current_user)):
          if not has_permission(current_user, resource, action):
              raise HTTPException(status_code=403, detail="Permission denied")
          return current_user
      return dependency
  ```
- [ ] Add permission checks to existing API endpoints

**Deliverable:** Permission enforcement system integrated with existing endpoints

### Phase 4: Cognito Integration (Week 2)
- [ ] Configure Cognito groups to match our role definitions
- [ ] Update `get_current_user` dependency to extract role from Cognito token:
  ```python
  def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
      try:
          user_data = auth_service.get_user(token)

          # Get user from database
          username = user_data.get("username")
          user = db.query(User).filter(User.username == username).first()

          # Extract role from Cognito groups
          cognito_groups = user_data.get("cognito:groups", [])
          role = map_cognito_groups_to_role(cognito_groups)

          if not user:
              # Create user with extracted role
              # ...
          else:
              # Update user's role if changed
              if role and user.role != role:
                  user.role = role
                  db.commit()

          return user
      except Exception as e:
          logger.error(f"Authentication error: {str(e)}")
          raise HTTPException(status_code=401)
  ```

**Deliverable:** Cognito integration for role management

### Phase 5: User Interface Updates (Week 3)
- [ ] Add role indicator to user profile page
- [ ] Implement conditional UI rendering based on user role
- [ ] Add basic role management for admins (assign roles to users)

**Deliverable:** User interface updates reflecting user roles

### Phase 6: Testing & Documentation (Week 3)
- [ ] Create pytest fixtures for different user roles
- [ ] Add permission verification tests
- [ ] Update API documentation with role requirements
- [ ] Create user guide for role-based features

**Deliverable:** Test suite and documentation

## Role Definitions (Using Existing Structure)

### Admin (is_superuser=True, role="admin")
- Full system access
- User management
- System configuration

### Developer (is_superuser=False, role="developer")
- Create and manage experiments and feature flags
- Access to API keys and SDKs
- Cannot modify system configuration

### Analyst (is_superuser=False, role="analyst")
- View all experiments and feature flags
- Create and manage analyses
- Cannot modify experiments or system configuration

### Viewer (is_superuser=False, role="viewer")
- Read-only access to experiments and feature flags
- No management capabilities

## Permission Checking Implementation

```python
# Example usage in API endpoint
@router.post("/experiments/", response_model=ExperimentResponse)
async def create_experiment(
    experiment: ExperimentCreate,
    current_user: User = Depends(require_permission("experiments", "create"))
):
    # User has permission to create experiments
    return experiment_service.create_experiment(experiment, current_user.id)
```

## Advantages of This Approach

1. **Minimal Database Changes**: Only adds one field to the existing User model
2. **Easy Integration**: Works with existing authentication system
3. **Faster Implementation**: Can be completed in approximately 3 weeks
4. **Simpler Maintenance**: Fewer moving parts, permissions defined in code
5. **Cognito Integration**: Leverages existing Cognito groups for role assignment

## Future Enhancements (Post-Implementation)

1. Move to a more dynamic permission system if needed
2. Add more granular permissions at the resource instance level
3. Implement audit logging for permission changes
4. Add custom role creation for larger organizations
