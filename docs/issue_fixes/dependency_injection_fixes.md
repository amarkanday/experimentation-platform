# Dependency Injection Fixes

## Issue Description

Multiple test failures were occurring in the User model tests and related API tests. The tests were failing with the following issues:

1. The `test_user_role_relationship` test in `tests/unit/models/test_core_data_models.py` was failing
2. Several user-related API tests in `tests/unit/api/test_users.py` were failing
3. The API endpoints were unable to properly handle user role relationships

These issues indicated problems with the dependency injection system used in the application, specifically in how User objects and their relationships were being handled.

## Root Cause

After investigation, the following root causes were identified:

1. **Circular Dependency Issues**: The dependency injection system in FastAPI was encountering circular imports when trying to resolve dependencies for User models and their relationships.

2. **Incorrect Parameter Types**: The functions in `app/api/deps.py` had incorrect parameter type annotations, leading to compatibility issues between the real User model and the mock models used in tests.

3. **Incomplete Mock Objects**: The mock objects used in tests were not properly mimicking all required functionality of the real objects, particularly around role relationships.

4. **Improper Dependency Resolution**: The way dependencies were being resolved in the test environment did not match how they were resolved in the production environment.

## Solution

The following changes were implemented to fix the issues:

1. **Improved Dependency Type Annotations**: Updated the type annotations in `app/api/deps.py` to properly handle both direct model objects and dictionary representations of those objects, using `Union[Experiment, Dict[str, Any]]` where appropriate.

2. **Enhanced Mock Objects**: Improved the mock objects in tests to more accurately represent the behavior of real database models, particularly around relationships and equality checks.

3. **Standardized User Role Handling**: Updated how user roles are assigned and checked throughout the application to ensure consistency between the authentication system and the database.

4. **Updated Test Fixtures**: Improved the test fixtures to properly initialize and handle dependency injection, with proper mocking of database sessions and user objects.

5. **Fixed Duplicate Function Definition**: Fixed a duplicated definition of `get_experiment_access` in `app/api/deps.py` that was causing confusion in dependency resolution.

## Testing

The solution was verified by running the previously failing tests:

1. Successfully ran the `test_user_role_relationship` test in `tests/unit/models/test_core_data_models.py`
2. Successfully ran all tests in `tests/unit/api/test_users.py`
3. Ran the full test suite to ensure no regressions were introduced

All 17 tests in the user API test file now pass successfully, and the core User model tests are working correctly. The only remaining failing tests (5 out of 414) are related to experiment deletion functionality, which is a separate issue.

## Lessons Learned

1. **Type Annotations Matter**: Proper type annotations are crucial in a dependency injection system, especially with complex object relationships.

2. **Mock Objects Need Careful Design**: When mocking complex objects with relationships, ensure that the mock objects accurately represent all required behavior of the real objects.

3. **Avoid Duplicate Functions**: Duplicate function definitions can lead to confusing behavior in dependency resolution and should be avoided.

4. **Test Fixtures Need Regular Maintenance**: As the application evolves, test fixtures need to be updated to ensure they continue to accurately represent the production environment.

5. **Dependency Injection Complexity**: Dependency injection systems can become complex in large applications and require careful design and maintenance to avoid issues like circular dependencies.
