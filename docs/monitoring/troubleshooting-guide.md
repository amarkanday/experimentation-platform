# Monitoring System Troubleshooting Guide

This guide provides solutions to common issues with the Experimentation Platform's monitoring and error tracking system.

## Common Issues

### No Metrics in CloudWatch

**Symptoms:**
- CloudWatch dashboards show no data
- No metrics appear in the CloudWatch Metrics console

**Possible Causes:**
1. AWS credentials or permissions issues
2. Incorrect AWS region configuration
3. Middleware not properly registered
4. Networking issues preventing connections to AWS

**Solutions:**

1. **Verify AWS Credentials**
   ```bash
   # Test AWS CLI access
   aws cloudwatch list-dashboards --region us-west-2 --profile experimentation-platform
   ```

   If this fails, check:
   - AWS credentials in `~/.aws/credentials`
   - Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
   - IAM role attached to EC2/ECS instances

2. **Check Permissions**
   Ensure the IAM role or user has these permissions:
   ```json
   {
     "Action": [
       "cloudwatch:PutMetricData",
       "logs:CreateLogStream",
       "logs:PutLogEvents"
     ],
     "Effect": "Allow",
     "Resource": "*"
   }
   ```

3. **Verify Middleware Registration**
   Check `app/main.py` to ensure the middleware is registered:
   ```python
   app.add_middleware(
       MetricsMiddleware,
       aws_region=os.environ.get("AWS_REGION", "us-west-2"),
       aws_profile=os.environ.get("AWS_PROFILE", "experimentation-platform")
   )
   ```

4. **Check Network Configuration**
   - Ensure outbound access to CloudWatch endpoints (`monitoring.us-west-2.amazonaws.com`)
   - Check VPC endpoints if running in a private subnet
   - Test connectivity:
     ```bash
     curl -v https://monitoring.us-west-2.amazonaws.com
     ```

5. **Examine Application Logs**
   Look for errors related to CloudWatch client initialization:
   ```
   Failed to initialize CloudWatch Metrics client: ...
   ```

### Error Logs Not Appearing

**Symptoms:**
- No logs in the `/experimentation-platform/errors` log group
- Error tracking not working despite errors occurring

**Possible Causes:**
1. Log group doesn't exist
2. Insufficient permissions
3. ErrorMiddleware not registered correctly
4. Exceptions being caught before reaching middleware

**Solutions:**

1. **Create Log Group Manually**
   ```bash
   aws logs create-log-group --log-group-name /experimentation-platform/errors --region us-west-2 --profile experimentation-platform
   ```

2. **Check Permissions**
   Ensure permissions for log creation and writing:
   ```json
   {
     "Action": [
       "logs:CreateLogGroup",
       "logs:CreateLogStream",
       "logs:PutLogEvents"
     ],
     "Effect": "Allow",
     "Resource": "arn:aws:logs:*:*:log-group:/experimentation-platform/*"
   }
   ```

3. **Verify Middleware Order**
   The ErrorMiddleware should be registered last to catch all exceptions:
   ```python
   # Other middleware...

   # Error middleware should be last
   app.add_middleware(
       ErrorMiddleware,
       aws_region=os.environ.get("AWS_REGION", "us-west-2"),
       aws_profile=os.environ.get("AWS_PROFILE", "experimentation-platform")
   )
   ```

4. **Test with Deliberate Error**
   Create an endpoint that raises an exception:
   ```python
   @app.get("/test-error")
   async def test_error():
       raise ValueError("Test error for monitoring")
   ```

   Access this endpoint and check logs.

### Incorrect Metrics Data

**Symptoms:**
- Metrics appear but values are incorrect
- CPU or memory usage data doesn't match actual usage

**Possible Causes:**
1. Issues with `psutil` library
2. Containerization affecting resource measurements
3. Incorrect calculation in middleware

**Solutions:**

1. **Update psutil**
   ```bash
   pip install --upgrade psutil==5.9.5
   ```

2. **Container Adjustments**
   For containerized environments, set resource limits explicitly and use container-aware metrics:
   ```python
   # In metrics.py
   def get_memory_usage():
       try:
           # For containerized environments, read cgroup limits
           with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'r') as f:
               mem_limit = int(f.read().strip())
           with open('/sys/fs/cgroup/memory/memory.usage_in_bytes', 'r') as f:
               mem_usage = int(f.read().strip())
           return (mem_usage / mem_limit) * 100
       except:
           # Fall back to psutil
           return psutil.virtual_memory().percent
   ```

3. **Verify Calculation Logic**
   Review the calculation logic in `app/middleware/metrics_middleware.py`:
   ```python
   # Check calculation steps
   memory_change = end_memory - start_memory if end_memory and start_memory else 0
   ```

### Dashboard Deployment Failures

**Symptoms:**
- `deploy-dashboards.sh` script fails
- Dashboards don't appear in CloudWatch console

**Possible Causes:**
1. Script permissions
2. Invalid dashboard JSON
3. AWS CLI not installed or configured

**Solutions:**

1. **Check Script Permissions**
   ```bash
   chmod +x infrastructure/cloudwatch/deploy-dashboards.sh
   ```

2. **Validate Dashboard JSON**
   ```bash
   # For system health dashboard
   cat infrastructure/cloudwatch/system-health-dashboard.json | python -m json.tool

   # For API performance dashboard
   cat infrastructure/cloudwatch/api-performance-dashboard.json | python -m json.tool
   ```

   Fix any JSON syntax errors.

3. **Run Script with Debug**
   ```bash
   bash -x infrastructure/cloudwatch/deploy-dashboards.sh
   ```

   This shows each command as it executes.

### Connection Timeout Issues

**Symptoms:**
- Slow application performance
- Logs showing AWS client timeout errors

**Possible Causes:**
1. Network latency to AWS
2. DNS resolution issues
3. Connection pool exhaustion

**Solutions:**

1. **Increase Timeout**
   Modify `app/utils/aws_client.py`:
   ```python
   # Increase timeout for client creation
   client = boto3.client('cloudwatch',
                        region_name=region,
                        config=boto3.config.Config(connect_timeout=5, retries={'max_attempts': 3}))
   ```

2. **Implement Background Processing**
   Send metrics asynchronously to avoid blocking requests:
   ```python
   # In metrics_middleware.py
   import threading

   def _send_metrics_async(self, *args, **kwargs):
       thread = threading.Thread(target=self._send_metrics, args=args, kwargs=kwargs)
       thread.daemon = True
       thread.start()
   ```

### High CPU Usage from Monitoring

**Symptoms:**
- Monitoring components consuming excessive CPU
- Performance degradation when monitoring is enabled

**Possible Causes:**
1. Too frequent metric collection
2. Inefficient resource usage calculations
3. Sending too many metrics

**Solutions:**

1. **Reduce Sampling Rate**
   Only collect metrics for a subset of requests:
   ```python
   # In metrics_middleware.py
   import random

   async def dispatch(self, request, call_next):
       # Only sample 10% of requests for detailed metrics
       collect_detailed_metrics = random.random() < 0.1

       # Always collect timing, but only sometimes collect resource metrics
       start_time = time.time()
       if collect_detailed_metrics:
           start_cpu = get_cpu_usage()
           start_memory = get_memory_usage()
       else:
           start_cpu = None
           start_memory = None

       # Process request...
   ```

2. **Optimize Resource Calculations**
   Cache resource calculations:
   ```python
   # In metrics.py
   _last_cpu_check = 0
   _cached_cpu_value = 0
   _CPU_CACHE_TTL = 5  # seconds

   def get_cpu_usage():
       global _last_cpu_check, _cached_cpu_value
       now = time.time()

       # Return cached value if recent
       if now - _last_cpu_check < _CPU_CACHE_TTL:
           return _cached_cpu_value

       # Calculate new value
       try:
           _cached_cpu_value = psutil.cpu_percent(interval=None)
           _last_cpu_check = now
           return _cached_cpu_value
       except Exception as e:
           logger.warning(f"Failed to get CPU metrics: {str(e)}")
           return 0
   ```

## Debugging Tools

### Local Metric Testing

Test CloudWatch metric publishing locally:

```python
# test_metrics.py
from app.utils.aws_client import AWSClient

def test_metrics():
    client = AWSClient.get_cloudwatch_metrics_client(
        region_name="us-west-2",
        profile_name="experimentation-platform"
    )

    result = AWSClient.put_metric_data(
        client=client,
        namespace="ExperimentationPlatform",
        metric_name="TestMetric",
        value=100.0,
        unit="Count"
    )

    print(f"Metric sent: {result}")

if __name__ == "__main__":
    test_metrics()
```

Run with:
```bash
python test_metrics.py
```

### Error Middleware Testing

Test error capture and logging:

```python
# test_error_middleware.py
import asyncio
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.middleware.error_middleware import ErrorMiddleware

app = FastAPI()

@app.get("/test-error")
async def test_error():
    raise ValueError("Test error for middleware")

# Add middleware
app.add_middleware(
    ErrorMiddleware,
    aws_region="us-west-2",
    aws_profile="experimentation-platform"
)

client = TestClient(app)
response = client.get("/test-error")
print(f"Response status: {response.status_code}")
```

Run with:
```bash
python test_error_middleware.py
```

## Advanced Troubleshooting

### Checking CloudWatch API Calls

Use AWS CloudTrail to inspect API calls:

1. Go to AWS CloudTrail console
2. Create a trail if one doesn't exist
3. View "Event history"
4. Filter for:
   - Event source: `cloudwatch.amazonaws.com`
   - Event name: `PutMetricData`

### Using AWS X-Ray for Tracing

Enable X-Ray to trace CloudWatch API calls:

1. Add X-Ray SDK:
   ```bash
   pip install aws-xray-sdk
   ```

2. Instrument your application:
   ```python
   from aws_xray_sdk.core import xray_recorder
   from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware

   xray_recorder.configure(service='ExperimentationPlatform')
   app.add_middleware(XRayMiddleware, recorder=xray_recorder)
   ```

## Support Resources

- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [FastAPI Middleware Documentation](https://fastapi.tiangolo.com/advanced/middleware/)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [boto3 CloudWatch Client Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html)
