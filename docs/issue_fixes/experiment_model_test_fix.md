# Experiment Test Mock Object Type Fix

## Issue Description

In the `test_get_experiment_found` function within `backend/tests/unit/api/test_experiments.py`, tests were failing with the following error:

```
AttributeError: 'dict' object has no attribute 'owner_id'
```

This error occurred in the `get_experiment_access` function, which was trying to access the `owner_id` attribute of what was expected to be an experiment model object but was actually a dictionary.

## Update: Related Dependency Injection Fixes

This issue was part of a larger pattern of dependency injection and type handling problems that have now been comprehensively addressed. A more thorough dependency injection fix has been implemented that resolves similar issues across the codebase:

1. The `get_experiment_access` function has been updated to properly handle both model objects and dictionary representations using a Union type: `Union[Experiment, Dict[str, Any]]`
2. A duplicate definition of the `get_experiment_access` function was removed, preventing ambiguity in dependency resolution
3. Mock objects have been enhanced to better represent real model behavior in tests

For full details on the comprehensive dependency injection fixes, see [Dependency Injection Fixes](dependency_injection_fixes.md).

## Root Cause

The issue was related to mock objects and typing in the tests for experiment endpoints:

1. The test was mocking the return value of `experiment_service.get_experiment_by_id()` using a dictionary instead of a proper model object
2. While the dictionary had an `owner_id` key, the `deps.get_experiment_access` function was expecting an actual object with an `owner_id` attribute
3. This type mismatch caused the attribute access to fail when trying to perform permission checks

This issue highlights the importance of using appropriate mock objects that correctly simulate the behavior of the actual objects they're replacing in tests.

## Fix Implementation

The solution was to update the test to use a proper `MockExperiment` object instead of a plain dictionary, which ensured that attribute access worked correctly:

1. Changed the mock to use a `MockExperiment` instance instead of a dictionary:
   ```python
   # Create a proper Experiment object for the mock
   mock_experiment = MockExperiment(
       id=experiment_id,
       name="Test Experiment",
       description="Test Description",
       hypothesis="Test Hypothesis",
       status=ModelExperimentStatus.DRAFT,
       experiment_type="a_b",
       targeting_rules={},
       tags=["test"],
       owner_id=mock_user.id,
       variants=[],
       metrics=[]
   )
   ```

2. Added a mock for the `get_experiment_access` dependency to ensure it returns the properly formatted object:
   ```python
   # Create a mock for deps.get_experiment_access to return the same mock experiment
   with patch("backend.app.api.deps.get_experiment_access", return_value=mock_experiment):
       # Call the endpoint
       response = await experiments.get_experiment(
           experiment_id=experiment_id,
           db=mock_db,
           current_user=mock_user,
           cache_control=mock_cache_control,
       )
   ```

3. Updated the assertions to properly compare the response with the mock object:
   ```python
   # For simpler comparison, verify key fields match
   assert str(response_dict["id"]) == str(mock_experiment.id)
   assert response_dict["name"] == mock_experiment.name
   assert response_dict["description"] == mock_experiment.description
   assert response_dict["hypothesis"] == mock_experiment.hypothesis
   assert response_dict["status"] == str(mock_experiment.status.value)
   ```

## Lessons Learned

1. **Mock Consistency**: Mock objects should accurately represent the behavior and structure of the real objects they replace in tests. Using a dictionary is not always sufficient - sometimes a proper object with the same interface is required.

2. **Type Awareness**: In Python, even with duck typing, it's important to understand the expected type of objects being passed between functions, especially when working with attribute access vs. dictionary key access.

3. **Test Design**: Tests should be designed to validate functionality as close to real usage as possible. Using mock objects that closely match real objects helps ensure tests catch issues that would occur in production.

4. **Attribute Access Methods**: For production code, consider using patterns like `getattr()` with a default value or proper handling of `AttributeError` to make code more robust against wrong object types.

This fix demonstrates the importance of using proper typing in tests, even in a dynamically typed language like Python, to ensure tests accurately validate the expected behavior of the code.
