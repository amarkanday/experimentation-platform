# Feature Flag RBAC Integration Ticket

## Issue Description
Currently, the feature flag endpoints in the experimentation platform implement permission checks directly in the route handlers rather than leveraging the existing role-based access control (RBAC) system defined in `core/permissions.py`. This inconsistency creates maintenance challenges and makes it harder to enforce a uniform permission model across the application.

## Background
The codebase has a well-designed RBAC system in `core/permissions.py` that defines:
- Resource types (Experiment, FeatureFlag, User, Role, Permission, Report)
- Actions (Create, Read, Update, Delete)
- Role-based permission mappings (ADMIN, DEVELOPER, ANALYST, VIEWER)
- Helper functions for permission checking

However, feature flag endpoints don't fully utilize this system. Instead, they implement permission checks directly in the endpoint handlers, primarily relying on:
- Superuser status checks
- Resource ownership checks
- HTTP 403 error responses with custom messages

## Objectives
1. Refactor feature flag endpoints to use the RBAC permission system consistently
2. Ensure proper permission checks based on user roles
3. Maintain backward compatibility with existing behavior
4. Add proper unit tests to verify role-based permissions for feature flags

## Acceptance Criteria
- [ ] Update feature flag endpoints in `backend/app/api/v1/endpoints/feature_flags.py` to use RBAC permission checks
- [ ] Replace direct permission checking with calls to `check_permission` and `check_ownership` from `core/permissions.py`
- [ ] Update dependency functions in `deps.py` to be consistent with the RBAC approach
- [ ] Ensure all role types (ADMIN, DEVELOPER, ANALYST, VIEWER) have appropriate access based on the permission matrix
- [ ] Add or update unit tests to verify RBAC permissions for feature flag endpoints
- [ ] Document the changes in both code comments and the implementation plan

## Implementation Steps
1. Audit current feature flag permission checks in endpoint handlers
2. Compare with permissions defined in `ROLE_PERMISSIONS` in `core/permissions.py`
3. Update dependency functions in `deps.py` to use the RBAC functions consistently
4. Refactor endpoint handlers to use these updated dependency functions
5. Update unit tests to verify different user roles have appropriate access
6. Add test cases for denied permissions

## Technical Notes
- Permission functions in `deps.py` are already using `check_permission` and `check_ownership` but they're not consistently used in endpoints
- The feature flag endpoints are async, so ensure proper `await` usage with async dependency functions
- When testing, use `@pytest.mark.asyncio` for async tests
- Ownership checks should still be made for non-admin users
- Superusers should maintain full access regardless of role

## Related Files
- `backend/app/api/v1/endpoints/feature_flags.py` - Feature flag endpoints
- `backend/app/api/deps.py` - Dependency functions for permission checks
- `backend/app/core/permissions.py` - RBAC permission definitions
- `backend/tests/unit/api/test_feature_flags.py` - Tests for feature flag endpoints
- `backend/tests/unit/api/test_permission_deps.py` - Tests for permission dependencies

## Estimated Time
- Analysis: 2 hours
- Implementation: 4 hours
- Testing: 2 hours
- Documentation: 1 hour
- Total: 9 hours

## Risks
- Breaking existing permission behavior
- Introducing regressions in feature flag access
- Complexity in transitioning from direct checks to RBAC system
- Ensuring backward compatibility with existing clients

## References
- [RBAC Implementation Plan](./rbac_implementation_plan.md)
- [Project Instructions](../../.cursor/project_instructions.md)
