# Authentication User Guide

This guide explains how to use the authentication features of the Experimentation Platform, including registration, login, password management, and security best practices.

## Account Registration

### Registration Requirements

To create an account on the Experimentation Platform, you will need to provide:

- **Username**: 3-20 characters, alphanumeric with underscores and hyphens only
- **Email**: A valid email address you can access for verification
- **Password**: Must satisfy the following requirements:
  - Minimum 8 characters
  - At least one uppercase letter (A-Z)
  - At least one lowercase letter (a-z)
  - At least one number (0-9)
  - At least one special character (e.g., !@#$%^&*)
  - Cannot contain your username or email address
- **First Name** and **Last Name**: Your real name or preferred name

### Registration Process

1. Navigate to the registration page at `/register` or click "Sign Up" from the login page
2. Enter your details in the registration form
3. Click "Register" to submit your information
4. Check your email for a verification code
5. Enter the verification code on the confirmation page
6. Once verified, you will be redirected to the login page

### Email Verification

- Verification codes are valid for 24 hours
- If you don't receive a verification code, check your spam folder
- You can request a new code by clicking "Resend Code" on the verification page
- Your account will not be fully active until you verify your email

## Login Process

### Standard Login

1. Navigate to the login page at `/login`
2. Enter your username or email and password
3. Click "Login" to authenticate

### Login Security Features

- **Multi-Factor Authentication (MFA)**: If enabled, you will be prompted for an additional verification code
- **Session Management**: Logged in for 24 hours by default before requiring re-authentication
- **Account Protection**: Too many failed login attempts will temporarily lock your account

### After Login

Once logged in successfully:
- You will be redirected to the dashboard
- An access token is stored in your browser
- This token is used for all subsequent API requests

## Password Management

### Password Reset Process

If you forget your password:

1. Click "Forgot Password" on the login page
2. Enter your username or email
3. Check your email for a password reset code
4. Enter the code and your new password on the reset page
5. Submit the form to update your password
6. Log in with your new password

### Password Reset Notes

- Reset codes expire after 15 minutes
- New passwords must meet the same requirements as registration
- You cannot reuse your previous password
- After resetting your password, all existing sessions will be invalidated

### Changing Your Password

To change your password while logged in:

1. Go to "Account Settings" in the user menu
2. Click "Change Password"
3. Enter your current password and new password
4. Submit the form to update your password

## Using Authentication Tokens

The platform uses JWT (JSON Web Tokens) for authentication. Here's how they work:

### Token Types

- **Access Token**: Used for API authentication (short-lived, 1 hour)
- **ID Token**: Contains user identity information
- **Refresh Token**: Used to obtain new access tokens (longer-lived, 30 days)

### Sample Token Usage

When making API requests, include the access token in the Authorization header:

```javascript
// Example of an authenticated API request using fetch
async function fetchExperiments() {
  const response = await fetch('https://api.experimentation-platform.com/api/v1/experiments', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
      'Content-Type': 'application/json'
    }
  });
  
  return response.json();
}
```

### Token Refresh

If your access token expires, use the refresh token to get a new one:

```javascript
// Example of refreshing an expired token
async function refreshTokens() {
  const refreshToken = localStorage.getItem('refreshToken');
  
  const response = await fetch('https://api.experimentation-platform.com/api/v1/auth/refresh', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('accessToken', data.access_token);
    localStorage.setItem('idToken', data.id_token);
    return true;
  } else {
    // Refresh failed, user needs to log in again
    return false;
  }
}
```

## Common Error Scenarios and Solutions

### Registration Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Username already exists" | The username is taken | Choose a different username |
| "Invalid email format" | Email address is not valid | Check for typos in your email |
| "Password doesn't meet requirements" | Password is too weak | Follow the password requirements listed above |

### Login Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Incorrect username or password" | Credentials don't match | Double-check your username and password |
| "User is not confirmed" | Email not verified | Complete the verification process |
| "User not found" | Account doesn't exist | Check username or register a new account |
| "Account temporarily locked" | Too many failed attempts | Wait 15 minutes and try again |

### Token Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Token expired" | Access token has expired | Refresh the token or log in again |
| "Invalid token" | Token is malformed or tampered | Log out and log in again |
| "Refresh token expired" | Refresh token has expired | Log in again to get new tokens |

### Password Reset Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid verification code" | Code doesn't match or expired | Request a new code |
| "Password recently used" | New password same as old one | Choose a different password |
| "Code expired" | Reset code is more than 15 minutes old | Request a new code |

## Security Best Practices

To keep your account secure:

### Password Security

- Use a unique password not used on other websites
- Consider using a password manager
- Change your password periodically (every 3-6 months)
- Never share your password with anyone

### Account Protection

- Enable Multi-Factor Authentication (MFA) for additional security
- Don't share your verification codes with anyone
- Log out when using shared or public computers
- Check for HTTPS in the browser address bar before logging in

### Device Security

- Keep your devices and browsers updated
- Use antivirus software on your computers
- Be cautious when logging in from public networks
- Clear browser cookies and storage after using public computers

### Suspicious Activity

If you notice suspicious activity on your account:
1. Change your password immediately
2. Contact support at support@experimentation-platform.com
3. Check your account activity log for unauthorized actions
4. Review connected devices in account settings

---

If you encounter any issues not covered in this guide, please contact our support team.
