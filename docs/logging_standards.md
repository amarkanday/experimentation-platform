# Logging Standards and Best Practices

## Overview
This document outlines the logging standards and best practices for the experimentation platform. All logs are structured in JSON format for better searchability and analysis, and are delivered to CloudWatch for centralized management.

## Log Format

### Required Fields
- `timestamp`: ISO 8601 formatted UTC timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `message`: Human-readable log message
- `logger`: Name of the logger
- `file`: Source file name
- `line`: Line number in source file
- `function`: Function name where log was called

### Optional Context Fields
- `correlation_id`: Unique identifier for tracking related logs
- `user_id`: ID of the user associated with the log
- `session_id`: Session identifier
- `process`: Process ID
- `thread`: Thread ID

## Log Levels

### DEBUG
- Detailed information for debugging
- Example: "Processing request with parameters: {...}"
- Use for development and troubleshooting

### INFO
- General operational information
- Example: "User logged in successfully"
- Use for normal operation events

### WARNING
- Warning conditions that don't affect normal operation
- Example: "Cache miss for key: {...}"
- Use for potential issues that don't require immediate action

### ERROR
- Error conditions that affect normal operation
- Example: "Failed to connect to database"
- Use for issues that need attention but don't stop the application

### CRITICAL
- Critical conditions that may stop the application
- Example: "Database connection lost"
- Use for issues that require immediate attention

## Best Practices

### 1. Context
- Always include relevant context in logs
- Use the `LogContext` class for adding context:
```python
with LogContext(logger, user_id="123", session_id="abc"):
    logger.info("User action completed")
```

### 2. Error Logging
- Include stack traces for errors
- Add relevant context (user ID, request ID, etc.)
- Example:
```python
try:
    # Code that might fail
except Exception as e:
    logger.error("Operation failed", exc_info=True, extra={
        "operation": "user_update",
        "user_id": user_id
    })
```

### 3. Performance Logging
- Log timing information for performance-critical operations
- Example:
```python
start_time = time.time()
# Operation
logger.info("Operation completed", extra={
    "duration_ms": (time.time() - start_time) * 1000
})
```

### 4. Security
- Never log sensitive information (passwords, tokens, etc.)
- Mask or redact sensitive data in logs
- Example:
```python
logger.info("User authenticated", extra={
    "user_id": user_id,
    "masked_token": token[:4] + "..." + token[-4:]
})
```

### 5. Searchability
- Use consistent field names
- Include relevant identifiers (user_id, request_id, etc.)
- Structure log messages for easy filtering

## Log Rotation
- Log files are rotated when they reach 10MB
- Up to 5 backup files are kept
- Oldest files are deleted when rotation limit is reached

## Monitoring and Alerts
- Error logs are monitored for anomalies
- Critical errors trigger alerts
- Log volume and patterns are analyzed for trends

## Tools and Integration

### CloudWatch Integration
All logs are automatically sent to AWS CloudWatch with the following structure:
- Log Group: `/experimentation-platform/{environment}`
- Log Streams: Organized by date (YYYY/MM/DD)
- Retention: Varies by log type (30-365 days)

#### Log Delivery
- Logs are batched (100 logs or 5 seconds)
- Automatic retry on delivery failure
- Asynchronous delivery to minimize impact

#### Environment-specific Configuration
```python
# Enable CloudWatch logging
setup_logging(
    log_level="INFO",
    enable_cloudwatch=True  # Defaults to True if AWS credentials are available
)
```

#### Required Environment Variables
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
APP_ENV=development|staging|production
```

For detailed CloudWatch setup and configuration, see [CloudWatch Setup Guide](infrastructure/cloudwatch-setup.md).

## Examples

### Basic Logging
```python
logger = get_logger(__name__)
logger.info("Operation started", extra={
    "operation": "user_update",
    "user_id": "123"
})
```

### Error Logging
```python
try:
    # Operation that might fail
except Exception as e:
    logger.error("Operation failed", exc_info=True, extra={
        "operation": "user_update",
        "user_id": "123",
        "error": str(e)
    })
```

### Contextual Logging
```python
with LogContext(logger, user_id="123", session_id="abc"):
    logger.info("User action started")
    # Operation
    logger.info("User action completed")
```
