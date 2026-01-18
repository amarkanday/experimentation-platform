Standardize and verify metrics model imports across the codebase.

Check and fix inconsistent import paths for metrics models to prevent SQLAlchemy mapping errors.

Arguments: $ARGUMENTS (optional - "check" to only verify, "fix" to apply fixes)

Background:
Inconsistent import paths (e.g., `from app.models.metrics...` vs `from backend.app.models.metrics...`) cause Python to treat classes as distinct, resulting in:
- Memory duplication
- SQLAlchemy "Class is not mapped" errors
- Type checking failures
- Unexpected runtime behavior

Steps to execute:
1. If $ARGUMENTS is "check" or empty: Run verification only
   - Execute: python standardize_metrics_imports.py --check
   - Report any inconsistencies found
   - Show files that need fixes

2. If $ARGUMENTS is "fix": Apply corrections
   - Execute: python standardize_metrics_imports.py
   - Review changes made
   - Run verification tests: python -m pytest backend/tests/unit/metrics/test_metrics_imports.py -v

3. Summarize results:
   - Number of files checked
   - Number of imports standardized
   - Verification test status

Standard import pattern (always use):
```python
from backend.app.models.metrics.metric import RawMetric, MetricType
```

Never use:
- Relative imports: `from app.models.metrics...`
- Re-exports from __init__.py files

Example usage:
- /fix-imports → check for issues
- /fix-imports check → same as above
- /fix-imports fix → apply fixes and verify
