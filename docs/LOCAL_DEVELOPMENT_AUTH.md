# Local Development Authentication Guide

## Problem

When running the application locally, you may encounter this error:

```
ERROR] Get user with groups error: An error occurred (NotAuthorizedException)
when calling the GetUser operation: Invalid Access Token
```

This occurs because the application expects AWS Cognito credentials that are not configured in local development.

## Solutions

Choose one of the following solutions based on your needs:

---

## ✅ Solution 1: LocalStack (Recommended)

Use LocalStack to emulate AWS Cognito locally. This provides a full Cognito experience without AWS costs.

### Prerequisites
- Docker and Docker Compose installed
- AWS CLI installed (`brew install awscli` on macOS)

### Setup Steps

1. **Start LocalStack:**
```bash
cd /Users/ashishmarkanday/github/experimentation-platform
docker-compose up -d localstack
```

2. **Run the Cognito setup script:**
```bash
./scripts/setup_local_cognito.sh
```

This script will:
- Create a local Cognito User Pool
- Create a User Pool Client
- Create an admin group
- Create a test admin user (admin@example.com / admin123)
- Output the configuration values

3. **Update your `backend/.env` file:**

Add the values outputted by the script:
```bash
# AWS/Cognito Settings (LocalStack)
AWS_REGION=us-west-2
AWS_ENDPOINT_URL=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
COGNITO_USER_POOL_ID=<value from script>
COGNITO_CLIENT_ID=<value from script>
```

4. **Restart your backend:**
```bash
source venv/bin/activate
uvicorn backend.app.main:app --reload
```

5. **Test with the admin user:**
   - Email: `admin@example.com`
   - Password: `admin123`

### Advantages
- ✅ Full Cognito features available
- ✅ No AWS account needed
- ✅ No AWS costs
- ✅ Realistic testing environment
- ✅ Safe for development

---

## Solution 2: Real AWS Cognito

Use your actual AWS Cognito User Pool. Best for staging or if you already have Cognito set up.

### Prerequisites
- AWS account with Cognito User Pool created
- AWS credentials configured

### Setup Steps

1. **Get your Cognito credentials from AWS Console:**
   - Navigate to: AWS Console → Cognito → User Pools
   - Select your User Pool
   - Note the **User Pool ID** (e.g., `us-east-1_XXXXXXXXX`)
   - Go to "App clients" tab
   - Note the **Client ID**

2. **Update `backend/.env`:**
```bash
# AWS/Cognito Settings (Real AWS)
AWS_REGION=us-east-1  # Your AWS region
COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX  # Your pool ID
COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxx  # Your client ID

# AWS Credentials (use IAM user or temporary credentials)
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
```

3. **Restart your backend**

### Advantages
- ✅ Production-like environment
- ✅ Real user management
- ✅ Can test with actual users

### Disadvantages
- ❌ Requires AWS account
- ❌ Potential AWS costs
- ❌ Requires network access to AWS

---

## Solution 3: Development Bypass (Quick Fix)

**⚠️ WARNING: This bypasses all authentication! Use ONLY for local development.**

This solution creates a development-only auth system that doesn't require Cognito.

### Setup Steps

1. **The development auth module has been created at:**
   `backend/app/api/deps_dev.py`

2. **Update your `backend/.env`:**
```bash
# Must be set to "development" for dev auth to work
ENVIRONMENT=development

# No Cognito credentials needed!
```

3. **Modify the endpoint you're testing** to use dev dependencies:

```python
# Instead of:
from backend.app.api import deps
current_user: User = Depends(deps.get_current_active_user)

# Use:
from backend.app.api import deps_dev
current_user: User = Depends(deps_dev.get_current_active_user_dev)
```

4. **Use the development token:**

When making API requests, use this token:
```bash
# In your Authorization header:
Authorization: Bearer dev-token-admin
```

Example with curl:
```bash
curl -H "Authorization: Bearer dev-token-admin" \
     http://localhost:8000/api/v1/audit-logs/
```

### How it Works

- Creates a test admin user in your database automatically
- Accepts a special development token: `dev-token-admin`
- **Only works when `ENVIRONMENT=development`**
- Returns full admin privileges for testing

### Advantages
- ✅ Zero configuration needed
- ✅ Fast setup
- ✅ No external dependencies
- ✅ Good for quick API testing

### Disadvantages
- ❌ Not realistic for production testing
- ❌ Security disabled (development only!)
- ❌ Single user only
- ❌ Requires code changes to endpoints

---

## Comparison

| Feature | LocalStack | Real AWS | Dev Bypass |
|---------|-----------|----------|------------|
| Setup Time | Medium | Medium | Fast |
| Realistic | High | Highest | Low |
| Cost | Free | $$ | Free |
| Security | Medium | High | None |
| User Management | Yes | Yes | No |
| Best For | Development | Staging/Prod | Quick Testing |

---

## Recommended Approach

For most local development, **use LocalStack (Solution 1)**:

1. One-time setup with the script
2. Full Cognito features
3. No AWS costs
4. Safe and isolated
5. Can create multiple users and groups

---

## Troubleshooting

### LocalStack not starting

```bash
# Check LocalStack logs
docker logs experimentation-localstack

# Restart LocalStack
docker-compose restart localstack

# Recreate from scratch
docker-compose down -v
docker-compose up -d localstack
./scripts/setup_local_cognito.sh
```

### Script fails to create Cognito resources

Ensure:
1. Docker is running
2. LocalStack container is healthy: `docker ps | grep localstack`
3. Port 4566 is not in use: `lsof -i :4566`
4. AWS CLI is installed: `aws --version`

### Still getting "Invalid Access Token"

1. Check environment variables are loaded:
```bash
env | grep COGNITO
env | grep AWS
```

2. Restart your backend after updating `.env`

3. Check the auth_service.py logs for initialization warnings

4. Verify the token format is correct (JWT from Cognito)

---

## Testing Your Setup

Once configured, test authentication:

```bash
# Using LocalStack or Real AWS:
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@example.com",
    "password": "admin123"
  }'

# Using Dev Bypass:
curl -H "Authorization: Bearer dev-token-admin" \
     http://localhost:8000/api/v1/audit-logs/
```

Expected: HTTP 200 with authentication success

---

## Production Deployment

**IMPORTANT:** For production:

1. ❌ **Never** use dev bypass (Solution 3)
2. ✅ Use real AWS Cognito (Solution 2)
3. ✅ Set `ENVIRONMENT=production`
4. ✅ Use proper AWS IAM roles and policies
5. ✅ Enable MFA for admin accounts
6. ✅ Use AWS Secrets Manager for credentials

---

## Questions?

Refer to:
- `/docs/CLAUDE.md` - Development guidelines
- AWS Cognito Documentation
- LocalStack Documentation: https://docs.localstack.cloud/
