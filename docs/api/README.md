# API Documentation

This directory contains the API documentation for the Experimentation Platform.

## Files

1. [API Reference](endpoints.md)
   - Comprehensive guide to using the API
   - Authentication and authorization
   - Usage examples with curl commands
   - Rate limiting and constraints
   - SDK usage examples
   - Framework integrations

2. [API Specification](specs.md)
   - Detailed OpenAPI/Swagger specification
   - Request/response schemas
   - Error codes and handling
   - Pagination details
   - Data types and formats

3. [API Development Guide](api-docs-guide.md)
   - Guidelines for API development
   - Best practices
   - Versioning strategy
   - Testing requirements
   - Documentation standards

## Quick Start

1. Get your API key from the platform's Settings page
2. Use the key in your requests:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" https://api.experimentation-platform.example.com/v1/experiments
   ```
3. Check the [API Reference](endpoints.md) for detailed usage examples
4. Refer to the [API Specification](specs.md) for complete endpoint documentation

## Common Tasks

1. **Authentication**
   - [OAuth2 Authentication](endpoints.md#oauth2-authentication)
   - [API Key Authentication](endpoints.md#api-key-authentication)

2. **Experiments**
   - [Creating Experiments](endpoints.md#managing-experiments)
   - [Managing Variants](specs.md#variants)
   - [Analyzing Results](endpoints.md#tracking-events)

3. **Feature Flags**
   - [Creating Feature Flags](endpoints.md#feature-flag-management)
   - [User Targeting](specs.md#targeting)
   - [Flag Evaluation](endpoints.md#feature-flag-management)

4. **Event Tracking**
   - [Tracking Events](endpoints.md#tracking-events)
   - [User Assignments](endpoints.md#tracking-events)
   - [Metrics](specs.md#metrics)

## Need Help?

- Check the [API Reference](endpoints.md) for usage examples
- Review the [API Specification](specs.md) for detailed endpoint documentation
- Follow the [API Development Guide](api-docs-guide.md) for best practices
- Contact support for additional assistance
