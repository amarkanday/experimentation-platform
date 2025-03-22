# Testing the FastAPI Cognito Authentication Implementation

This document outlines the testing process for the AWS Cognito authentication implementation in our FastAPI application, showing the steps and expected outcomes for each auth flow.

## Prerequisites

- FastAPI application is running on `http://localhost:8000`
- Environment variables are properly set:
  - `COGNITO_USER_POOL_ID`
  - `COGNITO_CLIENT_ID`
  - `AWS_REGION`

## Test Cases

### 1. Health Check

Verifying that the API is responding correctly:

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status":"healthy"}
```

### 2. User Registration

Creating a new user account:

```bash
curl -X POST http://localhost:8000/api/v1/auth/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1",
    "password": "Test@Password123",
    "email": "your-email@example.com",
    "given_name": "Test",
    "family_name": "User"
  }'
```

**Expected Response:**
```json
{
  "user_id": "some-uuid",
  "confirmed": false,
  "message": "User registration successful. Please check your email for verification code."
}
```

### 3. Email Confirmation

Confirming a user account with verification code:

```bash
curl -X POST http://localhost:8000/api/v1/auth/auth/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1",
    "confirmation_code": "123456"
  }'
```

**Expected Response:**
```json
{
  "message": "Account confirmed successfully. You can now sign in.",
  "confirmed": true
}
```

### 4. Sign In

Authenticating and receiving JWT tokens:

```bash
curl -X POST http://localhost:8000/api/v1/auth/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser1&password=Test@Password123"
```

**Expected Response:**
```json
{
  "access_token": "eyJra...",
  "token_type": "bearer",
  "refresh_token": "eyJjd...",
  "id_token": "eyJra...",
  "expires_in": 3600
}
```

### 5. Password Reset Flow

#### Step 1: Initiate password reset

```bash
curl -X POST http://localhost:8000/api/v1/auth/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser1"
  }'
```

**Expected Response:**
```json
{
  "message": "Password reset code has been sent to your email."