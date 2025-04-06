# Monitoring and Error Tracking Documentation

Welcome to the Experimentation Platform's Monitoring and Error Tracking documentation. This section provides comprehensive information about our AWS CloudWatch-based monitoring system.

## Table of Contents

1. [Monitoring Overview](monitoring-overview.md)
   - Architectural overview
   - Core components
   - Data flow
   - Environment variables
   - Metrics collected

2. [Setup Guide](setup-guide.md)
   - Prerequisites
   - Initial setup
   - Configuration
   - Integration with FastAPI
   - Verification

3. [Dashboard Reference](dashboard-reference.md)
   - System Health Dashboard
   - API Performance Dashboard
   - Using the dashboards
   - Dashboard management
   - Best practices

4. [Logs Insights Queries](log-insights-queries.md)
   - Error analysis queries
   - Performance analysis queries
   - User and request analysis
   - Combined analysis
   - Using and optimizing queries

5. [Troubleshooting Guide](troubleshooting-guide.md)
   - Common issues and solutions
   - Debugging tools
   - Advanced troubleshooting
   - Support resources

## Quick Start

To quickly set up the monitoring system, follow these steps:

1. Install required dependencies:
   ```bash
   pip install -r backend/requirements-monitoring.txt
   ```

2. Create CloudWatch log groups:
   ```bash
   aws logs create-log-group --log-group-name /experimentation-platform/errors --profile experimentation-platform --region us-west-2
   ```

3. Deploy dashboards:
   ```bash
   cd infrastructure/cloudwatch
   chmod +x deploy-dashboards.sh
   ./deploy-dashboards.sh
   ```

4. Configure environment variables:
   ```bash
   export AWS_REGION=us-west-2
   export AWS_PROFILE=experimentation-platform
   ```

5. Start your FastAPI application (middlewares are already integrated)

See the [Setup Guide](setup-guide.md) for detailed instructions.

## Key Features

- **Error Tracking**: Automatic capture and logging of all application errors
- **Performance Metrics**: Real-time tracking of API latency, CPU, and memory usage
- **Custom Dashboards**: Pre-configured CloudWatch dashboards
- **Log Analysis**: Powerful queries for analyzing logs and metrics

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  API Request    │───▶│    Middleware   │───▶│ AWS CloudWatch  │
└─────────────────┘    │  • Metrics      │    │  • Logs         │
                       │  • Error        │    │  • Metrics      │
┌─────────────────┐    │  • Logging      │    │  • Dashboards   │
│  API Response   │◀───│                 │◀───│  • Alarms       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

For more details, see the [Monitoring Overview](monitoring-overview.md).

## Contributing to the Monitoring System

If you want to improve our monitoring system:

1. Review the existing components and their responsibilities
2. Make changes to middleware or utilities
3. Update the dashboard JSON files if necessary
4. Run the deployment script to update dashboards
5. Document any changes in this documentation

## Related Resources

- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [FastAPI Middleware Documentation](https://fastapi.tiangolo.com/advanced/middleware/)
- [Infrastructure Monitoring Best Practices](../infrastructure/monitoring-best-practices.md)
