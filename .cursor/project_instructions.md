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

## Database Migrations
- Alembic is used for database schema migrations
- Migration files are located in `backend/app/db/migrations/versions/`
- When creating new migrations:
  - Use `alembic revision --autogenerate -m "description"` to generate migration files
  - Check the generated file for accuracy, especially for complex changes
  - Verify that `down_revision` points to the correct previous migration ID
  - Always use revision IDs, not migration names, in the `down_revision` field
- Running migrations:
  - Use `python -m alembic -c app/db/alembic.ini upgrade head` to apply migrations
  - Use `python -m alembic -c app/db/alembic.ini history` to view migration history
  - Set environment variables properly: `POSTGRES_DB=experimentation POSTGRES_SCHEMA=experimentation`
- Troubleshooting:
  - For "multiple heads" errors, create a merge migration with `alembic merge -m "merge heads" revision1 revision2`
  - For database/migration mismatches, use `alembic stamp heads` to mark the current state
  - Always verify migration chain integrity before deploying

## Common Issues
- Database connections must use `localhost` on macOS
- Clear caches when tests fail unexpectedly
- Check for duplicate relationship definitions

## Metrics Model Import Standards

### Issue Summary
- Inconsistent import paths for metrics models (especially `RawMetric`) cause Python to treat them as distinct classes
- This results in:
  - Memory duplication
  - SQLAlchemy "Class is not mapped" errors
  - Type checking failures
  - Unexpected behavior during runtime

### Root Causes
- Mixed import styles: `from app.models.metrics...` vs `from backend.app.models.metrics...`
- Re-exports of classes in `__init__.py` files creating multiple import paths
- Legacy references to deprecated models like `FlagEvaluation` and `RuleMatch`

### Solution & Prevention
1. **Standardized Import Paths**:
   - Always use fully qualified imports: `from backend.app.models.metrics.metric import RawMetric, MetricType`
   - Never use relative imports like `from app.models.metrics...`

2. **Avoid Re-exports**:
   - Don't re-export classes in `__init__.py` files
   - Import directly from the defining module

3. **Testing**:
   - Use the `test_metrics_imports.py` file to verify consistency
   - Add similar tests when introducing new models

4. **Legacy Support**:
   - Use the compatibility layer in `compat.py` for transition
   - Gradually migrate old code to new patterns

5. **Use Pydantic v2 Patterns**:
   - The codebase uses Pydantic v2.10.6
   - Always use Pydantic v2 patterns:
     - Replace `validator` with `field_validator`
     - Replace class-based `Config` with `model_config = ConfigDict(...)`
     - Use `model_validator` for complex validations
   - Import from the correct paths:
     - Use `from pydantic import field_validator, model_validator, ConfigDict`
     - Use `from pydantic_settings import BaseSettings, SettingsConfigDict` for settings

### Automatic Verification
- Run `python standardize_metrics_imports.py --check` to detect inconsistencies
- Run `python -m pytest backend/tests/unit/metrics/test_metrics_imports.py` to verify imports

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

### Experiment Permission Implementation Notes
- **Important**: Do not use `can_delete_experiment` dependency function in the `delete_experiment` endpoint
  - There is a design conflict between dependency requirements and endpoint logic:
    - `can_delete_experiment` depends on `get_experiment_access` → `get_experiment_by_key`
    - `get_experiment_by_key` requires experiments to be ACTIVE and returns a 400 error if they're not
    - The `delete_experiment` endpoint requires experiments to be in DRAFT status
  - Instead, use inline permission checks directly within the endpoint:
    - Accept a required `experiment_key` query parameter
    - Retrieve the experiment directly from the database
    - Perform permission checks in the endpoint
    - Check experiment status (must be DRAFT)
  - This approach eliminates incompatible status requirements while maintaining proper permission checks

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

## Feature Flag Rollout Schedules

The platform supports gradual rollout of feature flags through rollout schedules. This enables controlled, staged deployments of features with configurable criteria for progression.

### Key Components

1. **Rollout Schedules**: Define a plan for gradually increasing a feature flag's rollout percentage over time.
2. **Rollout Stages**: Individual steps within a schedule, each with a target percentage and conditions for activation.
3. **Triggers**: Criteria that determine when to progress to the next stage (time-based, metric-based, or manual).

### Database Models

- `RolloutSchedule`: Main model for rollout schedules.
- `RolloutStage`: Model for individual stages within a schedule.

### API Endpoints

All rollout schedule endpoints are available under `/api/v1/rollout-schedules`.

- `POST /`: Create a new rollout schedule
- `GET /`: List rollout schedules with optional filtering
- `GET /{schedule_id}`: Get a specific rollout schedule
- `PUT /{schedule_id}`: Update a rollout schedule
- `DELETE /{schedule_id}`: Delete a rollout schedule
- `POST /{schedule_id}/activate`: Activate a rollout schedule
- `POST /{schedule_id}/pause`: Pause an active rollout schedule
- `POST /{schedule_id}/cancel`: Cancel a rollout schedule
- `POST /{schedule_id}/stages`: Add a stage to a rollout schedule
- `PUT /stages/{stage_id}`: Update a rollout stage
- `DELETE /stages/{stage_id}`: Delete a rollout stage
- `POST /stages/{stage_id}/advance`: Manually advance a stage

### Scheduler

The `RolloutScheduler` runs in the background to automatically process active rollout schedules. It:

1. Checks for schedules with pending stages that are eligible for activation
2. Updates feature flag rollout percentages according to the stages
3. Transitions stages and schedules through their lifecycle (pending → in_progress → completed)

### Usage Example

```python
# Create a new rollout schedule
schedule_data = {
    "name": "Gradual Rollout for Feature X",
    "description": "Gradually roll out Feature X over 3 weeks",
    "feature_flag_id": "123e4567-e89b-12d3-a456-426614174000",
    "start_date": "2023-12-01T00:00:00Z",
    "end_date": "2023-12-31T23:59:59Z",
    "max_percentage": 100,
    "min_stage_duration": 24,  # Minimum 24 hours between stages
    "stages": [
        {
            "name": "Initial Rollout",
            "description": "First 10% of users",
            "stage_order": 1,
            "target_percentage": 10,
            "trigger_type": "time_based",
            "start_date": "2023-12-01T00:00:00Z"
        },
        {
            "name": "Expanded Rollout",
            "description": "Expand to 50% of users",
            "stage_order": 2,
            "target_percentage": 50,
            "trigger_type": "time_based",
            "start_date": "2023-12-15T00:00:00Z"
        },
        {
            "name": "Full Rollout",
            "description": "Roll out to all users",
            "stage_order": 3,
            "target_percentage": 100,
            "trigger_type": "manual"
        }
    ]
}
```

### Common Gotchas

1. Rollout percentages must be non-decreasing across stages (e.g., 10% → 50% → 100%).
2. Active schedules cannot have their stages deleted.
3. Stage orders must be sequential without gaps.
4. For time-based triggers, ensure the dates are in UTC timezone.
5. Manual stages must be explicitly advanced using the API.

## Safety Monitoring APIs

The platform includes safety monitoring functionality for feature flags to detect and respond to issues in production.

### Key Components

1. **Safety Checks**: Automated checks that monitor metrics like error rates, latency, and API errors.
2. **Rollback Mechanism**: Ability to automatically or manually roll back problematic feature flags.
3. **Safety Settings**: Global configuration for thresholds, monitoring windows, and automatic responses.
4. **Safety Reports**: Comprehensive reports on feature flag health and safety metrics.

### API Endpoints

All safety monitoring endpoints are available under `/api/v1/safety`.

- `GET /settings`: Get current safety monitoring settings (superuser only)
- `PUT /settings`: Update safety monitoring settings (superuser only)
- `POST /check`: Check safety metrics for a specific feature flag
- `GET /check/{feature_flag_id}`: Check safety for a specific feature flag
- `GET /check`: Check safety for all active feature flags
- `POST /rollback/{feature_flag_id}`: Roll back a feature flag to its previous state
- `GET /report`: Generate a comprehensive safety report

### Authentication & Permissions

Safety endpoints use different authentication dependencies based on their sensitivity:

1. **Settings Management** (superuser only):
   - Uses `deps.get_current_superuser` dependency
   - Example: `get_safety_settings` and `update_safety_settings` endpoints

2. **Safety Monitoring** (all authenticated users):
   - Uses `deps.get_current_active_user` dependency
   - Example: `check_feature_flag_safety` and `get_safety_report` endpoints

3. **Feature Flag Rollback** (requires specific permissions):
   - Uses `deps.get_current_active_user` dependency
   - Checks `check_permission(current_user, ResourceType.FEATURE_FLAG, Action.UPDATE)`
   - Example: `rollback_feature_flag` endpoint

### Database Schema

The safety monitoring system uses three main tables:

1. **safety_settings**: Global safety configuration
   - `id`: UUID primary key
   - `created_at`, `updated_at`: Timestamps
   - `enable_automatic_rollbacks`: Boolean flag to enable/disable automatic rollbacks
   - `default_metrics`: JSONB field containing default metric thresholds

2. **feature_flag_safety_configs**: Per-feature flag safety configuration
   - `id`: UUID primary key
   - `created_at`, `updated_at`: Timestamps
   - `feature_flag_id`: Foreign key to feature_flags table
   - `enabled`: Boolean flag to enable/disable safety monitoring
   - `metrics`: JSONB field containing metric thresholds specific to this feature flag
   - `rollback_percentage`: Default percentage to roll back to (default: 0)

3. **safety_rollback_records**: History of safety-triggered rollbacks
   - `id`: UUID primary key
   - `created_at`, `updated_at`: Timestamps
   - `feature_flag_id`: Foreign key to feature_flags table
   - `trigger_type`: Type of rollback trigger (error_rate, latency, manual, etc.)
   - `trigger_reason`: Text description of the rollback reason
   - `previous_percentage`: Rollout percentage before rollback
   - `target_percentage`: Rollout percentage after rollback
   - `success`: Whether the rollback was successful
   - `executed_by_user_id`: UUID of the user who triggered the rollback (null for automatic)

The database migration for these tables is in `backend/app/db/migrations/versions/create_safety_tables.py` (revision ID: 9734af8b92e1).

### Testing Safety APIs

When writing tests for safety endpoints:

1. Mock the appropriate dependencies:
   ```python
   # For superuser endpoints
   with patch("backend.app.api.deps.get_current_superuser", return_value=mock_user):
       response = client.get("/api/v1/safety/settings")

   # For standard authenticated endpoints
   with patch("backend.app.api.deps.get_current_active_user", return_value=mock_user):
       response = client.get("/api/v1/safety/check")
   ```

2. For rollback endpoints, also mock the permission check:
   ```python
   with patch("backend.app.core.permissions.check_permission", return_value=True):
       with patch("backend.app.api.deps.get_current_active_user", return_value=mock_user):
           response = client.post(f"/api/v1/safety/rollback/{feature_flag_id}")
   ```

3. Create appropriate mock responses from the `SafetyService`:
   ```python
   with patch("backend.app.services.safety_service.SafetyService.check_feature_flag_safety") as mock_check:
       mock_check.return_value = expected_result
       # Test API call
   ```

4. Test both success and error scenarios:
   - 200 OK with valid data
   - 403 Forbidden when permission is denied
   - 404 Not Found when resources don't exist
   - 500 Internal Server Error when service throws unexpected exceptions

### Implementation Details

1. **SafetyService**: The core service implementing safety logic in `backend/app/services/safety_service.py`
   - `check_feature_flag_safety`: Evaluates metrics against thresholds
   - `rollback_feature_flag`: Executes feature flag rollback
   - `get_safety_settings`: Retrieves global settings
   - `create_or_update_safety_settings`: Updates global settings

2. **Safety Schemas**: Located in `backend/app/schemas/safety.py`
   - `HealthStatus`: Enum with values HEALTHY, WARNING, CRITICAL, UNKNOWN
   - `MetricThreshold`: Defines warning and critical thresholds
   - Various request/response schemas for settings, configs, and safety checks

3. **Rollback Mechanism**:
   - Safety monitoring can trigger automatic rollbacks when metrics exceed thresholds
   - Rollbacks reduce the feature flag's rollout percentage (typically to 0%)
   - All rollbacks are logged with detailed information about the trigger
   - Manual rollbacks can be performed by superusers through the API
