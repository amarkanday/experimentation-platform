# Experimentation Platform API Specification

This document outlines the API endpoints for the Experimentation Platform, providing a reference for developers integrating with the system.

## Base URL

```
Production: https://api.experimentation-platform.example.com
Development: https://dev-api.experimentation-platform.example.com
```

## Authentication

All API requests must include an API key in the `Authorization` header:

```
Authorization: Bearer YOUR_API_KEY
```

API keys can be generated and managed in the platform's Settings page.

## Response Format

All responses are returned in JSON format with the following structure:

### Success Response

```json
{
  "data": {
    // Response data specific to the endpoint
  },
  "meta": {
    // Metadata about the response (pagination, etc.)
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional error details if available
    }
  }
}
```

## API Endpoints

### Experiments API

#### List Experiments

```
GET /api/v1/experiments
```

Retrieves a list of experiments.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | Filter by status (DRAFT, ACTIVE, PAUSED, COMPLETED, ARCHIVED) |
| page | integer | No | Page number for pagination (default: 1) |
| limit | integer | No | Number of results per page (default: 20, max: 100) |
| sort | string | No | Sort field (created_at, name, status) |
| order | string | No | Sort order (asc, desc) |

**Example Response**

```json
{
  "data": [
    {
      "id": "exp_12345",
      "name": "Homepage Redesign Test",
      "description": "Testing the new homepage design",
      "hypothesis": "The new homepage design will increase conversion rates",
      "status": "ACTIVE",
      "created_at": "2023-10-15T10:30:00Z",
      "updated_at": "2023-10-15T14:45:00Z",
      "start_date": "2023-10-16T00:00:00Z",
      "end_date": "2023-11-16T00:00:00Z",
      "variants": [
        {
          "id": "var_a123",
          "name": "control",
          "description": "Current homepage",
          "allocation": 50
        },
        {
          "id": "var_b456",
          "name": "treatment",
          "description": "New homepage design",
          "allocation": 50
        }
      ]
    }
  ],
  "meta": {
    "total": 42,
    "page": 1,
    "limit": 20,
    "pages": 3
  }
}
```

#### Get Experiment

```
GET /api/v1/experiments/{experiment_id}
```

Retrieves details of a specific experiment.

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| experiment_id | string | Yes | ID of the experiment |

**Example Response**

```json
{
  "data": {
    "id": "exp_12345",
    "name": "Homepage Redesign Test",
    "description": "Testing the new homepage design",
    "hypothesis": "The new homepage design will increase conversion rates",
    "status": "ACTIVE",
    "created_at": "2023-10-15T10:30:00Z",
    "updated_at": "2023-10-15T14:45:00Z",
    "start_date": "2023-10-16T00:00:00Z",
    "end_date": "2023-11-16T00:00:00Z",
    "variants": [
      {
        "id": "var_a123",
        "name": "control",
        "description": "Current homepage",
        "allocation": 50
      },
      {
        "id": "var_b456",
        "name": "treatment",
        "description": "New homepage design",
        "allocation": 50
      }
    ],
    "targeting": {
      "rules": [
        {
          "attribute": "country",
          "operator": "in",
          "value": ["US", "CA", "UK"]
        },
        {
          "attribute": "device",
          "operator": "equals",
          "value": "desktop"
        }
      ],
      "operator": "and"
    },
    "metrics": [
      {
        "id": "met_789",
        "name": "conversion_rate",
        "description": "Percentage of users who complete a purchase",
        "event_name": "purchase_completed"
      }
    ]
  }
}
```

#### Create Experiment

```
POST /api/v1/experiments
```

Creates a new experiment.

**Request Body**

```json
{
  "name": "Homepage Redesign Test",
  "description": "Testing the new homepage design",
  "hypothesis": "The new homepage design will increase conversion rates",
  "status": "DRAFT",
  "start_date": "2023-10-16T00:00:00Z",
  "end_date": "2023-11-16T00:00:00Z",
  "variants": [
    {
      "name": "control",
      "description": "Current homepage",
      "allocation": 50
    },
    {
      "name": "treatment",
      "description": "New homepage design",
      "allocation": 50
    }
  ],
  "targeting": {
    "rules": [
      {
        "attribute": "country",
        "operator": "in",
        "value": ["US", "CA", "UK"]
      },
      {
        "attribute": "device",
        "operator": "equals",
        "value": "desktop"
      }
    ],
    "operator": "and"
  },
  "metrics": [
    {
      "name": "conversion_rate",
      "description": "Percentage of users who complete a purchase",
      "event_name": "purchase_completed"
    }
  ]
}
```

**Example Response**

```json
{
  "data": {
    "id": "exp_12345",
    "name": "Homepage Redesign Test",
    "description": "Testing the new homepage design",
    "hypothesis": "The new homepage design will increase conversion rates",
    "status": "DRAFT",
    "created_at": "2023-10-15T10:30:00Z",
    "updated_at": "2023-10-15T10:30:00Z",
    "start_date": "2023-10-16T00:00:00Z",
    "end_date": "2023-11-16T00:00:00Z",
    "variants": [
      {
        "id": "var_a123",
        "name": "control",
        "description": "Current homepage",
        "allocation": 50
      },
      {
        "id": "var_b456",
        "name": "treatment",
        "description": "New homepage design",
        "allocation": 50
      }
    ],
    "targeting": {
      "rules": [
        {
          "attribute": "country",
          "operator": "in",
          "value": ["US", "CA", "UK"]
        },
        {
          "attribute": "device",
          "operator": "equals",
          "value": "desktop"
        }
      ],
      "operator": "and"
    },
    "metrics": [
      {
        "id": "met_789",
        "name": "conversion_rate",
        "description": "Percentage of users who complete a purchase",
        "event_name": "purchase_completed"
      }
    ]
  }
}
```

#### Update Experiment

```
PUT /api/v1/experiments/{experiment_id}
```

Updates an existing experiment.

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| experiment_id | string | Yes | ID of the experiment to update |

**Request Body**

Same as the create experiment request body. Only include the fields you want to update.

**Example Response**

```json
{
  "data": {
    "id": "exp_12345",
    "name": "Homepage Redesign Test (Updated)",
    "description": "Testing the new homepage design with additional changes",
    "hypothesis": "The new homepage design will increase conversion rates",
    "status": "DRAFT",
    "created_at": "2023-10-15T10:30:00Z",
    "updated_at": "2023-10-15T15:45:00Z",
    "start_date": "2023-10-16T00:00:00Z",
    "end_date": "2023-11-16T00:00:00Z",
    "variants": [
      {
        "id": "var_a123",
        "name": "control",
        "description": "Current homepage",
        "allocation": 50
      },
      {
        "id": "var_b456",
        "name": "treatment",
        "description": "New homepage design",
        "allocation": 50
      }
    ],
    "targeting": {
      "rules": [
        {
          "attribute": "country",
          "operator": "in",
          "value": ["US", "CA", "UK"]
        },
        {
          "attribute": "device",
          "operator": "equals",
          "value": "desktop"
        }
      ],
      "operator": "and"
    },
    "metrics": [
      {
        "id": "met_789",
        "name": "conversion_rate",
        "description": "Percentage of users who complete a purchase",
        "event_name": "purchase_completed"
      }
    ]
  }
}
```

#### Start Experiment

```
POST /api/v1/experiments/{experiment_id}/start
```

Starts an experiment.

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| experiment_id | string | Yes | ID of the experiment to start |

**Example Response**

```json
{
  "data": {
    "id": "exp_12345",
    "status": "ACTIVE",
    "updated_at": "2023-10-15T16:00:00Z",
    "start_date": "2023-10-15T16:00:00Z"
  }
}
```

#### Stop Experiment

```
POST /api/v1/experiments/{experiment_id}/stop
```

Stops an experiment.

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| experiment_id | string | Yes | ID of the experiment to stop |

**Example Response**

```json
{
  "data": {
    "id": "exp_12345",
    "status": "COMPLETED",
    "updated_at": "2023-10-25T12:00:00Z",
    "end_date": "2023-10-25T12:00:00Z"
  }
}
```

#### Get Experiment Results

```
GET /api/v1/experiments/{experiment_id}/results
```

Retrieves the results of an experiment.

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| experiment_id | string | Yes | ID of the experiment |

**Example Response**

```json
{
  "data": {
    "experiment_id": "exp_12345",
    "status": "ACTIVE",
    "sample_size": {
      "control": 5420,
      "treatment": 5380
    },
    "metrics": [
      {
        "name": "conversion_rate",
        "results": {
          "control": {
            "value": 3.2,
            "confidence_interval": [2.8, 3.6]
          },
          "treatment": {
            "value": 4.1,
            "confidence_interval": [3.7, 4.5]
          },
          "improvement": 28.1,
          "confidence": 98.5,
          "is_significant": true
        }
      }
    ]
  }
}
```

### Feature Flags API

#### List Feature Flags

```
GET /api/v1/feature-flags
```

Retrieves a list of feature flags.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| enabled | boolean | No | Filter by enabled status |
| page | integer | No | Page number for pagination (default: 1) |
| limit | integer | No | Number of results per page (default: 20, max: 100) |

**Example Response**

```json
{
  "data": [
    {
      "id": "flag_123",
      "key": "new_checkout_flow",
      "name": "New Checkout Flow",
      "description": "Enable the new checkout flow",
      "enabled": true,
      "created_at": "2023-09-15T10:00:00Z",
      "updated_at": "2023-10-01T14:30:00Z"
    },
    {
      "id": "flag_456",
      "key": "dark_mode",
      "name": "Dark Mode",
      "description": "Enable dark mode theme",
      "enabled": false,
      "created_at": "2023-09-10T11:15:00Z",
      "updated_at": "2023-09-10T11:15:00Z"
    }
  ],
  "meta": {
    "total": 15,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
}
```

#### Get Feature Flag

```
GET /api/v1/feature-flags/{flag_id}
```

Retrieves details of a specific feature flag.

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| flag_id | string | Yes | ID of the feature flag |

**Example Response**

```json
{
  "data": {
    "id": "flag_123",
    "key": "new_checkout_flow",
    "name": "New Checkout Flow",
    "description": "Enable the new checkout flow",
    "enabled": true,
    "created_at": "2023-09-15T10:00:00Z",
    "updated_at": "2023-10-01T14:30:00Z",
    "rules": [
      {
        "id": "rule_789",
        "attribute": "user_type",
        "operator": "equals",
        "value": "premium",
        "rollout_percentage": 100
      },
      {
        "id": "rule_012",
        "attribute": "country",
        "operator": "in",
        "value": ["US", "CA"],
        "rollout_percentage": 25
      }
    ],
    "default_rule": {
      "rollout_percentage": 0
    },
    "variations": [
      {
        "id": "var_def",
        "key": "on",
        "value": true
      },
      {
        "id": "var_ghi",
        "key": "off",
        "value": false
      }
    ]
  }
}
```

#### Create Feature Flag

```
POST /api/v1/feature-flags
```

Creates a new feature flag.

**Request Body**

```json
{
  "key": "new_checkout_flow",
  "name": "New Checkout Flow",
  "description": "Enable the new checkout flow",
  "enabled": false,
  "rules": [
    {
      "attribute": "user_type",
      "operator": "equals",
      "value": "premium",
      "rollout_percentage": 100
    },
    {
      "attribute": "country",
      "operator": "in",
      "value": ["US", "CA"],
      "rollout_percentage": 25
    }
  ],
  "default_rule": {
    "rollout_percentage": 0
  },
  "variations": [
    {
      "key": "on",
      "value": true
    },
    {
      "key": "off",
      "value": false
    }
  ]
}
```

**Example Response**

```json
{
  "data": {
    "id": "flag_123",
    "key": "new_checkout_flow",
    "name": "New Checkout Flow",
    "description": "Enable the new checkout flow",
    "enabled": false,
    "created_at": "2023-10-15T10:00:00Z",
    "updated_at": "2023-10-15T10:00:00Z",
    "rules": [
      {
        "id": "rule_789",
        "attribute": "user_type",
        "operator": "equals",
        "value": "premium",
        "rollout_percentage": 100
      },
      {
        "id": "rule_012",
        "attribute": "country",
        "operator": "in",
        "value": ["US", "CA"],
        "rollout_percentage": 25
      }
    ],
    "default_rule": {
      "rollout_percentage": 0
    },
    "variations": [
      {
        "id": "var_def",
        "key": "on",
        "value": true
      },
      {
        "id": "var_ghi",
        "key": "off",
        "value": false
      }
    ]
  }
}
```

#### Update Feature Flag

```
PUT /api/v1/feature-flags/{flag_id}
```

Updates an existing feature flag.

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| flag_id | string | Yes | ID of the feature flag to update |

**Request Body**

Same as the create feature flag request body. Only include the fields you want to update.

**Example Response**

Similar to the response from the Get Feature Flag endpoint, with updated values.

#### Toggle Feature Flag

```
PATCH /api/v1/feature-flags/{flag_id}/toggle
```

Enables or disables a feature flag.

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| flag_id | string | Yes | ID of the feature flag to toggle |

**Request Body**

```json
{
  "enabled": true
}
```

**Example Response**

```json
{
  "data": {
    "id": "flag_123",
    "key": "new_checkout_flow",
    "enabled": true,
    "updated_at": "2023-10-15T14:30:00Z"
  }
}
```

#### Evaluate Feature Flag

```
GET /api/v1/feature-flags/evaluate
```

Evaluates a feature flag for a specific user.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| key | string | Yes | Key of the feature flag to evaluate |
| user_id | string | Yes | ID of the user |
| context | string | No | JSON string of user attributes for targeting |

**Example Request**

```
GET /api/v1/feature-flags/evaluate?key=new_checkout_flow&user_id=user_123&context={"country":"US","user_type":"premium"}
```

**Example Response**

```json
{
  "data": {
    "key": "new_checkout_flow",
    "enabled": true,
    "variation": "on",
    "value": true,
    "rule_id": "rule_789"
  }
}
```

### Assignment API

#### Get Assignment

```
GET /api/v1/assignments
```

Retrieves the variant assignment for a user in an experiment.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| experiment_id | string | Yes | ID of the experiment |
| user_id | string | Yes | ID of the user |
| context | string | No | JSON string of user attributes for targeting |

**Example Request**

```
GET /api/v1/assignments?experiment_id=exp_12345&user_id=user_789&context={"country":"US","device":"mobile"}
```

**Example Response**

```json
{
  "data": {
    "experiment_id": "exp_12345",
    "user_id": "user_789",
    "variant": "treatment",
    "variant_id": "var_b456",
    "timestamp": "2023-10-15T15:30:22Z"
  }
}
```

### Events API

#### Track Event

```
POST /api/v1/events
```

Tracks an event for a user.

**Request Body**

```json
{
  "user_id": "user_789",
  "event_type": "purchase_completed",
  "experiment_id": "exp_12345",
  "variant": "treatment",
  "timestamp": "2023-10-15T16:45:33Z",
  "metadata": {
    "value": 99.99,
    "currency": "USD",
    "product_id": "prod_456"
  }
}
```

**Example Response**

```json
{
  "data": {
    "id": "evt_987",
    "user_id": "user_789",
    "event_type": "purchase_completed",
    "experiment_id": "exp_12345",
    "variant": "treatment",
    "timestamp": "2023-10-15T16:45:33Z",
    "received_at": "2023-10-15T16:45:34Z"
  }
}
```

#### Batch Track Events

```
POST /api/v1/events/batch
```

Tracks multiple events in a single request.

**Request Body**

```json
{
  "events": [
    {
      "user_id": "user_789",
      "event_type": "page_view",
      "experiment_id": "exp_12345",
      "variant": "treatment",
      "timestamp": "2023-10-15T16:40:22Z",
      "metadata": {
        "page": "/products"
      }
    },
    {
      "user_id": "user_789",
      "event_type": "add_to_cart",
      "experiment_id": "exp_12345",
      "variant": "treatment",
      "timestamp": "2023-10-15T16:42:15Z",
      "metadata": {
        "product_id": "prod_456",
        "quantity": 1
      }
    }
  ]
}
```

**Example Response**

```json
{
  "data": {
    "processed": 2,
    "failed": 0,
    "event_ids": ["evt_123", "evt_124"]
  }
}
```

### Users API

#### List Users

```
GET /api/v1/users
```

Retrieves a list of users with access to the platform.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| role | string | No | Filter by role (admin, analyst, developer, viewer) |
| page | integer | No | Page number for pagination (default: 1) |
| limit | integer | No | Number of results per page (default: 20, max: 100) |

**Example Response**

```json
{
  "data": [
    {
      "id": "usr_123",
      "email": "john.doe@example.com",
      "name": "John Doe",
      "role": "admin",
      "created_at": "2023-09-01T10:00:00Z",
      "last_login": "2023-10-15T09:30:00Z"
    },
    {
      "id": "usr_456",
      "email": "jane.smith@example.com",
      "name": "Jane Smith",
      "role": "analyst",
      "created_at": "2023-09-15T14:20:00Z",
      "last_login": "2023-10-14T16:45:00Z"
    }
  ],
  "meta": {
    "total": 8,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
}
```

#### Create User

```
POST /api/v1/users
```

Creates a new user with access to the platform.

**Request Body**

```json
{
  "email": "new.user@example.com",
  "name": "New User",
  "role": "developer"
}
```

**Example Response**

```json
{
  "data": {
    "id": "usr_789",
    "email": "new.user@example.com",
    "name": "New User",
    "role": "developer",
    "created_at": "2023-10-15T17:00:00Z"
  }
}
```

### API Keys API

#### List API Keys

```
GET /api/v1/api-keys
```

Retrieves a list of API keys for the account.

**Example Response**

```json
{
  "data": [
    {
      "id": "key_123",
      "name": "Production API Key",
      "prefix": "pk_123",
      "created_at": "2023-09-01T10:00:00Z",
      "last_used_at": "2023-10-15T09:30:00Z"
    },
    {
      "id": "key_456",
      "name": "Development API Key",
      "prefix": "pk_456",
      "created_at": "2023-09-15T14:20:00Z",
      "last_used_at": "2023-10-14T16:45:00Z"
    }
  ]
}
```

#### Create API Key

```
POST /api/v1/api-keys
```

Creates a new API key.

**Request Body**

```json
{
  "name": "New API Key"
}
```

**Example Response**

```json
{
  "data": {
    "id": "key_789",
    "name": "New API Key",
    "prefix": "pk_789",
    "key": "pk_789_COMPLETE_KEY_SHOWN_ONLY_ONCE",
    "created_at": "2023-10-15T17:30:00Z"
  }
}
```

#### Revoke API Key

```
DELETE /api/v1/api-keys/{key_id}
```

Revokes an API key.

**Path Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| key_id | string | Yes | ID of the API key to revoke |

**Example Response**

```json
{
  "data": {
    "id": "key_123",
    "revoked": true,
    "revoked_at": "2023-10-15T18:00:00Z"
  }
}
```

## Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| UNAUTHORIZED | 401 | Authentication failed or invalid API key |
| FORBIDDEN | 403 | Not authorized to perform the requested action |
| NOT_FOUND | 404 | The requested resource was not found |
| VALIDATION_ERROR | 422 | Request validation failed |
| CONFLICT | 409 | Operation cannot be completed due to a conflict |
| RATE_LIMIT_EXCEEDED | 429 | Rate limit exceeded |
| INTERNAL_ERROR | 500 | An internal server error occurred |

## Rate Limits

The API enforces the following rate limits:

- Standard tier: 10 requests per second, 10,000 requests per day
- Enterprise tier: 100 requests per second, 1,000,000 requests per day

When a rate limit is exceeded, the API will respond with a 429 status code and the following headers:

- `X-RateLimit-Limit`: The maximum number of requests allowed per time window
- `X-RateLimit-Remaining`: The number of requests remaining in the current time window
- `X-RateLimit-Reset`: The time at which the current rate limit window resets in UTC epoch seconds

## Versioning

The API uses a versioned URL path (e.g., `/api/v1/`) to ensure backward compatibility. When breaking changes are introduced, a new API version will be released.

## SDK Support

The API is accessible through our client SDKs:

- [JavaScript SDK](https://github.com/your-org/experimentation-js-sdk)
- [Python SDK](https://github.com/your-org/experimentation-python-sdk)
- [Ruby SDK](https://github.com/your-org/experimentation-ruby-sdk)
- [Java SDK](https://github.com/your-org/experimentation-java-sdk)

## Webhook Notifications

The platform can send webhook notifications for important events:

- Experiment started
- Experiment stopped
- Experiment reached statistical significance
- Feature flag toggled

To configure webhooks, visit the Integrations section in the platform settings.
