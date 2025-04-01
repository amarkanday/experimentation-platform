# API Endpoints Documentation

This document provides detailed information about all available API endpoints in the Experimentation Platform.

## Authentication and Authorization

### Overview
The API uses two types of authentication:
1. OAuth2 Bearer tokens for user authentication
2. API keys for client applications

### OAuth2 Authentication
1. **Obtain Access Token**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=your_password"
   ```

2. **Using the Access Token**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/users/me" \
     -H "Authorization: Bearer your_access_token"
   ```

### API Key Authentication
1. **Obtain API Key**:
   - Contact your administrator to get an API key
   - API keys are used for client applications to access tracking and feature flag endpoints

2. **Using the API Key**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/feature-flags/user/123" \
     -H "X-API-Key: your_api_key"
   ```

### Authorization Levels
1. **Regular Users**:
   - Can access their own data
   - Can create and manage their own experiments
   - Cannot access admin endpoints

2. **Superusers**:
   - Can access all user data
   - Can manage all experiments
   - Can access admin endpoints
   - Can create other users

## Usage Examples

### 1. User Registration and Authentication
```bash
# 1. Register a new user
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "given_name": "John",
    "family_name": "Doe"
  }'

# 2. Confirm registration
curl -X POST "http://localhost:8000/api/v1/auth/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "confirmation_code": "123456"
  }'

# 3. Login to get access token
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john.doe&password=SecurePass123!"
```

### 2. Managing Experiments
```bash
# 1. List experiments
curl -X GET "http://localhost:8000/api/v1/experiments/" \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json"

# 2. Create a new experiment
curl -X POST "http://localhost:8000/api/v1/experiments/" \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Button Color Test",
    "description": "Testing different button colors",
    "hypothesis": "Red buttons will have higher click rates",
    "experiment_type": "AB_TEST",
    "start_date": "2024-04-01T00:00:00Z",
    "end_date": "2024-04-30T23:59:59Z",
    "targeting_rules": {
      "countries": ["US", "CA"],
      "browsers": ["chrome", "firefox"]
    }
  }'

# 3. Get experiment results
curl -X GET "http://localhost:8000/api/v1/experiments/123/results" \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json"
```

### 3. Feature Flag Management
```bash
# 1. List feature flags
curl -X GET "http://localhost:8000/api/v1/feature-flags/" \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json"

# 2. Create a feature flag
curl -X POST "http://localhost:8000/api/v1/feature-flags/" \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "new_checkout_flow",
    "name": "New Checkout Flow",
    "description": "Rolling out new checkout experience",
    "status": "ACTIVE",
    "rollout_percentage": 50,
    "targeting_rules": {
      "countries": ["US"],
      "user_segments": ["premium"]
    }
  }'

# 3. Get feature flags for a user (client-side)
curl -X GET "http://localhost:8000/api/v1/feature-flags/user/123" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json"
```

### 4. Tracking Events
```bash
# 1. Get user assignments
curl -X GET "http://localhost:8000/api/v1/tracking/assignments/123" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json"

# 2. Track an event
curl -X POST "http://localhost:8000/api/v1/tracking/events" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "PURCHASE",
    "user_id": "123",
    "experiment_id": "456",
    "variant_id": "789",
    "value": 99.99,
    "event_metadata": {
      "product_id": "ABC123",
      "payment_method": "credit_card"
    }
  }'
```

### 5. Admin Operations
```bash
# 1. List all users (superuser only)
curl -X GET "http://localhost:8000/api/v1/admin/users" \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json"

# 2. Create a new user (superuser only)
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane.smith",
    "email": "jane@example.com",
    "password": "SecurePass123!",
    "full_name": "Jane Smith",
    "is_active": true,
    "is_superuser": false
  }'
```

## Rate Limiting and API Constraints

### Rate Limits
- Authentication endpoints: 5 requests per minute
- API endpoints: 100 requests per minute per API key
- Admin endpoints: 50 requests per minute

### Request Size Limits
- Maximum request body size: 1MB
- Maximum response size: 10MB

### Pagination
- Default page size: 100 items
- Maximum page size: 500 items
- All list endpoints support pagination using `skip` and `limit` parameters

### Caching
- Experiment and feature flag data is cached for 1 hour
- Results data is cached for 5 minutes
- Cache-Control headers are included in responses

## Authentication Endpoints

### Sign Up
- **Endpoint**: `POST /api/v1/auth/signup`
- **Description**: Register a new user
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string",
    "email": "string",
    "given_name": "string",
    "family_name": "string"
  }
  ```
- **Response**: 201 Created
  ```json
  {
    "username": "string",
    "user_id": "string",
    "confirmation_required": true
  }
  ```

### Confirm Sign Up
- **Endpoint**: `POST /api/v1/auth/confirm`
- **Description**: Confirm user registration with verification code
- **Request Body**:
  ```json
  {
    "username": "string",
    "confirmation_code": "string"
  }
  ```
- **Response**: 200 OK
  ```json
  {
    "message": "User confirmed successfully"
  }
  ```

### Login
- **Endpoint**: `POST /api/v1/auth/token`
- **Description**: OAuth2 compatible token login
- **Request Body**: Form data
  - username: string
  - password: string
- **Response**: 200 OK
  ```json
  {
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ```

### Get User Info
- **Endpoint**: `GET /api/v1/auth/me`
- **Description**: Get current user information
- **Headers**: Authorization: Bearer {token}
- **Response**: 200 OK
  ```json
  {
    "username": "string",
    "email": "string",
    "given_name": "string",
    "family_name": "string"
  }
  ```

## User Management Endpoints

### List Users
- **Endpoint**: `GET /api/v1/users/`
- **Description**: List users (all for superusers, self for regular users)
- **Headers**: Authorization: Bearer {token}
- **Query Parameters**:
  - skip: int (default: 0)
  - limit: int (default: 100, max: 100)
- **Response**: 200 OK
  ```json
  {
    "items": [
      {
        "id": "string",
        "username": "string",
        "email": "string",
        "full_name": "string",
        "is_active": true,
        "is_superuser": false,
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    ],
    "total": 100,
    "skip": 0,
    "limit": 100
  }
  ```

### Create User
- **Endpoint**: `POST /api/v1/users/`
- **Description**: Create new user (superuser only)
- **Headers**: Authorization: Bearer {token}
- **Request Body**:
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string",
    "full_name": "string",
    "is_active": true,
    "is_superuser": false
  }
  ```
- **Response**: 201 Created

### Get User
- **Endpoint**: `GET /api/v1/users/{user_id}`
- **Description**: Get user by ID
- **Headers**: Authorization: Bearer {token}
- **Path Parameters**:
  - user_id: string (UUID)
- **Response**: 200 OK
  ```json
  {
    "id": "string",
    "username": "string",
    "email": "string",
    "full_name": "string",
    "is_active": true,
    "is_superuser": false,
    "created_at": "datetime",
    "updated_at": "datetime"
  }
  ```

## Experiment Endpoints

### List Experiments
- **Endpoint**: `GET /api/v1/experiments/`
- **Description**: List experiments with filtering and pagination
- **Headers**: Authorization: Bearer {token}
- **Query Parameters**:
  - status_filter: string (optional)
  - skip: int (default: 0)
  - limit: int (default: 100, max: 500)
  - search: string (optional)
  - sort_by: string (default: "created_at")
  - sort_order: string (default: "desc")
- **Response**: 200 OK
  ```json
  {
    "items": [
      {
        "id": "string",
        "name": "string",
        "description": "string",
        "status": "string",
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    ],
    "total": 100,
    "skip": 0,
    "limit": 100
  }
  ```

### Get Experiment
- **Endpoint**: `GET /api/v1/experiments/{experiment_id}`
- **Description**: Get experiment details
- **Headers**: Authorization: Bearer {token}
- **Path Parameters**:
  - experiment_id: string (UUID)
- **Response**: 200 OK
  ```json
  {
    "id": "string",
    "name": "string",
    "description": "string",
    "status": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
  ```

### Get Experiment Results
- **Endpoint**: `GET /api/v1/experiments/{experiment_id}/results`
- **Description**: Get experiment results and analysis
- **Headers**: Authorization: Bearer {token}
- **Path Parameters**:
  - experiment_id: string (UUID)
- **Response**: 200 OK
  ```json
  {
    "experiment_id": "string",
    "status": "string",
    "metrics": [
      {
        "name": "string",
        "control_value": 0.0,
        "treatment_value": 0.0,
        "difference": 0.0,
        "p_value": 0.0,
        "is_significant": true
      }
    ],
    "sample_size": {
      "control": 100,
      "treatment": 100
    }
  }
  ```

## Feature Flag Endpoints

### List Feature Flags
- **Endpoint**: `GET /api/v1/feature-flags/`
- **Description**: List feature flags with filtering and pagination
- **Headers**: Authorization: Bearer {token}
- **Query Parameters**:
  - status_filter: string (optional)
  - skip: int (default: 0)
  - limit: int (default: 100, max: 500)
  - search: string (optional)
- **Response**: 200 OK
  ```json
  [
    {
      "id": "string",
      "key": "string",
      "name": "string",
      "description": "string",
      "status": "string",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ]
  ```

### Get User Feature Flags
- **Endpoint**: `GET /api/v1/feature-flags/user/{user_id}`
- **Description**: Get all feature flags evaluated for a user
- **Headers**: X-API-Key: {api_key}
- **Path Parameters**:
  - user_id: string
- **Query Parameters**:
  - context: object (optional)
- **Response**: 200 OK
  ```json
  {
    "feature_flag_key": true,
    "another_flag": false
  }
  ```

## Tracking Endpoints

### Get User Assignments
- **Endpoint**: `GET /api/v1/tracking/assignments/{user_id}`
- **Description**: Get user's experiment assignments
- **Headers**: X-API-Key: {api_key}
- **Path Parameters**:
  - user_id: string
- **Query Parameters**:
  - active_only: boolean (default: true)
- **Response**: 200 OK
  ```json
  [
    {
      "experiment_id": "string",
      "variant_id": "string",
      "assignment_date": "datetime"
    }
  ]
  ```

## Admin Endpoints

### List Users (Admin)
- **Endpoint**: `GET /api/v1/admin/users`
- **Description**: List all users (superuser only)
- **Headers**: Authorization: Bearer {token}
- **Query Parameters**:
  - skip: int (default: 0)
  - limit: int (default: 100, max: 100)
- **Response**: 200 OK
  ```json
  {
    "items": [
      {
        "id": "string",
        "username": "string",
        "email": "string",
        "full_name": "string",
        "is_active": true,
        "is_superuser": false,
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    ],
    "total": 100,
    "skip": 0,
    "limit": 100
  }
  ```

### Delete User (Admin)
- **Endpoint**: `DELETE /api/v1/admin/users/{user_id}`
- **Description**: Delete user (superuser only)
- **Headers**: Authorization: Bearer {token}
- **Path Parameters**:
  - user_id: string (UUID)
- **Response**: 204 No Content

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Error Handling Examples

### 1. Authentication Errors
```bash
# Invalid credentials
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=wrong@example.com&password=wrong_password"

# Response (401 Unauthorized)
{
  "detail": "Incorrect username or password"
}

# Expired token
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer expired_token"

# Response (401 Unauthorized)
{
  "detail": "Token has expired"
}
```

### 2. Validation Errors
```bash
# Invalid experiment creation
curl -X POST "http://localhost:8000/api/v1/experiments/" \
  -H "Authorization: Bearer your_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "",  # Empty name
    "experiment_type": "INVALID_TYPE"  # Invalid type
  }'

# Response (422 Unprocessable Entity)
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "name cannot be empty",
      "type": "value_error"
    },
    {
      "loc": ["body", "experiment_type"],
      "msg": "invalid experiment type",
      "type": "value_error"
    }
  ]
}
```

### 3. Rate Limiting
```bash
# Too many requests
curl -X GET "http://localhost:8000/api/v1/experiments/" \
  -H "Authorization: Bearer your_access_token"

# Response (429 Too Many Requests)
{
  "detail": "Too many requests. Please try again in 60 seconds."
}
```

## Targeting Rules and Experiment Types

### Targeting Rules

#### 1. User-Based Targeting
```json
{
  "user_segments": ["premium", "beta_users"],
  "user_attributes": {
    "country": ["US", "CA"],
    "browser": ["chrome", "firefox"],
    "device_type": ["mobile", "desktop"],
    "user_role": ["admin", "editor"]
  }
}
```

#### 2. Time-Based Targeting
```json
{
  "time_rules": {
    "start_date": "2024-04-01T00:00:00Z",
    "end_date": "2024-04-30T23:59:59Z",
    "timezone": "America/New_York",
    "day_of_week": ["monday", "wednesday", "friday"],
    "hour_of_day": {
      "start": 9,
      "end": 17
    }
  }
}
```

#### 3. Percentage-Based Rollout
```json
{
  "rollout_percentage": 50,
  "sticky_assignment": true,
  "excluded_users": ["user1", "user2"],
  "included_users": ["user3", "user4"]
}
```

### Experiment Types

#### 1. A/B Testing
```json
{
  "experiment_type": "AB_TEST",
  "variants": [
    {
      "id": "control",
      "name": "Control",
      "weight": 0.5
    },
    {
      "id": "treatment",
      "name": "Treatment",
      "weight": 0.5
    }
  ]
}
```

#### 2. Multivariate Testing
```json
{
  "experiment_type": "MULTIVARIATE",
  "factors": [
    {
      "name": "button_color",
      "levels": ["red", "blue", "green"]
    },
    {
      "name": "button_size",
      "levels": ["small", "medium", "large"]
    }
  ],
  "design": "FULL_FACTORIAL"
}
```

#### 3. Feature Flag
```json
{
  "experiment_type": "FEATURE_FLAG",
  "status": "ACTIVE",
  "default_value": false,
  "overrides": [
    {
      "user_id": "user1",
      "value": true
    },
    {
      "user_segment": "beta_users",
      "value": true
    }
  ]
}
```

## SDK Usage

### Python SDK

#### Installation
```bash
pip install experimentation-platform-sdk
```

#### Basic Usage
```python
from experimentation_platform import ExperimentationClient

# Initialize client
client = ExperimentationClient(
    api_key="your_api_key",
    base_url="http://localhost:8000"
)

# Get feature flags for a user
flags = client.get_user_feature_flags(
    user_id="user123",
    context={
        "country": "US",
        "browser": "chrome"
    }
)

# Track an event
client.track_event(
    event_type="PURCHASE",
    user_id="user123",
    experiment_id="exp456",
    variant_id="var789",
    value=99.99,
    metadata={
        "product_id": "ABC123",
        "payment_method": "credit_card"
    }
)

# Get experiment assignments
assignments = client.get_user_assignments(
    user_id="user123",
    active_only=True
)
```

### JavaScript SDK

#### Installation
```bash
npm install experimentation-platform-sdk
```

#### Basic Usage
```javascript
import { ExperimentationClient } from 'experimentation-platform-sdk';

// Initialize client
const client = new ExperimentationClient({
  apiKey: 'your_api_key',
  baseUrl: 'http://localhost:8000'
});

// Get feature flags for a user
const flags = await client.getUserFeatureFlags('user123', {
  context: {
    country: 'US',
    browser: 'chrome'
  }
});

// Track an event
await client.trackEvent({
  eventType: 'PURCHASE',
  userId: 'user123',
  experimentId: 'exp456',
  variantId: 'var789',
  value: 99.99,
  metadata: {
    productId: 'ABC123',
    paymentMethod: 'credit_card'
  }
});

// Get experiment assignments
const assignments = await client.getUserAssignments('user123', {
  activeOnly: true
});
```

### SDK Features

#### 1. Automatic Caching
```python
# Python
client = ExperimentationClient(
    api_key="your_api_key",
    cache_ttl=3600  # Cache for 1 hour
)

# JavaScript
const client = new ExperimentationClient({
  apiKey: 'your_api_key',
  cacheTTL: 3600  // Cache for 1 hour
});
```

#### 2. Error Handling
```python
# Python
try:
    flags = client.get_user_feature_flags("user123")
except ExperimentationError as e:
    if e.code == "RATE_LIMIT":
        # Handle rate limiting
    elif e.code == "INVALID_API_KEY":
        # Handle invalid API key
```

```javascript
// JavaScript
try {
  const flags = await client.getUserFeatureFlags('user123');
} catch (error) {
  if (error.code === 'RATE_LIMIT') {
    // Handle rate limiting
  } else if (error.code === 'INVALID_API_KEY') {
    // Handle invalid API key
  }
}
```

#### 3. Batch Operations
```python
# Python
client.track_events([
    {
        "event_type": "PURCHASE",
        "user_id": "user1",
        "value": 99.99
    },
    {
        "event_type": "PURCHASE",
        "user_id": "user2",
        "value": 149.99
    }
])
```

```javascript
// JavaScript
await client.trackEvents([
  {
    eventType: 'PURCHASE',
    userId: 'user1',
    value: 99.99
  },
  {
    eventType: 'PURCHASE',
    userId: 'user2',
    value: 149.99
  }
]);
```

## Framework Integration Examples

### React Integration

#### 1. Using React Hook
```typescript
// hooks/useExperimentation.ts
import { useState, useEffect } from 'react';
import { ExperimentationClient } from 'experimentation-platform-sdk';

const client = new ExperimentationClient({
  apiKey: process.env.REACT_APP_API_KEY,
  baseUrl: process.env.REACT_APP_API_URL
});

export function useExperimentation(userId: string) {
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const [assignments, setAssignments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [flagsData, assignmentsData] = await Promise.all([
          client.getUserFeatureFlags(userId, {
            context: {
              browser: navigator.userAgent,
              screenSize: `${window.innerWidth}x${window.innerHeight}`
            }
          }),
          client.getUserAssignments(userId, { activeOnly: true })
        ]);
        setFlags(flagsData);
        setAssignments(assignmentsData);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [userId]);

  return { flags, assignments, loading, error };
}

// Usage in component
function MyComponent({ userId }: { userId: string }) {
  const { flags, assignments, loading, error } = useExperimentation(userId);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {flags.newFeature && <NewFeatureComponent />}
      {assignments.map(assignment => (
        <ExperimentVariant key={assignment.experiment_id} variant={assignment.variant_id}>
          {/* Variant content */}
        </ExperimentVariant>
      ))}
    </div>
  );
}
```

#### 2. Using Context Provider
```typescript
// contexts/ExperimentationContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { ExperimentationClient } from 'experimentation-platform-sdk';

interface ExperimentationContextType {
  flags: Record<string, boolean>;
  assignments: any[];
  trackEvent: (eventType: string, value?: number, metadata?: any) => Promise<void>;
}

const ExperimentationContext = createContext<ExperimentationContextType | null>(null);

export function ExperimentationProvider({
  children,
  userId,
  apiKey
}: {
  children: React.ReactNode;
  userId: string;
  apiKey: string;
}) {
  const client = new ExperimentationClient({ apiKey });
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const [assignments, setAssignments] = useState<any[]>([]);

  useEffect(() => {
    // Load initial data
    loadExperimentationData();
  }, [userId]);

  async function loadExperimentationData() {
    try {
      const [flagsData, assignmentsData] = await Promise.all([
        client.getUserFeatureFlags(userId),
        client.getUserAssignments(userId)
      ]);
      setFlags(flagsData);
      setAssignments(assignmentsData);
    } catch (error) {
      console.error('Failed to load experimentation data:', error);
    }
  }

  async function trackEvent(eventType: string, value?: number, metadata?: any) {
    try {
      await client.trackEvent({
        eventType,
        userId,
        value,
        metadata
      });
    } catch (error) {
      console.error('Failed to track event:', error);
    }
  }

  return (
    <ExperimentationContext.Provider value={{ flags, assignments, trackEvent }}>
      {children}
    </ExperimentationContext.Provider>
  );
}

export function useExperimentationContext() {
  const context = useContext(ExperimentationContext);
  if (!context) {
    throw new Error('useExperimentationContext must be used within ExperimentationProvider');
  }
  return context;
}

// Usage in app
function App() {
  return (
    <ExperimentationProvider userId="user123" apiKey="your_api_key">
      <MyApp />
    </ExperimentationProvider>
  );
}
```

### Node.js Integration

#### 1. Express.js Middleware
```typescript
// middleware/experimentation.ts
import { ExperimentationClient } from 'experimentation-platform-sdk';

const client = new ExperimentationClient({
  apiKey: process.env.API_KEY,
  baseUrl: process.env.API_URL
});

export function experimentationMiddleware() {
  return async (req: any, res: any, next: any) => {
    try {
      const userId = req.user?.id || req.headers['x-user-id'];
      if (!userId) {
        return next();
      }

      const [flags, assignments] = await Promise.all([
        client.getUserFeatureFlags(userId, {
          context: {
            ip: req.ip,
            userAgent: req.headers['user-agent']
          }
        }),
        client.getUserAssignments(userId)
      ]);

      // Attach to request object
      req.experimentation = {
        flags,
        assignments,
        trackEvent: async (eventType: string, value?: number, metadata?: any) => {
          await client.trackEvent({
            eventType,
            userId,
            value,
            metadata: {
              ...metadata,
              path: req.path,
              method: req.method
            }
          });
        }
      };

      next();
    } catch (error) {
      console.error('Experimentation middleware error:', error);
      next();
    }
  };
}

// Usage in Express app
import express from 'express';
import { experimentationMiddleware } from './middleware/experimentation';

const app = express();

app.use(experimentationMiddleware());

app.get('/api/products', async (req, res) => {
  const { flags, trackEvent } = req.experimentation;

  // Use feature flags
  if (flags.newPricingModel) {
    // New pricing logic
  }

  // Track events
  await trackEvent('VIEW_PRODUCTS', undefined, {
    category: 'electronics'
  });

  res.json({ /* products */ });
});
```

#### 2. NestJS Integration
```typescript
// experimentation.module.ts
import { Module } from '@nestjs/common';
import { ExperimentationService } from './experimentation.service';
import { ExperimentationController } from './experimentation.controller';

@Module({
  providers: [ExperimentationService],
  controllers: [ExperimentationController],
  exports: [ExperimentationService]
})
export class ExperimentationModule {}

// experimentation.service.ts
import { Injectable } from '@nestjs/common';
import { ExperimentationClient } from 'experimentation-platform-sdk';

@Injectable()
export class ExperimentationService {
  private client: ExperimentationClient;

  constructor() {
    this.client = new ExperimentationClient({
      apiKey: process.env.API_KEY,
      baseUrl: process.env.API_URL
    });
  }

  async getUserFlags(userId: string, context?: any) {
    return this.client.getUserFeatureFlags(userId, { context });
  }

  async getUserAssignments(userId: string) {
    return this.client.getUserAssignments(userId);
  }

  async trackEvent(eventType: string, userId: string, value?: number, metadata?: any) {
    return this.client.trackEvent({
      eventType,
      userId,
      value,
      metadata
    });
  }
}

// experimentation.controller.ts
import { Controller, Get, Post, Body, Param, UseGuards } from '@nestjs/common';
import { ExperimentationService } from './experimentation.service';
import { AuthGuard } from '@nestjs/passport';

@Controller('experimentation')
@UseGuards(AuthGuard('jwt'))
export class ExperimentationController {
  constructor(private experimentationService: ExperimentationService) {}

  @Get('flags/:userId')
  async getUserFlags(@Param('userId') userId: string) {
    return this.experimentationService.getUserFlags(userId);
  }

  @Post('events')
  async trackEvent(
    @Body() body: {
      eventType: string;
      userId: string;
      value?: number;
      metadata?: any;
    }
  ) {
    return this.experimentationService.trackEvent(
      body.eventType,
      body.userId,
      body.value,
      body.metadata
    );
  }
}
```

#### 3. Next.js API Routes
```typescript
// pages/api/experimentation/flags.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { ExperimentationClient } from 'experimentation-platform-sdk';

const client = new ExperimentationClient({
  apiKey: process.env.API_KEY,
  baseUrl: process.env.API_URL
});

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const userId = req.query.userId as string;
    if (!userId) {
      return res.status(400).json({ message: 'userId is required' });
    }

    const flags = await client.getUserFeatureFlags(userId, {
      context: {
        userAgent: req.headers['user-agent'],
        ip: req.headers['x-forwarded-for'] || req.socket.remoteAddress
      }
    });

    res.status(200).json(flags);
  } catch (error) {
    console.error('Error fetching feature flags:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
}

// pages/api/experimentation/events.ts
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const { eventType, userId, value, metadata } = req.body;

    await client.trackEvent({
      eventType,
      userId,
      value,
      metadata: {
        ...metadata,
        path: req.headers.referer,
        userAgent: req.headers['user-agent']
      }
    });

    res.status(200).json({ message: 'Event tracked successfully' });
  } catch (error) {
    console.error('Error tracking event:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
}
```
