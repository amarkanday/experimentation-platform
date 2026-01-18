Run code quality checks on the backend.

Execute formatting, import sorting, type checking, and linting tools.

Arguments: $ARGUMENTS (optional - "check" for dry-run, "fix" to apply changes, or specific tool name)

Available tools:
- black: Code formatting (PEP 8 compliant)
- isort: Import statement sorting
- mypy: Static type checking
- flake8: Linting and style checking

Steps to execute:

If $ARGUMENTS is "check" or empty (dry-run):
1. Activate virtual environment
2. Run black in check mode: black backend/ --check --diff
3. Run isort in check mode: isort backend/ --check-only --diff
4. Run mypy: mypy backend/app/
5. Run flake8: flake8 backend/app/
6. Report summary of issues found

If $ARGUMENTS is "fix":
1. Activate virtual environment
2. Apply black formatting: black backend/
3. Apply isort sorting: isort backend/
4. Run mypy for type checking: mypy backend/app/
5. Run flake8 for remaining issues: flake8 backend/app/
6. Report changes made and remaining issues

If $ARGUMENTS is a specific tool name (black|isort|mypy|flake8):
1. Run only that tool in fix mode
2. Report results

Quality standards:
- Black for consistent formatting
- Imports sorted by isort
- Type hints checked by mypy
- PEP 8 compliance via flake8

Example usage:
- /quality → check all quality metrics
- /quality check → same as above
- /quality fix → apply formatting and sorting fixes
- /quality black → run only black formatter
