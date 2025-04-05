# CloudWatch Logging Setup

## Overview
This document outlines the setup and configuration of CloudWatch logging for the experimentation platform.

## Prerequisites
1. AWS account with appropriate permissions
2. AWS CLI installed and configured
3. Required environment variables:
   ```bash
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=your_region
   APP_ENV=development|staging|production
   ```

## Log Group Structure
```
/experimentation-platform/
├── development/
│   ├── api/
│   │   ├── requests
│   │   ├── responses
│   │   └── errors
│   ├── application/
│   │   ├── info
│   │   ├── warning
│   │   └── error
│   └── audit/
├── staging/
│   └── [similar structure]
└── production/
    └── [similar structure]
```

## Retention Policies
- API logs: 30 days
- Application logs: 60 days
- Error logs: 90 days
- Audit logs: 1 year

## Setup Instructions

### 1. Configure AWS CLI
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your preferred region (e.g., us-east-1)
# Enter your preferred output format (json)
```

### 2. Create Log Groups
```bash
# Development environment
aws logs create-log-group --log-group-name /experimentation-platform/development
aws logs put-retention-policy --log-group-name /experimentation-platform/development --retention-in-days 30

# Staging environment
aws logs create-log-group --log-group-name /experimentation-platform/staging
aws logs put-retention-policy --log-group-name /experimentation-platform/staging --retention-in-days 30

# Production environment
aws logs create-log-group --log-group-name /experimentation-platform/production
aws logs put-retention-policy --log-group-name /experimentation-platform/production --retention-in-days 30
```

### 3. Configure Application
1. Add required dependencies:
   ```bash
   pip install watchtower boto3
   ```

2. Environment variables in `.env`:
   ```bash
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=your_region
   APP_ENV=development
   ```

## Log Subscription Filters

### Error Tracking
```bash
aws logs put-subscription-filter \
    --log-group-name /experimentation-platform/production \
    --filter-name error-filter \
    --filter-pattern '[timestamp, level="ERROR", ...]' \
    --destination-arn your-lambda-arn
```

### Performance Monitoring
```bash
aws logs put-subscription-filter \
    --log-group-name /experimentation-platform/production \
    --filter-name performance-filter \
    --filter-pattern '[timestamp, duration_ms>1000, ...]' \
    --destination-arn your-lambda-arn
```

### Security Events
```bash
aws logs put-subscription-filter \
    --log-group-name /experimentation-platform/production \
    --filter-name security-filter \
    --filter-pattern '[timestamp, level in ["WARNING", "ERROR"], message contains "security", ...]' \
    --destination-arn your-lambda-arn
```

## Monitoring and Alerts

### CloudWatch Metrics
The following metrics are automatically created:
- Log volume by group/stream
- Error rate
- Response time distribution
- API request volume

### CloudWatch Alarms
Example alarm configuration:
```bash
aws cloudwatch put-metric-alarm \
    --alarm-name high-error-rate \
    --metric-name ErrorCount \
    --namespace ExperimentationPlatform \
    --statistic Sum \
    --period 300 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions your-sns-topic-arn
```

## Troubleshooting

### Common Issues

1. Invalid Credentials
```
UnrecognizedClientException: The security token included in the request is invalid
```
Solution: Check AWS credentials in environment variables or `~/.aws/credentials`

2. Missing Permissions
```
AccessDeniedException: User is not authorized to perform logs:CreateLogGroup
```
Solution: Ensure IAM role has correct CloudWatch Logs permissions

3. Log Delivery Issues
```
Failed to deliver logs to CloudWatch: RequestError
```
Solution:
- Check network connectivity
- Verify AWS region configuration
- Ensure batch settings are appropriate

### Verification
To verify logging is working:
1. Generate test logs in application
2. Check CloudWatch Logs console
3. Verify log format and fields
4. Test subscription filters
5. Confirm metrics are being generated

## Cost Optimization
1. Use appropriate retention periods
2. Implement log filtering at source
3. Use batch processing for log delivery
4. Monitor and adjust based on usage patterns

## Security Considerations
1. Use IAM roles with minimal required permissions
2. Encrypt sensitive log data
3. Regularly audit log access
4. Implement log sanitization

## Maintenance
1. Regularly review and update retention policies
2. Monitor log volume and costs
3. Update subscription filters as needed
4. Review and adjust alerting thresholds
