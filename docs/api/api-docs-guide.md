# Experimentation Platform API Documentation Guide

This guide explains how to access and use the API documentation for the experimentation platform.

## Accessing the Documentation

The API documentation is available in two formats:

1. **Swagger UI**: Interactive documentation where you can try out API endpoints
   - URL: `/api/v1/docs`
   - Best for: Developers who want to test API endpoints directly

2. **ReDoc**: Clean, responsive documentation with better navigation
   - URL: `/api/v1/redoc`
   - Best for: Reviewing API structure and understanding request/response formats

> **Note**: In production environments, these documentation endpoints may be disabled for security reasons.

## Understanding the API Structure

The API is organized into the following sections:

1. **Authentication (`/api/v1/auth`)**: Endpoints for user authentication
2. **Experiments (`/api/v1/experiments`)**: Manage experiments and variants
3. **Tracking (`/api/v1/tracking`)**: Track user assignments and events
4. **Feature Flags (`/api/v1/feature-flags`)**: Manage feature flags
5. **Administration (`/api/v1/admin`)**: Admin-only operations
6. **Health (`/health`)**: System health check

## Authentication

The API uses two authentication methods:

1. **OAuth2 Bearer Token**: For authenticated user endpoints
   - Obtain a token via `/api/v1/auth/token` endpoint
   - Include the token in the `Authorization: Bearer <token>` header

2. **API Key**: For tracking endpoints called from client applications
   - Include the API key in the `X-API-Key: <api-key>` header

## Using Swagger UI

Swagger UI provides an interactive interface to:

1. **Explore Endpoints**: Browse all available endpoints organized by tags
2. **Read Documentation**: View detailed descriptions, parameters, and response formats
3. **Try Endpoints**: Execute API calls directly from the browser
4. **View Models**: Examine request and response data structures

### Steps to Test an Endpoint

1. Click on the endpoint you want to test
2. Click the "Try it out" button
3. Fill in the required parameters
4. For endpoints requiring authentication, click the "Authorize" button at the top and enter your credentials
5. Click "Execute" to send the request
6. View the response below

## Using ReDoc

ReDoc provides a cleaner reading experience with:

1. **Three-panel layout**: Navigation sidebar, API description, and request/response examples
2. **Search functionality**: Quickly find endpoints by keyword
3. **Deep linking**: Share links to specific endpoints
4. **Responsive design**: Works well on mobile devices

## API Versioning

The API uses versioning to ensure backward compatibility:

- Current version: v1 (accessed via `/api/v1/...`)
- Future versions will be accessible via `/api/v2/...`, etc.

## Common Response Formats

All API endpoints follow a consistent response format:

1. **Success Responses**: Return HTTP 200/201/204 status codes with data in the response body
2. **Error Responses**: Return appropriate HTTP error codes (400, 401, 403, 404, 422, 500) with a standardized error format:

```json
{
  "error": {
    "status_code": 400,
    "message": "Detailed error message",
    "details": [...] // Additional details for validation errors
  }
}
```

## Pagination

List endpoints support pagination with the following query parameters:

- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100, max: 500)

Paginated responses include metadata:

```json
{
  "items": [...],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

## Filtering and Sorting

Many list endpoints support filtering and sorting:

- Filtering: Use query parameters (e.g., `status_filter=active`)
- Sorting: Use `sort_by` and `sort_order` parameters (e.g., `sort_by=created_at&sort_order=desc`)

## Data Models

The API uses Pydantic models to define request and response data structures. These models:

1. **Validate Data**: Ensure all fields meet validation rules
2. **Document Types**: Provide type information for all fields
3. **Set Defaults**: Supply default values where appropriate
4. **Enforce Constraints**: Apply business rules to data

You can view the complete data model definitions in both Swagger UI and ReDoc.

## Common Workflows

Here are the key API workflows for the experimentation platform:

### Experiment Management Workflow

1. Create experiment (`POST /api/v1/experiments`)
2. Update experiment details (`PUT /api/v1/experiments/{experiment_id}`)
3. Start experiment (`POST /api/v1/experiments/{experiment_id}/start`)
4. Monitor results (`GET /api/v1/experiments/{experiment_id}/results`)
5. Complete experiment (`POST /api/v1/experiments/{experiment_id}/complete`)

### User Assignment and Tracking Workflow

1. Assign user to experiment (`POST /api/v1/tracking/assign`)
2. Track user events (`POST /api/v1/tracking/track` or `POST /api/v1/tracking/batch`)
3. Analyze results (`GET /api/v1/experiments/{experiment_id}/results`)

### Feature Flag Workflow

1. Create feature flag (`POST /api/v1/feature-flags`)
2. Update flag configurations (`PUT /api/v1/feature-flags/{feature_flag_id}`)
3. Evaluate flags for user (`POST /api/v1/feature-flags/evaluate`)
4. Create user-specific overrides (`POST /api/v1/feature-flags/{feature_flag_id}/overrides`)

## Rate Limiting

The API implements rate limiting to ensure fair usage and system stability:

- Standard endpoints: 100 requests per minute
- Tracking endpoints: 1000 requests per minute
- Batch tracking endpoint: 10 requests per minute (each request can contain up to 100 events)

Rate limit headers are included in responses:

- `X-RateLimit-Limit`: Maximum requests per minute
- `X-RateLimit-Remaining`: Remaining requests for the current window
- `X-RateLimit-Reset`: Time in seconds until the limit resets

## Security Best Practices

When using the API, follow these security best practices:

1. **Keep credentials secure**: Never expose API keys or tokens in client-side code
2. **Use HTTPS**: Always connect to the API over HTTPS
3. **Minimize permissions**: Use the least privileged role necessary
4. **Validate inputs**: Even though the API validates inputs, also validate on the client side
5. **Handle errors gracefully**: Properly handle API errors in your application

## Webhook Integration

The API provides webhooks for real-time event notifications:

1. Configure webhooks (`POST /api/v1/webhooks`)
2. Receive event notifications (experiment starts, completions, significant results)
3. Implement webhook handlers in your application

Webhook payloads are signed using HMAC-SHA256 for security.

## SDK Support

For easier integration, the platform provides official SDKs:

- JavaScript/TypeScript SDK
- Python SDK
- Java SDK
- iOS/Swift SDK
- Android/Kotlin SDK

The SDKs simplify API integration and handle authentication, retries, and caching.

## Additional Resources

For more information:

1. **Developer Guides**: Detailed tutorials for common use cases
2. **API Changelog**: History of API changes and versioning
3. **Sample Applications**: Reference implementations using the API
4. **Community Forum**: Get help from other developers

## Support and Feedback

If you need assistance with the API:

- Check the documentation first
- Search the community forum for similar issues
- Report bugs or request features using the GitHub repository
- Contact support for critical issues

We welcome your feedback to improve the API and documentation!
