# Cursor Project Instructions

## Code Style
- Follow PEP 8 for Python code
- Use type annotations
- Document public functions with docstrings

## Testing
- Write tests for all new features
- Clear schema cache between tests with `clear_schema_cache()`
- Ensure PostgreSQL is running locally with docker before tests
- Use localhost for postgres running in Docker
- ensure that virtualenv is activated before running tests
- cd /Users/ashishmarkanday/github/experimentation-platform && source venv/bin/activate && APP_ENV=test && TESTING=true

## Database
- Use SQLAlchemy for database operations
- Always include schema in table definitions
- Watch for duplicate relationship definitions

## Common Issues
- Database connections must use `localhost` on macOS
- Clear caches when tests fail unexpectedly
- Check for duplicate relationship definitions

## Async
- Feature flag and report-related dependencies are asynchronous (e.g., `get_feature_flag_access`, `can_create_feature_flag`, `get_report_access`)
- Experiment-related dependencies are synchronous (e.g., `get_experiment_access`, `can_create_experiment`)
- When testing async functions, use:
  - `@pytest.mark.asyncio` decorator on test functions
  - `async def` for test function declarations
  - `await` when calling async functions
- Make sure to check for READ permission before UPDATE permission in the correct order
- Don't mix async and sync patterns incorrectly - follow the implementation in `deps.py`

## Permissions System

### Role-Based Access Control (RBAC)
- The `core/permissions.py` module implements a comprehensive RBAC system with four roles:
  - ADMIN: Full access to all resources and actions
  - DEVELOPER: Can create and manage experiments and feature flags
  - ANALYST: Can view all data but cannot create or modify resources
  - VIEWER: Read-only access to approved resources
- Role permissions are defined in the `ROLE_PERMISSIONS` dictionary mapping roles to allowed actions
- Permission checks use the `check_permission(user, resource_type, action)` function
- Ownership checks complement permission checks using `check_ownership(user, resource)`
- All critical endpoints integrate permission checks before processing requests
- Unauthorized actions return 403 Forbidden responses with descriptive error messages

### Feature Flag Permissions
- Feature flags use an ownership-based permission model where:
  - Superusers can access and modify all feature flags
  - Regular users can only access and modify their own feature flags (where `owner_id` matches the user's ID)
- Endpoints requiring authentication use `deps.get_current_active_user`
- API endpoints for feature flag evaluation use API key authentication via `deps.get_api_key`
- Missing permission checks result in 403 Forbidden responses
- The `core/permissions.py` module provides RBAC support but is not currently used in feature flag endpoints
  - A ticket for integrating feature flags with the RBAC system has been created: `docs/issue_fixes/feature_flag_permission_integration.md`
- Feature flag permissions are implemented as async functions in `deps.py`:
  - `get_feature_flag_access`: Checks if a user can access a feature flag (requires await)
  - `can_create_feature_flag`: Checks if a user can create a feature flag (requires await)
  - `can_update_feature_flag`: Checks if a user can update a feature flag (requires await)
  - `can_delete_feature_flag`: Checks if a user can delete a feature flag (requires await)
- Schema validation for feature flags requires `owner_id` to be an integer:
  - In `FeatureFlagReadExtended` schema, `owner_id` is defined as `Optional[int]`
  - When mocking feature flags in tests, ensure `owner_id` is cast to int, not left as a UUID string
  - A common validation error is: `Input should be a valid integer, unable to parse string as an integer`

### Common Permission Issues
- When adding new feature flag endpoints, remember to implement owner or superuser checks
- Feature flag endpoints don't use the `require_permission` function but handle permissions directly
- Feature flag activation/deactivation requires ownership or superuser status
- Watch for permissions in cached data - invalidate cached data when permissions might change
- External API access is controlled through API keys, not user credentials
- When fixing permission bugs, refer to `docs/issue_fixes/feature_flag_permission_fixes.md` and `docs/issue_fixes/rbac_implementation_plan.md`
- Be careful about mixing async and sync patterns - use await with async functions

### Testing Permissions
- Test both regular users and superusers when creating test cases
- Verify that proper 403 responses are returned when unauthorized actions are attempted
- Use mock objects that accurately represent actual objects including ownership properties
- Reference `test_experiment_permissions.py` for permission testing patterns
- Multiple test classes are available for permission testing:
  - `TestExperimentPermissionDeps`: Tests experiment permission dependency functions
  - `TestFeatureFlagPermissionDeps`: Tests feature flag permission dependency functions
  - `TestFeatureFlagPermissions`: Tests RBAC enforcement for feature flags with different user roles
  - `TestReportPermissionDeps`: Tests report permission dependency functions
- All permission tests should validate that:
  - ADMIN users can perform all actions
  - DEVELOPER users can create and manage resources
  - ANALYST users can view but not modify resources
  - VIEWER users have read-only access
  - Unauthorized actions return 403 Forbidden responses
- For feature flag and report tests:
  - Use `@pytest.mark.asyncio` decorator
  - Define test functions as `async def test_function_name`
  - Use `await` when calling async dependency functions
  - Properly mock both `check_permission` and `check_ownership` in permissions tests
  - For permissions side effects, handle both READ and UPDATE permissions in the mock function
- For experiment tests:
  - Use regular synchronous test functions
  - Call dependency functions directly without `await`
