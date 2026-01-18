Run backend tests with proper environment setup.

Run pytest tests for the backend with all necessary environment configuration.

Arguments: $ARGUMENTS (optional - specific test path or pytest flags)

Steps to execute:
1. Activate the virtual environment at /Users/ashishmarkanday/github/experimentation-platform/venv
2. Set required environment variables: APP_ENV=test and TESTING=true
3. Run pytest with the provided arguments, or all backend tests if no args provided
4. Use verbose output (-v) and short traceback (--tb=short) for clear results
5. Report results clearly including pass/fail counts and any errors

Default behavior (no arguments): Run all backend unit tests
With arguments: Run specific tests or apply specific pytest flags

Examples:
- /test-backend → runs all backend tests
- /test-backend backend/tests/unit/services/test_audit_service.py → runs specific file
- /test-backend backend/tests/unit/ -k "test_feature" → runs tests matching pattern
- /test-backend -m "unit" → runs tests with "unit" marker
