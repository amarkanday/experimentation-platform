# Safety Monitoring API

The Safety Monitoring API provides a way to monitor feature flags for safety concerns and automatically roll back flags when issues are detected.

## Overview

The safety monitoring system includes:

1. Global safety settings for the platform
2. Feature flag-specific safety configurations
3. Safety checks for feature flags
4. Rollback functionality for feature flags
5. Record keeping of rollback events

## API Endpoints

### Global Safety Settings

- `GET /api/v1/safety/settings` - Get global safety settings
- `POST /api/v1/safety/settings` - Update global safety settings (superuser only)

### Feature Flag Safety Configuration

- `GET /api/v1/safety/feature-flags/{feature_flag_id}/config` - Get safety configuration for a feature flag
- `POST /api/v1/safety/feature-flags/{feature_flag_id}/config` - Update safety configuration for a feature flag (superuser only)

### Safety Checks

- `GET /api/v1/safety/feature-flags/{feature_flag_id}/check` - Check safety status of a feature flag

### Rollback Operations

- `POST /api/v1/safety/feature-flags/{feature_flag_id}/rollback` - Roll back a feature flag to a safe state (superuser only)

## Data Models

### Safety Settings

Global settings for safety monitoring:

```json
{
  "enable_automatic_rollbacks": false,
  "default_metrics": {
    "error_rate": {
      "warning_threshold": 0.05,
      "critical_threshold": 0.1,
      "comparison_type": "greater_than"
    },
    "latency": {
      "warning_threshold": 150,
      "critical_threshold": 300,
      "comparison_type": "greater_than"
    }
  }
}
```

### Feature Flag Safety Configuration

Configuration specific to a feature flag:

```json
{
  "feature_flag_id": "uuid",
  "enabled": true,
  "metrics": {
    "error_rate": {
      "warning_threshold": 0.05,
      "critical_threshold": 0.1,
      "comparison_type": "greater_than"
    }
  },
  "rollback_percentage": 0
}
```

### Safety Check Response

Response from a safety check:

```json
{
  "feature_flag_id": "uuid",
  "overall_status": "healthy",
  "metrics": {
    "error_rate": {
      "value": 0.03,
      "status": "healthy",
      "threshold": {
        "warning_threshold": 0.05,
        "critical_threshold": 0.1,
        "comparison_type": "greater_than"
      }
    }
  },
  "timestamp": "2023-12-01T12:00:00Z"
}
```

## Health Status Values

The health status of a feature flag can be one of the following:

- `healthy` - No issues detected
- `warning` - Warning threshold exceeded but not critical
- `critical` - Critical threshold exceeded
- `unknown` - Unable to determine health status

## Rollback Operations

Rollbacks can be triggered:

1. Manually via the API
2. Automatically by the safety monitoring system (if enabled)
3. Through scheduled rollbacks

When a rollback occurs, the system:

1. Reduces the rollout percentage to the specified value (default 0%)
2. Creates a rollback record with details about the operation
3. Logs the event for future reference

## Security

All endpoints require authentication. Updates to settings and rollback operations require superuser privileges.
