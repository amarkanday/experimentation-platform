# Environment Configuration Setup Guide

This guide explains how to set up the environment configuration for the Experimentation Platform.

## Overview

The platform uses Pydantic Settings to manage environment-specific configuration. The setup includes:

1. A base settings class with common configurations
2. Environment-specific settings classes (development, testing, production)
3. Environment file templates for different environments
4. Logic to determine the current environment and load appropriate settings

## Setup Steps

### 1. Create Environment Files

Create these files in the project root:

- `.env` - Base environment variables (development)
- `.env.test` - Testing environment variables
- `.env.prod` - Production environment variables (for deployment)

You can use the provided templates as a starting point.

### 2. Environment Variables

The most important environment variables to configure:

#### Database Connection
```
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=experimentation
POSTGRES_PORT=5432
POSTGRES_SCHEMA=experimentation
```

#### Redis Connection
```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0
```

#### Application Settings
```
PROJECT_NAME="Experimentation Platform"
ENVIRONMENT=development  # or testing, production
DEBUG=true              # set to false in production
LOG_LEVEL=DEBUG         # INFO, WARNING, ERROR in production
```

#### Security Settings
```
SECRET_KEY=your_secret_key  # Use a strong random string in production
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### 3. Environment Selection

The application determines which environment to use based on the `ENVIRONMENT` variable:

- If not set, defaults to `development`
- Valid values: `development`, `testing`, `production`

Set this in your shell, deployment configuration, or .env file:

```bash
# For development (default)
export ENVIRONMENT=development

# For testing
export ENVIRONMENT=testing

# For production
export ENVIRONMENT=production
```

### 4. Production Configuration

For production deployment:

1. **Never commit production credentials to version control**
2. Use a secure method to provide the `.env.prod` file or environment variables
3. Ensure the following production values are properly set:
   - `SECRET_KEY` (generate a strong random string)
   - `POSTGRES_PASSWORD` (use a strong password)
   - `REDIS_PASSWORD` (if applicable)
   - `FIRST_SUPERUSER_PASSWORD` (for the admin user)
   - `DEBUG=false`
   - `LOG_LEVEL=WARNING` or `ERROR`

## Accessing Settings in Code

The settings are accessible throughout the application by importing the `settings` instance:

```python
from backend.app.core.config import settings

# Use settings
db_connection = settings.SQLALCHEMY_DATABASE_URI
app_name = settings.PROJECT_NAME
```

## Extending the Configuration

To add new configuration options:

1. Add the new setting to the `BaseAppSettings` class in `config.py`
2. Provide a default value
3. Override in environment-specific classes if needed
4. Update environment file templates with the new variable

Example:
```python
# In config.py
class BaseAppSettings(BaseSettings):
    # ... existing settings
    
    # New setting
    CACHE_TTL_SECONDS: int = 300  # Default 5 minutes
```

## Troubleshooting

- If settings aren't loading correctly, check that your environment file exists and has the correct format
- Verify environment variables are set correctly
- Check file permissions on the .env files
- Enable DEBUG mode to see more detailed logs
