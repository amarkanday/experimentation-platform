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

## Permissions System

### Feature Flag Permissions
- Feature flags use an ownership-based permission model where:
  - Superusers can access and modify all feature flags
  - Regular users can only access and modify their own feature flags (where `owner_id` matches the user's ID)
- Endpoints requiring authentication use `deps.get_current_active_user`
- API endpoints for feature flag evaluation use API key authentication via `deps.get_api_key`
- Missing permission checks result in 403 Forbidden responses
- The `core/permissions.py` module provides RBAC support but is not currently used in feature flag endpoints

### Common Permission Issues
- When adding new feature flag endpoints, remember to implement owner or superuser checks
- Feature flag endpoints don't use the `require_permission` function but handle permissions directly
- Feature flag activation/deactivation requires ownership or superuser status
- Watch for permissions in cached data - invalidate cached data when permissions might change
- External API access is controlled through API keys, not user credentials
- When fixing permission bugs, refer to `docs/issue_fixes/feature_flag_permission_fixes.md` and `docs/issue_fixes/rbac_implementation_plan.md`

### Testing Permissions
- Test both regular users and superusers when creating test cases
- Verify that proper 403 responses are returned when unauthorized actions are attempted
- Use mock objects that accurately represent actual objects including ownership properties
- Reference `test_experiment_permissions.py` for permission testing patterns
