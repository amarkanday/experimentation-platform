# Authentication Developer Documentation

This document provides technical documentation for developers integrating with and extending the AWS Cognito authentication system in the Experimentation Platform.

## Architecture Overview

The authentication system is built on AWS Cognito and provides these key capabilities:
- User registration and account management
- Secure authentication with JWT tokens
- Password reset functionality
- Authorization and permission control
- Token refresh mechanism

### Components

1. **AWS Cognito User Pool** - Manages user directory and authentication
2. **Auth Service** - Backend service that interfaces with Cognito APIs
3. **Auth Middleware** - Validates JWT tokens and enforces permissions
4. **Auth API Endpoints** - FastAPI routes for authentication operations

## Cognito Configuration

### User Pool Configuration

Our Cognito User Pool is configured with the following settings:

```typescript
// CDK Configuration (simplified)
const userPool = new cognito.UserPool(this, "ExperimentationUserPool", {
  userPoolName: `experimentation-platform-users-${environment}`,
  selfSignUpEnabled: true,
  signInAliases: {
    email: true,
    username: true,
  },
  passwordPolicy: {
    minLength: 8,
    requireLowercase: true,
    requireUppercase: true,
    requireDigits: true,
    requireSymbols: true,
    tempPasswordValidity: Duration.days(7),
  },
  accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
  autoVerify: { email: true },
  mfa: cognito.Mfa.OPTIONAL,
  mfaSecondFactor: {
    sms: true,
    otp: true,
  },
  standardAttributes: {
    email: { required: true, mutable: true },
    givenName: { required: true, mutable: true },
    familyName: { required: true, mutable: true },
  },
  customAttributes: {
    company: new cognito.StringAttribute({ mutable: true }),
    role: new cognito.StringAttribute({ mutable: true }),
  }
});
```

### App Client Configuration

```typescript
// CDK Configuration (simplified)
const userPoolClient = new cognito.UserPoolClient(this, "ExperimentationClient", {
  userPool,
  authFlows: {
    userPassword: true,
    userSrp: true,
    refreshToken: true,
  },
  supportedIdentityProviders: [
    cognito.UserPoolClientIdentityProvider.COGNITO,
  ],
  oAuth: {
    flows: {
      authorizationCodeGrant: true,
      implicitCodeGrant: true,
    },
    scopes: [
      cognito.OAuthScope.EMAIL,
      cognito.OAuthScope.OPENID,
      cognito.OAuthScope.PROFILE,
    ],
    callbackUrls: [
      'http://localhost:3000/callback',
      'https://app.experimentation-platform.example.com/callback',
    ],
    logoutUrls: [
      'http://localhost:3000/',
      'https://app.experimentation-platform.example.com/',
    ],
  },
  preventUserExistenceErrors: true,
  accessTokenValidity: Duration.hours(1),
  idTokenValidity: Duration.hours(1),
  refreshTokenValidity: Duration.days(30),
});
```

## API Reference

### Authentication Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/auth/signup` | POST | Register a new user | No |
| `/auth/confirm` | POST | Confirm user registration | No |
| `/auth/token` | POST | Authenticate and get tokens | No |
| `/auth/forgot-password` | POST | Initiate password reset | No |
| `/auth/reset-password` | POST | Complete password reset | No |
| `/auth/refresh` | POST | Refresh access token | No |
| `/auth/logout` | POST | Invalidate tokens | Yes |
| `/auth/me` | GET | Get current user profile | Yes |

### Detailed API Documentation

#### User Registration

**Request:**
```http
POST /api/v1/auth/signup
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecureP@ssw0rd",
  "email": "john.doe@example.com",
  "given_name": "John",
  "family_name": "Doe",
  "company": "ACME Inc"
}
```

**Response:**
```json
{
  "user_id": "a1b2c3d4-5678-90ab-cdef-ghijklmnopqr",
  "confirmed": false,
  "message": "User registration successful. Please check your email for verification code."
}
```

#### Email Confirmation

**Request:**
```http
POST /api/v1/auth/confirm
Content-Type: application/json

{
  "username": "johndoe",
  "confirmation_code": "123456"
}
```

**Response:**
```json
{
  "message": "Account confirmed successfully. You can now sign in.",
  "confirmed": true
}
```

#### User Authentication

**Request:**
```http
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=johndoe&password=SecureP@ssw0rd
```

**Response:**
```json
{
  "access_token": "eyJraWQiOiJxdUF4eVJUZHZ1...",
  "id_token": "eyJraWQiOiJzXC9cL3hsK1BLc...",
  "refresh_token": "eyJjdHkiOiJKV1QiLCJlbm...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### Password Reset Request

**Request:**
```http
POST /api/v1/auth/forgot-password
Content-Type: application/json

{
  "username": "johndoe"
}
```

**Response:**
```json
{
  "message": "Password reset code has been sent to your email."
}
```

#### Complete Password Reset

**Request:**
```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "username": "johndoe",
  "confirmation_code": "123456",
  "new_password": "NewSecureP@ssw0rd"
}
```

**Response:**
```json
{
  "message": "Password has been reset successfully. You can now sign in."
}
```

#### Token Refresh

**Request:**
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJjdHkiOiJKV1QiLCJlbm..."
}
```

**Response:**
```json
{
  "access_token": "eyJraWQiOiJjNTc5...",
  "id_token": "eyJraWQiOiJuU3A5d...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

#### User Logout

**Request:**
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJraWQiOiJxdUF4eVJUZHZ1...
```

**Response:**
```json
{
  "message": "You have been signed out successfully."
}
```

#### Get User Profile

**Request:**
```http
GET /api/v1/auth/me
Authorization: Bearer eyJraWQiOiJxdUF4eVJUZHZ1...
```

**Response:**
```json
{
  "username": "johndoe",
  "attributes": {
    "sub": "a1b2c3d4-5678-90ab-cdef-ghijklmnopqr",
    "email": "john.doe@example.com",
    "email_verified": true,
    "given_name": "John",
    "family_name": "Doe",
    "company": "ACME Inc"
  }
}
```

## Authentication Flow Implementation

### 1. Authentication Service

The `CognitoAuthService` class handles all interactions with the AWS Cognito API:

```python
# Excerpt from app/services/auth_service.py

class CognitoAuthService:
    def __init__(self):
        self.user_pool_id = os.environ.get('COGNITO_USER_POOL_ID')
        self.client_id = os.environ.get('COGNITO_CLIENT_ID')
        self.client = boto3.client('cognito-idp')
    
    def sign_up(self, username, password, email, given_name, family_name, **additional_attributes):
        try:
            user_attributes = [
                {'Name': 'email', 'Value': email},
                {'Name': 'given_name', 'Value': given_name},
                {'Name': 'family_name', 'Value': family_name},
            ]
            
            # Add additional attributes
            for key, value in additional_attributes.items():
                if value:
                    user_attributes.append({'Name': key, 'Value': str(value)})
            
            response = self.client.sign_up(
                ClientId=self.client_id,
                Username=username,
                Password=password,
                UserAttributes=user_attributes
            )
            
            return {
                "user_id": response['UserSub'],
                "confirmed": False,
                "message": "User registration successful. Please check your email for verification code."
            }
        except Exception as e:
            # Error handling logic
            raise ValueError(str(e))
```

### 2. JWT Token Validation Middleware

```python
# Excerpt from app/middleware/auth.py

class CognitoJWTValidator:
    def __init__(self, region, user_pool_id, client_id):
        self.region = region
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
        
    @lru_cache(maxsize=1)
    def _get_jwks(self):
        response = requests.get(self.jwks_url)
        return response.json()
        
    def validate_token(self, token):
        # Extract token header
        header = jwt.get_unverified_header(token)
        kid = header['kid']
        
        # Find the key
        key_data = next((k for k in self._get_jwks()['keys'] if k['kid'] == kid), None)
        if not key_data:
            raise ValueError("Invalid token: Key ID not found")
            
        # Convert to PEM format
        public_key = jwk.construct(key_data).to_pem().decode('utf-8')
        
        # Validate token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=self.client_id,
            issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
        )
        
        return payload
```

### 3. Protected Route Decorator

```python
# Excerpt from app/api/decorators.py

def require_auth(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = auth_header.split("Bearer ")[1]
        
        try:
            # Validate token
            payload = jwt_validator.validate_token(token)
            
            # Add user info to request state
            request.state.user = payload
            
            # Call the original route handler
            return await func(request, *args, **kwargs)
            
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    return wrapper
```

## Common Integration Patterns

### Frontend Login Integration

```javascript
// Example React authentication hook
import { useState } from 'react';

export function useAuth() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const login = async (username, password) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await fetch('/api/v1/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }
      
      // Store tokens
      localStorage.setItem('accessToken', data.access_token);
      localStorage.setItem('idToken', data.id_token);
      localStorage.setItem('refreshToken', data.refresh_token);
      
      return data;
    } catch (error) {
      setError(error.message);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };
  
  // Other auth methods (logout, register, etc.)
  
  return {
    isLoading,
    error,
    login,
    // Other methods
  };
}
```

### Authenticated API Requests

```javascript
// Example authenticated API client
const apiClient = {
  async fetch(url, options = {}) {
    // Get the access token
    const token = localStorage.getItem('accessToken');
    
    // Set up headers
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    // Add Authorization header if we have a token
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    
    // Make the request
    const response = await fetch(url, {
      ...options,
      headers,
    });
    
    // Handle 401 Unauthorized errors (token expired)
    if (response.status === 401) {
      // Try to refresh the token
      const refreshed = await this.refreshToken();
      
      // If refresh succeeded, retry the request with new token
      if (refreshed) {
        return this.fetch(url, options);
      }
      
      // If refresh failed, redirect to login
      window.location.href = '/login';
      return null;
    }
    
    return response;
  },
  
  async refreshToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    
    if (!refreshToken) {
      return false;
    }
    
    try {
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      
      if (!response.ok) {
        return false;
      }
      
      const data = await response.json();
      
      // Update tokens
      localStorage.setItem('accessToken', data.access_token);
      localStorage.setItem('idToken', data.id_token);
      
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  },
};
```

## Security Considerations

### Token Storage

- **Access Tokens**: Store in memory or short-lived storage
- **ID Tokens**: Store in memory or short-lived storage
- **Refresh Tokens**: Store in secure HTTP-only cookies or secure storage

### CSRF Protection

- Use the SameSite cookie attribute
- Implement CSRF tokens for sensitive operations
- Validate the origin of requests

### Token Validation

- Always validate token signatures
- Verify token issuer and audience
- Check token expiration time
- Validate token against expected claims

### Error Handling

- Do not expose detailed error information to clients
- Log authentication failures for monitoring
- Implement rate limiting for authentication endpoints

## Troubleshooting

### Common JWT Validation Issues

1. **"Token expired"**
   - Access token has exceeded its validity period
   - Solution: Refresh the token or require re-authentication

2. **"Invalid signature"**
   - Token has been tampered with or incorrectly signed
   - Solution: Ensure correct JWKS URL and proper JWT library usage

3. **"Invalid issuer"**
   - Mismatch between token issuer and expected issuer
   - Solution: Verify correct User Pool ID and region in configurations

4. **"Invalid audience"**
   - The token's audience claim doesn't match the expected client ID
   - Solution: Check Client ID configuration in both Cognito and application

## Further Resources

- [AWS Cognito Developer Guide](https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html)
- [JWT.io](https://jwt.io/) - Useful for debugging JWT tokens
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
