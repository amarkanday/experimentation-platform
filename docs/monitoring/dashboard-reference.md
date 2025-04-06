# CloudWatch Dashboard Reference

This document provides a detailed reference for the CloudWatch dashboards used in the Experimentation Platform monitoring system.

## System Health Dashboard

The System Health Dashboard (`ExperimentationPlatform-SystemHealth`) provides a high-level view of system health and error rates.

![System Health Dashboard](../images/system-health-dashboard.png)

### Widgets

1. **CPU Utilization**
   - **Description**: Shows the average CPU usage percentage over time
   - **Metric**: `ExperimentationPlatform/CPUUtilization`
   - **Statistic**: Average
   - **Period**: 5 minutes

2. **Memory Utilization**
   - **Description**: Shows the average memory usage percentage over time
   - **Metric**: `ExperimentationPlatform/MemoryUtilization`
   - **Statistic**: Average
   - **Period**: 5 minutes

3. **Total Errors**
   - **Description**: Shows the total number of errors across all endpoints
   - **Metric**: `ExperimentationPlatform/ErrorCount`
   - **Statistic**: Sum
   - **Period**: 5 minutes

4. **Errors by Type**
   - **Description**: Breaks down errors by exception type
   - **Metric**: `ExperimentationPlatform/ErrorCount` with dimension `ErrorType`
   - **Statistic**: Sum
   - **Period**: 5 minutes
   - **Dimensions**:
     - `ValueError`
     - `KeyError`
     - `AttributeError`
     - `Exception` (general exceptions)

### Dashboard Definition

The dashboard is defined in `infrastructure/cloudwatch/system-health-dashboard.json` with this structure:

```json
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["ExperimentationPlatform", "CPUUtilization", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "CPU Utilization"
      }
    },
    // Additional widgets...
  ]
}
```

## API Performance Dashboard

The API Performance Dashboard (`ExperimentationPlatform-APIPerformance`) focuses on API performance metrics and latency.

![API Performance Dashboard](../images/api-performance-dashboard.png)

### Widgets

1. **API Latency by Endpoint**
   - **Description**: Shows the average request latency broken down by endpoint
   - **Metric**: `ExperimentationPlatform/RequestLatency` with dimension `Endpoint`
   - **Statistic**: Average
   - **Period**: 5 minutes
   - **Key Endpoints**:
     - `/api/v1/experiments`
     - `/api/v1/users`
     - `/api/v1/feature-flags`
     - `/api`

2. **API Latency Percentiles**
   - **Description**: Shows latency percentiles (p50, p90, p99) for all endpoints
   - **Metric**: `ExperimentationPlatform/RequestLatency`
   - **Statistics**: p50, p90, p99
   - **Period**: 5 minutes

3. **API Errors**
   - **Description**: Shows the total number of API errors
   - **Metric**: `ExperimentationPlatform/ErrorCount`
   - **Statistic**: Sum
   - **Period**: 5 minutes

4. **Resource Utilization - Maximum**
   - **Description**: Shows maximum CPU and memory usage
   - **Metrics**:
     - `ExperimentationPlatform/CPUUtilization`
     - `ExperimentationPlatform/MemoryUtilization`
   - **Statistic**: Maximum
   - **Period**: 5 minutes

### Dashboard Definition

The dashboard is defined in `infrastructure/cloudwatch/api-performance-dashboard.json` with this structure:

```json
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 24,
      "height": 6,
      "properties": {
        "metrics": [
          ["ExperimentationPlatform", "RequestLatency", "Endpoint", "/api/v1/experiments", {"stat": "Average"}],
          ["ExperimentationPlatform", "RequestLatency", "Endpoint", "/api/v1/users", {"stat": "Average"}],
          ["ExperimentationPlatform", "RequestLatency", "Endpoint", "/api/v1/feature-flags", {"stat": "Average"}],
          ["ExperimentationPlatform", "RequestLatency", "Endpoint", "/api", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "API Latency by Endpoint (ms)"
      }
    },
    // Additional widgets...
  ]
}
```

## Using the Dashboards

### Accessing Dashboards

1. Log in to the AWS Management Console
2. Navigate to CloudWatch
3. Select "Dashboards" from the left navigation
4. Select either:
   - `ExperimentationPlatform-SystemHealth`
   - `ExperimentationPlatform-APIPerformance`

### Time Range Selection

- Use the time range selector in the top-right corner
- Default: Last 3 hours
- Recommended for troubleshooting: Last 1 hour
- Recommended for trend analysis: Last 1 week

### Refreshing Data

- Auto-refresh:
  - Select the auto-refresh button
  - Choose interval (10s, 1m, 5m, 15m, 1h)
- Manual refresh: Click the refresh button

### Customizing Views

1. Click "Actions" in the top-right corner
2. Select "Add to dashboard" to add widgets to your own dashboard
3. Use "Edit" to modify the dashboard layout
4. Add "Text" widgets to include notes or information

## Creating Alarms from Dashboards

To create an alarm from a metric on the dashboard:

1. Hover over a metric line
2. Click the bell icon that appears
3. Configure the alarm threshold and notification options
4. Click "Create Alarm"

## Dashboard Management

### Deploying Updated Dashboards

If you modify the dashboard definitions, redeploy them using:

```bash
cd infrastructure/cloudwatch
./deploy-dashboards.sh
```

### Creating Custom Dashboards

1. Create a new JSON definition file in the `infrastructure/cloudwatch/` directory
2. Add the deployment logic to `deploy-dashboards.sh`
3. Run the script to deploy the new dashboard

## Best Practices

1. **Regular review**: Check dashboards daily for anomalies
2. **Baseline understanding**: Establish normal patterns for your metrics
3. **Correlating metrics**: Use multiple widgets to correlate different metrics
4. **Custom dashboards**: Create role-specific dashboards for different teams
5. **Dashboard sharing**: Share dashboard links with appropriate permissions
