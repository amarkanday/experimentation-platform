# Deprecation Warnings Fixes

This document summarizes the deprecation warnings that were addressed in the codebase to ensure compatibility with newer library versions.

## Overview

Several deprecation warnings were identified during test runs, primarily related to:
1. Pydantic V1 to V2 migration issues
2. SQLAlchemy legacy imports
3. FastAPI parameter deprecations

## Fixed Issues

### 1. SQLAlchemy Deprecation Warning

**Issue:** The use of `declarative_base()` from `sqlalchemy.ext.declarative` is deprecated since SQLAlchemy 2.0.

**Fix:** Updated the import path to use the newer location:
```python
# Before
from sqlalchemy.ext.declarative import declarative_base

# After
from sqlalchemy.orm import declarative_base
```

**File changed:** `backend/app/models/base.py`

### 2. Pydantic Validator Deprecation

**Issue:** Pydantic V1 style `@validator` decorators are deprecated in favor of V2 style `@field_validator`.

**Fix:** Updated the validators and added the required `@classmethod` decorator:
```python
# Before
@validator("baseline_rate")
def validate_baseline_rate(cls, v):
    # ...

# After
@field_validator("baseline_rate")
@classmethod
def validate_baseline_rate(cls, v):
    # ...
```

**File changed:** `backend/app/api/v1/sample_size_calculator.py`

### 3. Pydantic List Validation Deprecation

**Issue:** The `min_items` and `max_items` attributes for validating list lengths are deprecated in favor of `min_length` and `max_length`.

**Fix:** Updated the field definitions:
```python
# Before
variants: List[VariantBase] = Field(
    ..., min_items=1, description="Experiment variants"
)

# After
variants: List[VariantBase] = Field(
    ..., min_length=1, description="Experiment variants"
)
```

**File changed:** `backend/app/schemas/experiment.py`

### 4. Pydantic Config Schema Deprecation

**Issue:** The class-based `Config` with `schema_extra` is deprecated in favor of `ConfigDict` with `json_schema_extra`.

**Fix:** Updated the configuration style:
```python
# Before
class Config:
    """Pydantic model configuration."""
    schema_extra = {
        "example": {
            # ...
        }
    }

# After
model_config = ConfigDict(
    json_schema_extra={
        "example": {
            # ...
        }
    }
)
```

**Files changed:** Multiple schema files across the codebase

### 5. FastAPI Example Parameter Deprecation

**Issue:** The `example` parameter in FastAPI `Body()` is deprecated in favor of `examples`.

**Fix:** Updated to use the structured examples format:
```python
# Before
Body(
    ...,
    description="Batch of events to track",
    example={
        "events": [
            # ...
        ]
    },
)

# After
Body(
    ...,
    description="Batch of events to track",
    examples={
        "default": {
            "summary": "Batch tracking example",
            "description": "A sample batch of events to track for an experiment",
            "value": {
                "events": [
                    # ...
                ]
            }
        }
    },
)
```

**File changed:** `backend/app/api/v1/endpoints/tracking.py`

## Remaining Warnings

Some warnings remain in the external libraries and are not directly fixable in our codebase:

1. Pydantic internal warnings about config keys changing in V2, specifically the `schema_extra` to `json_schema_extra` rename in the library's internal code.

## Impact

These fixes:
1. Ensure compatibility with future versions of the libraries
2. Improve code quality and maintainability
3. Prepare the codebase for eventual migration to newer major versions of dependencies
4. Reduced noisy warnings in test output, making legitimate issues more visible

All tests are now passing with minimal warnings, and the code has been updated to use the recommended modern patterns from each library.
