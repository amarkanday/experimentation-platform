# Troubleshooting Guide: Enhanced Logging Middleware

This document provides solutions for common issues that may arise when using the enhanced logging middleware features.

## Common Issues and Solutions

### 1. Missing or Incomplete Metrics

**Symptoms:**
- Metrics are showing as `0.0` or `None`
- Memory usage or CPU usage not being recorded

**Possible Causes and Solutions:**

- **Missing `psutil` dependency:**
  ```bash
  pip install psutil==5.9.8
  ```

- **Insufficient permissions:**
  Ensure the application has sufficient permissions to access system metrics.

- **Metrics collection not started:**
  Verify that `metrics.start()` is called before attempting to collect metrics.

- **Platform-specific issues:**
  The metrics collection may behave differently on different operating systems. Check the specific documentation for your platform.

### 2. Sensitive Data Not Being Masked

**Symptoms:**
- Sensitive data appears in logs unmasked
- Custom fields are not being masked

**Possible Causes and Solutions:**

- **Environment variable not set:**
  Ensure `MASK_ADDITIONAL_FIELDS` is set correctly if you want to mask custom fields.

- **Request body not being collected:**
  Set `COLLECT_REQUEST_BODY="true"` to collect and mask request bodies.

- **Nested fields:**
  For deeply nested JSON, add the parent field to `MASK_ADDITIONAL_FIELDS`. For example, `customer.credit_card` would require `customer` to be in the list.

- **Unexpected data format:**
  The masking utility works with string values. Ensure that numeric values or other types that should be masked are converted to strings first.

### 3. Performance Impact

**Symptoms:**
- Slow response times
- High CPU or memory usage in production

**Possible Causes and Solutions:**

- **Too much logging:**
  Adjust the log level to reduce verbosity in production:
  ```
  LOG_LEVEL=WARNING
  ```

- **Request body collection in production:**
  Consider disabling request body collection in production to improve performance:
  ```
  COLLECT_REQUEST_BODY="false"
  ```

- **Metrics collection overhead:**
  If metrics collection is causing significant overhead, consider sampling instead of collecting for every request.

### 4. Test Failures

**Symptoms:**
- Unit tests for the middleware or utilities are failing

**Possible Causes and Solutions:**

- **Missing test dependencies:**
  Ensure all test dependencies are installed:
  ```bash
  pip install pytest-asyncio==0.23.4 pytest-mock==3.12.0
  ```

- **Mocking issues:**
  When testing middleware with mocked dependencies, ensure the mocks are correctly set up to handle async functions.

- **Environment setup:**
  Some tests may rely on specific environment variables. Make sure they are set correctly for the test environment.

### 5. Integration with CloudWatch

**Symptoms:**
- Logs not appearing in CloudWatch
- Incomplete metrics in CloudWatch

**Possible Causes and Solutions:**

- **AWS credentials:**
  Ensure that `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION` are set correctly.

- **IAM permissions:**
  Verify that the IAM role or user has sufficient permissions to write to CloudWatch logs.

- **CloudWatch configuration:**
  Check that the CloudWatch log group and stream exist and are configured correctly.

- **Log formatting:**
  Ensure that logs are in a format that CloudWatch can parse correctly.

## Debugging Tips

1. **Enable debug logging:**
   ```
   LOG_LEVEL=DEBUG
   ```

2. **Log raw data before masking:**
   Add temporary debug logging to see data before it's masked, but be careful not to log sensitive data in production.

3. **Use print statements in the example script:**
   Modify the example script to print more detailed information about what's happening during processing.

4. **Check system compatibility:**
   Verify that your OS and environment are compatible with the utilities, especially for metrics collection.

## Getting Additional Help

If you continue to experience issues after trying these solutions, please:

1. Create a detailed bug report including:
   - Complete error messages
   - OS and environment information
   - Steps to reproduce the issue
   - Environment variables set

2. Consult the unit tests as reference implementations for correct usage

3. Check for recent updates to the utilities that may address known issues
