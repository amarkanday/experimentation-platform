# Monitoring System Setup Guide

This guide provides detailed instructions for setting up the monitoring and error tracking system for the Experimentation Platform.

## Prerequisites

- AWS CLI installed and configured
- AWS account with appropriate permissions
- Python 3.9+ environment

## Initial Setup

### 1. Install Required Dependencies

Add the monitoring dependencies to your environment:

```bash
pip install -r backend/requirements-monitoring.txt
```

The key dependencies include:

```
boto3==1.28.0
botocore==1.31.0
psutil==5.9.5
python-json-logger==2.0.7
```

### 2. Create CloudWatch Log Groups

Set up the required log groups in CloudWatch:

```bash
# Create log groups
aws logs create-log-group --log-group-name /experimentation-platform/api --profile experimentation-platform --region us-west-2
aws logs create-log-group --log-group-name /experimentation-platform/services --profile experimentation-platform --region us-west-2
aws logs create-log-group --log-group-name /experimentation-platform/errors --profile experimentation-platform --region us-west-2

# Set retention policies (optional but recommended)
aws logs put-retention-policy --log-group-name /experimentation-platform/api --retention-in-days 30 --profile experimentation-platform --region us-west-2
aws logs put-retention-policy --log-group-name /experimentation-platform/services --retention-in-days 30 --profile experimentation-platform --region us-west-2
aws logs put-retention-policy --log-group-name /experimentation-platform/errors --retention-in-days 30 --profile experimentation-platform --region us-west-2
```

### 3. Deploy CloudWatch Dashboards

Deploy the pre-configured dashboards:

```bash
cd infrastructure/cloudwatch
chmod +x deploy-dashboards.sh
./deploy-dashboards.sh
```

This script deploys two dashboards:
- `ExperimentationPlatform-SystemHealth`
- `ExperimentationPlatform-APIPerformance`

## Configuration

### Environment Variables

Configure the monitoring system with these environment variables:

```bash
# AWS Configuration
export AWS_REGION=us-west-2  # Set your preferred region
export AWS_PROFILE=experimentation-platform  # Set your AWS profile

# Monitoring Options
export COLLECT_REQUEST_BODY=false  # Set to true to include request bodies in error logs
```

For production deployments, set these variables in your deployment environment (e.g., ECS Task Definitions, Lambda environment variables).

### IAM Permissions

The AWS user or role used by the application needs these CloudWatch permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/experimentation-platform/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:GetDashboard",
        "cloudwatch:PutDashboard"
      ],
      "Resource": "*"
    }
  ]
}
```

## Integration with FastAPI

The monitoring middleware should already be integrated in `app/main.py`. If you need to add it manually:

```python
from app.middleware.error_middleware import ErrorMiddleware
from app.middleware.metrics_middleware import MetricsMiddleware

# Add performance metrics middleware (should be first to get accurate measurements)
app.add_middleware(
    MetricsMiddleware,
    aws_region=os.environ.get("AWS_REGION", "us-west-2"),
    aws_profile=os.environ.get("AWS_PROFILE", "experimentation-platform")
)

# Add error tracking middleware (should be last to catch all errors)
app.add_middleware(
    ErrorMiddleware,
    aws_region=os.environ.get("AWS_REGION", "us-west-2"),
    aws_profile=os.environ.get("AWS_PROFILE", "experimentation-platform")
)
```

## Verification

### Verify CloudWatch Dashboards

Confirm that the dashboards were created successfully:

```bash
aws cloudwatch list-dashboards --profile experimentation-platform --region us-west-2
```

You should see both dashboards in the output:

```json
{
  "DashboardEntries": [
    {
      "DashboardName": "ExperimentationPlatform-APIPerformance",
      "DashboardArn": "arn:aws:cloudwatch::ACCOUNT_ID:dashboard/ExperimentationPlatform-APIPerformance",
      "LastModified": "TIMESTAMP",
      "Size": 1427
    },
    {
      "DashboardName": "ExperimentationPlatform-SystemHealth",
      "DashboardArn": "arn:aws:cloudwatch::ACCOUNT_ID:dashboard/ExperimentationPlatform-SystemHealth",
      "LastModified": "TIMESTAMP",
      "Size": 1179
    }
  ]
}
```

### Verify Metrics Collection

1. Start the application
2. Make several API requests
3. Check the CloudWatch console for metrics
4. Verify that metrics appear in the "ExperimentationPlatform" namespace

### Verify Error Tracking

1. Trigger an error (e.g., request a non-existent resource)
2. Check the CloudWatch Logs console for the `/experimentation-platform/errors` log group
3. Verify that error details were logged correctly

## Troubleshooting

### No Metrics in CloudWatch

1. Check AWS credentials and permissions
2. Verify AWS region configuration
3. Check application logs for AWS client initialization errors
4. Ensure the middleware is properly registered in the FastAPI app

### Dashboard Not Showing Data

1. Verify the correct AWS region in the dashboard
2. Check that metrics are being published to the correct namespace
3. Adjust the time range in the CloudWatch console

### Error Logs Not Appearing

1. Verify the log group exists
2. Check application logs for errors during log publishing
3. Ensure the ErrorMiddleware is registered correctly

## Next Steps

- [Set up CloudWatch Alarms](../alerts/cloudwatch-alarms.md) for proactive monitoring
- Configure [Log Insights queries](log-insights-queries.md) for analysis
- Integrate with [AWS X-Ray](../tracing/xray-integration.md) for distributed tracing
