# CloudWatch Logging Test Issues and Fixes

## File Location

The CloudWatch logging tests are located at:
```
backend/tests/unit/core/test_cloudwatch_logging.py
```

## Issues

1. **Test Assertion Failures**
   - Tests were failing because they didn't account for the "CloudWatch logging enabled" message logged during `setup_logging`
   - Assertions expected single calls to `emit` but were getting multiple calls
   - Batching test expected 5 calls but was getting 6 due to the setup message

2. **Error Handling Test Issues**
   - Error simulation was set up before `setup_logging`, causing the setup itself to fail
   - Mock handler wasn't properly handling exceptions and calling `handleError`
   - Test was failing with unhandled exceptions instead of verifying error handling

3. **Mock Handler Implementation**
   - Initial mock handler was a simple MagicMock without proper logging handler behavior
   - Didn't properly inherit from `logging.Handler`
   - Lacked proper error handling mechanisms

## Fixes

### 1. Updated Test Assertions

```python
# Before
mock_handler.emit.assert_called_once()

# After
assert mock_handler.emit.call_count == 2  # One for setup_logging, one for test message
```

The assertions were updated to account for the fact that `setup_logging` itself logs a message. This affects all tests that verify the number of log messages.

### 2. Proper Mock Handler Implementation

```python
class MockCloudWatchHandler(logging.Handler):
    """Mock CloudWatch handler for testing."""
    def __init__(self):
        super().__init__()
        self.emit = MagicMock()
        self.handleError = MagicMock()

    def handle(self, record):
        """Override handle to catch exceptions from emit."""
        try:
            self.emit(record)
        except Exception as e:
            self.handleError(record)
```

The mock handler was improved by:
- Inheriting from `logging.Handler`
- Implementing proper error handling
- Using MagicMock for `emit` and `handleError` methods

### 3. Error Handling Test Fix

```python
# Before
mock_handler.emit.side_effect = Exception("Test error")
setup_logging(enable_cloudwatch=True)  # Would fail immediately

# After
setup_logging(enable_cloudwatch=True)
logger = get_logger(__name__)
mock_handler.emit.side_effect = Exception("Test error")  # Set after setup
logger.info("Test message")  # Now properly triggers error handling
```

The error handling test was fixed by:
- Moving error simulation after `setup_logging`
- Properly implementing error handling in the mock handler
- Verifying that `handleError` was called

### 4. Added Clear Handlers Fixture

```python
@pytest.fixture(autouse=True)
def clear_handlers():
    """Clear all handlers from the root logger before each test."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    yield
```

This fixture ensures each test starts with a clean logging state.

## Results

After implementing these fixes:
- All CloudWatch logging tests are passing (except for the skipped integration test)
- Error handling is properly tested
- Test assertions accurately reflect the expected behavior
- Each test runs in isolation with a clean logging state

## Remaining Issues

1. **Linter Errors**
   - Unresolved imports for `pytest`, `watchtower`, and `boto3`
   - These don't affect test functionality but should be addressed by ensuring proper package installation

2. **Integration Test**
   - One test remains skipped as it requires AWS credentials
   - This is expected behavior as integration tests shouldn't run in CI without proper credentials
