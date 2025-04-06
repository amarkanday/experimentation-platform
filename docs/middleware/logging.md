# Logging Middleware Documentation

## Overview

The logging middleware provides comprehensive request/response logging with performance metrics collection, sensitive data masking, and request correlation. It ensures all API interactions are properly logged and monitored while protecting sensitive information.

## Features

### 1. Request/Response Logging

All HTTP requests and responses are automatically logged with detailed information:

**Request Details:**
- HTTP method
- URL path
- Query parameters
- Headers
- Client IP
- Request body (for POST/PUT/PATCH)

**Response Details:**
- Status code
- Response headers
- Content type
- Processing time

### 2. Request Correlation

Each request is assigned a unique correlation ID that is:
- Included in all log entries related to the request
- Added to response headers as `X-Request-ID`
- Available in the request context for application code

This enables easy tracking of request flows through the system.

### 3. Performance Metrics

The middleware collects detailed performance metrics for each request:

- Request processing time (milliseconds)
- Memory usage (MB)
  - Memory change during request
  - Total memory usage
- CPU usage percentage

These metrics are:
- Logged with each request
- Added to response headers (processing time)
- Available for monitoring and alerting

### 4. Sensitive Data Masking

The middleware automatically masks sensitive information in logs:

**Fully Masked Fields:**
- Passwords
- Tokens (all types)
- API keys
- Credit card numbers
- Social security numbers
- Private keys

**Partially Masked Fields:**
- Email addresses (show first 2 chars + domain)
- Phone numbers (show last 4 digits)
- IP addresses (show first octet)

### 5. Error Handling

For failed requests, the middleware:
- Logs full error details with stack traces
- Includes performance metrics at point of failure
- Maintains request correlation
- Preserves sensitive data masking

## Configuration

The middleware is enabled by default and requires no additional configuration. However, you can customize its behavior through environment variables:

```env
LOG_LEVEL=INFO                    # Logging level (DEBUG, INFO, WARNING, ERROR)
MASK_ADDITIONAL_FIELDS=field1,field2  # Additional fields to mask
COLLECT_REQUEST_BODY=true        # Whether to collect request bodies
```

## Example Log Output

Successful request:
```json
{
  "timestamp": "2024-03-20T10:30:45.123Z",
  "level": "INFO",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "request": {
    "method": "POST",
    "path": "/api/users",
    "headers": {
      "content-type": "application/json",
      "authorization": "***MASKED***"
    },
    "body": {
      "email": "jo***@example.com",
      "password": "***MASKED***"
    }
  },
  "response": {
    "status_code": 201,
    "content_type": "application/json"
  },
  "metrics": {
    "request_time_ms": 45.23,
    "memory_usage_mb": 2.5,
    "total_memory_mb": 156.7,
    "cpu_percent": 12.4
  }
}
```

Failed request:
```json
{
  "timestamp": "2024-03-20T10:31:12.456Z",
  "level": "ERROR",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
  "request": {
    "method": "GET",
    "path": "/api/products/123",
    "client": "192.***"
  },
  "error": "Product not found",
  "metrics": {
    "request_time_ms": 12.34,
    "memory_usage_mb": 1.2,
    "total_memory_mb": 157.9,
    "cpu_percent": 8.6
  }
}
```

## Best Practices

1. **Correlation ID Usage**
   - Pass the correlation ID in requests between services
   - Include it in error responses to clients
   - Reference it in support tickets/bug reports

2. **Sensitive Data**
   - Regularly review and update masked fields
   - Never log sensitive data in application code
   - Use appropriate log levels

3. **Performance Monitoring**
   - Set up alerts for high processing times
   - Monitor memory usage trends
   - Track CPU usage patterns

4. **Log Management**
   - Implement log rotation
   - Set up log aggregation
   - Configure appropriate retention periods

## Troubleshooting

Common issues and solutions:

1. **Missing Logs**
   - Check LOG_LEVEL setting
   - Verify logger configuration
   - Check disk space

2. **Performance Impact**
   - Adjust logging detail level
   - Review masked fields configuration
   - Monitor resource usage

3. **Sensitive Data Exposure**
   - Update MASK_ADDITIONAL_FIELDS
   - Review custom logging code
   - Check log access permissions
