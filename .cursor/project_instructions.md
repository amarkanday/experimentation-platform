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

## Experiment Scheduling

### Implementation
- Experiment scheduling functionality allows setting future start and end dates for experiments
- The `update_experiment_schedule` service method handles schedule updates
- API endpoint for updating schedules: `PUT /api/v1/experiments/{experiment_id}/schedule`
- Schedule configuration includes:
  - `start_date`: When the experiment should automatically activate
  - `end_date`: When the experiment should automatically complete
  - `time_zone`: Time zone for interpreting the dates (default: UTC)
- Experiments must be in DRAFT or PAUSED status to be scheduled
- End date must be after start date with a minimum duration of 1 hour

### Scheduler Implementation
- A background task scheduler is implemented in `backend/app/core/scheduler.py` that automatically transitions experiments based on their scheduled dates
- The scheduler:
  - Runs periodically (every 15 minutes by default) to check for experiments that need status updates
  - Activates experiments when current time reaches or passes their `start_date`
  - Completes experiments when current time reaches or passes their `end_date`
  - Logs all automatic status transitions
  - Handles timezone conversions using the stored `time_zone` metadata
- Key components:
  - `ExperimentScheduler` class manages the scheduling process
  - `process_scheduled_experiments()` method performs the state transitions
  - The scheduler is started/stopped automatically when the FastAPI application starts/stops
  - Admin-only endpoint `POST /api/v1/experiments/schedules/process` for manually triggering the scheduler

### Test Considerations
- When testing the scheduler, use the provided unit tests in `backend/tests/unit/services/test_experiment_scheduler.py`
- Test activation (DRAFT → ACTIVE) and completion (ACTIVE → COMPLETED) transitions
- Mock the database session when testing the scheduler
- Test timezone handling
- For schedule API tests, ensure proper authentication mocking via:
  ```python
  with patch("backend.app.api.deps.get_current_user", return_value=mock_current_user):
      response = client.put(...)
  ```

## Test Environment Configuration

### Database Setup
- Ensure PostgreSQL is running locally in Docker for tests
- Database connection string should use `localhost` on macOS
- Test users must have a `hashed_password` value set to avoid integrity errors

### Authentication Setup
- Mock dependencies that involve AWS Cognito for API tests
- For API test fixtures, provide mock users with required fields
- Use a structure like:
  ```python
  user = User(
      id=uuid4(),
      username="test_user",
      email="test@example.com",
      is_superuser=True,
      hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # Password hash
  )
  ```
- Properly mock authentication with:
  ```python
  async def mock_get_current_user():
      return user
  monkeypatch.setattr("backend.app.api.deps.get_current_user", mock_get_current_user)
  ```

### Complete Authentication Mocking for API Tests
- For API tests that use tokens, you need to mock multiple components of the auth system:

1. Mock the `get_current_user` and `get_current_active_user` dependencies:
   ```python
   with patch("backend.app.api.deps.get_current_user", AsyncMock(return_value=user)), \
        patch("backend.app.api.deps.get_current_active_user", MagicMock(return_value=user)):
   ```

2. Mock the token decoding to bypass AWS Cognito validation:
   ```python
   with patch("backend.app.core.security.decode_token",
             MagicMock(return_value={"sub": str(user.id), "username": user.username})):
   ```

3. Mock the Cognito auth service to return user data with appropriate groups:
   ```python
   with patch("backend.app.services.auth_service.CognitoAuthService.get_user_with_groups",
             MagicMock(return_value={
                 "username": user.username,
                 "attributes": {"email": user.email},
                 "groups": ["admin-group"]  # This will map to ADMIN role
             })):
   ```

4. For fixtures that provide tokens, include all these mocks:
   ```python
   @pytest.fixture
   def admin_token(admin_user, monkeypatch):
       token = "mock_admin_token"
       # Mock get_current_user
       async def mock_get_current_user():
           return admin_user
       monkeypatch.setattr("backend.app.api.deps.get_current_user", mock_get_current_user)

       # Mock get_current_active_user
       def mock_get_current_active_user():
           return admin_user
       monkeypatch.setattr("backend.app.api.deps.get_current_active_user", mock_get_current_active_user)

       # Mock auth_service.get_user_with_groups
       def mock_get_user_with_groups(*args, **kwargs):
           return {
               "username": admin_user.username,
               "attributes": {"email": admin_user.email},
               "groups": ["admin-group"]
           }
       monkeypatch.setattr("backend.app.services.auth_service.CognitoAuthService.get_user_with_groups",
                          mock_get_user_with_groups)

       # Mock token decoder
       def mock_decode_token(*args, **kwargs):
           return {"sub": str(admin_user.id), "username": admin_user.username}
       monkeypatch.setattr("backend.app.core.security.decode_token", mock_decode_token)

       return token
   ```

### Running Tests
- Activate the virtual environment before running tests:
  ```
  cd /Users/ashishmarkanday/github/experimentation-platform && source venv/bin/activate
  ```
- Set environment variables for testing:
  ```
  APP_ENV=test TESTING=true
  ```
- Run specific test modules with:
  ```
  python -m pytest backend/tests/unit/services/test_experiment_scheduling.py -v
  ```
