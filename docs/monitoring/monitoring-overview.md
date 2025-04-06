# Monitoring and Error Tracking Overview

This document provides an overview of the Experimentation Platform's monitoring and error tracking system implemented using AWS CloudWatch.

## Architecture

Our monitoring system follows a multi-layered approach:

1. **Middleware Layer**: FastAPI middleware components that capture metrics and errors
2. **AWS Integration Layer**: AWS client utilities that send data to CloudWatch
3. **Visualization Layer**: CloudWatch dashboards for real-time monitoring
4. **Alerting Layer**: CloudWatch alarms for incident response

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  API Request    │───▶│    Middleware   │───▶│ AWS CloudWatch  │
└─────────────────┘    │  • Metrics      │    │  • Logs         │
                       │  • Error        │    │  • Metrics      │
┌─────────────────┐    │  • Logging      │    │  • Dashboards   │
│  API Response   │◀───│                 │◀───│  • Alarms       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### Middleware

1. **Error Middleware** (`ErrorMiddleware`):
   - Captures all unhandled exceptions
   - Logs detailed error context (stack trace, request details)
   - Sends error metrics to CloudWatch

2. **Metrics Middleware** (`MetricsMiddleware`):
   - Captures request latency
   - Tracks CPU and memory usage
   - Sends performance metrics to CloudWatch

3. **Request Logging Middleware** (`RequestLoggingMiddleware`):
   - Logs incoming requests with masked sensitive data
   - Records request method, path, status code, and duration

### AWS Client Utility

The `AWSClient` class in `app/utils/aws_client.py` provides a standardized way to:
- Initialize CloudWatch clients with proper error handling
- Send metrics to CloudWatch
- Support different AWS profiles and regions

### CloudWatch Dashboards

Two pre-configured dashboards visualize key metrics:

1. **System Health Dashboard**:
   - CPU and memory utilization
   - Error counts (total and by type)

2. **API Performance Dashboard**:
   - Request latency by endpoint
   - Latency percentiles (p50, p90, p99)
   - Error counts
   - Resource utilization

## Data Flow

1. A request arrives at the FastAPI application
2. The MetricsMiddleware records the start time and initial resource usage
3. The request is processed by the application
4. If an error occurs, ErrorMiddleware captures it, logs details, and sends metrics
5. After processing, MetricsMiddleware records final resource usage and calculates metrics
6. All middleware components send their data to CloudWatch through the AWSClient utility
7. CloudWatch dashboards display the metrics in real-time

## Environment Variables

The monitoring system can be configured with these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for CloudWatch | `us-west-2` |
| `AWS_PROFILE` | AWS profile for credentials | `experimentation-platform` |
| `COLLECT_REQUEST_BODY` | Whether to include request bodies in error logs | `false` |

## Metrics Collected

### Performance Metrics

| Metric | Description | Unit |
|--------|-------------|------|
| `RequestLatency` | Time to process a request | Milliseconds |
| `CPUUtilization` | CPU usage percentage | Percent |
| `MemoryUtilization` | Memory usage percentage | Percent |
| `CPUChange` | Change in CPU usage during request | Percent |
| `MemoryChange` | Change in memory usage during request | Megabytes |

### Error Metrics

| Metric | Description | Dimensions |
|--------|-------------|------------|
| `ErrorCount` | Count of errors | None (total) |
| `ErrorCount` | Count of errors by type | `ErrorType` |
| `ErrorCount` | Count of errors by endpoint | `Endpoint` |

## Implementation Details

The monitoring system is integrated into the FastAPI application in `app/main.py`:

```python
# Add performance metrics middleware (should be first to get accurate measurements)
application.add_middleware(
    MetricsMiddleware,
    aws_region=os.environ.get("AWS_REGION", "us-west-2"),
    aws_profile=os.environ.get("AWS_PROFILE", "experimentation-platform")
)

# Add error tracking middleware (should be last to catch all errors)
application.add_middleware(
    ErrorMiddleware,
    aws_region=os.environ.get("AWS_REGION", "us-west-2"),
    aws_profile=os.environ.get("AWS_PROFILE", "experimentation-platform")
)
```

See the [Setup Guide](setup-guide.md) and [Dashboard Reference](dashboard-reference.md) for more details.
