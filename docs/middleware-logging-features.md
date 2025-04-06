# Enhanced Logging Middleware

This document describes the enhanced logging middleware features that have been implemented to improve observability, security, and debugging capabilities.

## Features Overview

1. **Sensitive Data Masking**
   - Mask email addresses, credit card numbers, passwords, tokens, etc.
   - Customizable masking for additional fields

2. **Performance Metrics Collection**
   - CPU usage tracking
   - Memory usage monitoring
   - Response time measurements

3. **Enhanced Logging**
   - HTTP request/response logging
   - Error tracking
   - Integration with CloudWatch

## Sensitive Data Masking

The masking utility (`backend/app/utils/masking.py`) provides functions to mask various types of sensitive information:

- Passwords & secrets: Fully masked with `***MASKED***`
- Email addresses: Partially masked (e.g., `us***@example.com`)
- Credit card numbers: Last 4 digits visible (e.g., `****-****-****-1111`)
- Phone numbers: Last 4 digits visible (e.g., `***-***-4567`)
- IP addresses: First octet visible (e.g., `192.***.***.**`)
- Additional fields: Configurable via environment variables

### Configuration

Set the `MASK_ADDITIONAL_FIELDS` environment variable with a comma-separated list of field names to mask additional data.

Example:
```
MASK_ADDITIONAL_FIELDS=account_number,personal_info,ssn
```

## Performance Metrics Collection

The metrics utility (`backend/app/utils/metrics.py`) provides functions to collect system performance metrics:

- Memory usage tracking (in MB)
- CPU usage monitoring (percentage)
- Ability to measure metrics over time for a specific request

### Usage

The `MetricsCollector` class provides methods to start monitoring, get metrics, and calculate changes:

```python
from backend.app.utils.metrics import MetricsCollector

# Start collecting metrics
metrics = MetricsCollector()
metrics.start()

# Your code here

# Get metrics and changes
results = metrics.get_metrics()
print(f"Memory usage: {results['memory_mb']} MB")
print(f"CPU usage: {results['cpu_percent']}%")
print(f"Memory change: {results['memory_change_mb']} MB")
```

## Middleware Integration

The logging middleware (`backend/app/middleware/logging_middleware.py`) integrates both the masking and metrics collection utilities to provide enhanced logging capabilities:

- Logs all incoming requests with masked sensitive data
- Collects performance metrics for each request
- Logs detailed error information
- Configurable via environment variables

### Configuration

- `COLLECT_REQUEST_BODY`: Set to `"true"` to include request bodies in logs (default: `"false"`)
- `MASK_ADDITIONAL_FIELDS`: Comma-separated list of additional fields to mask
- `LOG_LEVEL`: Set the logging level (default: `"INFO"`)

## Example Usage

See the example script at `docs/examples/middleware_usage_example.py` for a complete demonstration of how to use the enhanced logging middleware.

## Testing

Unit tests are provided for all new features:

- `backend/tests/unit/utils/test_masking.py`: Tests for the masking utility
- `backend/tests/unit/utils/test_metrics.py`: Tests for the metrics collection utility
- `backend/tests/unit/middleware/test_logging_middleware.py`: Tests for the enhanced logging middleware

To run the tests:

```bash
cd backend
python -m pytest tests/unit/utils/test_masking.py tests/unit/utils/test_metrics.py tests/unit/middleware/test_logging_middleware.py -v
```

## Dependencies

These features require the following dependencies (added to `requirements.txt`):

- `psutil==5.9.8`: For system metrics collection
- `pytest-asyncio==0.23.4`: For testing async code
- `pytest-mock==3.12.0`: For mocking in tests
