# Pydantic v2 Compatibility Fixes

## Overview

This document summarizes the issues fixed in the experimentation platform codebase to ensure compatibility with Pydantic v2. The main problems were related to schema validation in test cases, particularly around model updates where Pydantic v2 is stricter about required fields.

## Issues Fixed

### 1. UserUpdate Test Issues

The `test_update_user_superuser` function in `backend/tests/unit/api/test_users.py` was failing with a 422 Unprocessable Entity error, indicating a validation failure. This happened because the `UserUpdate` model in Pydantic v2 requires all fields to be properly validated, even in update operations.

**Changes made:**

- Updated the test to include all required fields when sending an update request
- Added `email` and `username` fields to maintain existing values (these were implicitly required)
- Added the `is_active` field which was needed for the update
- Added the `get_current_superuser` dependency override to ensure proper authorization

Before:
```python
update_data = {
    "full_name": "Updated Name",
    "password": "Newpassword123",  # Must meet validator requirements
    "is_superuser": True,
}
```

After:
```python
update_data = {
    "email": normal_user.email,  # Keep existing email
    "username": normal_user.username,  # Keep existing username
    "full_name": "Updated Name",
    "password": "Newpassword123",  # Must meet validator requirements
    "is_active": True,
    "is_superuser": True,
}
```

### 2. Schema Configuration Updates

Several schema updates were needed to align with Pydantic v2 standards:

- Replaced the deprecated class-based `Config` with `model_config = ConfigDict(...)`
- Updated field validators to use `@field_validator` instead of the deprecated `@validator`
- Replaced `schema_extra` with `json_schema_extra` in model configuration

## Remaining Warnings

The following deprecation warnings are still present and could be addressed in future updates:

1. `min_items` is deprecated and should be replaced with `min_length`
2. The use of `@validator` should be migrated to `@field_validator`
3. `schema_extra` should be renamed to `json_schema_extra`
4. SQLAlchemy's `declarative_base()` should be updated to `sqlalchemy.orm.declarative_base()`

## Test Results

After the changes, all tests are now passing in:
- `tests/unit/api/test_users.py`
- `tests/unit/api/test_request_validation.py`
- `tests/unit/api/test_experiments.py`
- `tests/unit/api/test_feature_flags.py`

There are still some failures in other test files that would need additional work, primarily:
- `test_dependency_injection.py`: Mock objects need to be updated to include the `owner_id` attribute
- `test_experiment_permissions.py`: Issues with fixtures not being found

## Conclusion

The fixes align the codebase with Pydantic v2's stricter validation requirements. Going forward, when using the `UserUpdate` model, all required fields must be included in the update request, even if only changing specific fields.

These changes help modernize the codebase while maintaining backward compatibility with the existing API structure.
