# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an AWS-based experimentation platform for A/B testing and feature flags with real-time evaluation capabilities. The platform enables data-driven decisions through robust experimentation and feature management.

## Project Structure

- **backend/**: FastAPI Python services with comprehensive APIs for experiments, feature flags, users, and analytics
- **frontend/**: Next.js React application for experiment management and analytics dashboards
- **infrastructure/**: AWS CDK infrastructure definitions for deployment
- **sdk/**: Client SDKs (JavaScript and Python) for integrating with applications
- **docs/**: Comprehensive project documentation
- **lambda/**: AWS Lambda functions for real-time operations

## Development Commands

### Backend (Python)

```bash
# Setup environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Testing
pytest  # Run all tests
pytest backend/tests/unit/  # Unit tests only
pytest backend/tests/integration/  # Integration tests only

# Code quality
black .  # Format code
isort .  # Sort imports
mypy .   # Type checking
flake8 . # Linting

# Database migrations
python -m alembic -c app/db/alembic.ini upgrade head
python -m alembic -c app/db/alembic.ini revision --autogenerate -m "description"
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev    # Development server
npm test       # Run tests
npm run build  # Production build
```

### Infrastructure (AWS CDK)

```bash
cd infrastructure
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
cdk deploy --all
```

### Docker Development

```bash
# Start local development environment
docker-compose up -d

# View logs
docker-compose logs -f
```

## Architecture

The platform uses a modern microservices architecture:

### Backend Services
- **FastAPI Application**: Main API server with comprehensive endpoints for experiments, feature flags, users, metrics, and safety monitoring
- **Background Schedulers**: Automated systems for experiment scheduling, rollout management, metrics collection, and safety monitoring
- **Lambda Functions**: Real-time services for experiment assignment, feature flag evaluation, and event processing

### Key Backend Components
- **API Layer**: RESTful endpoints organized by resource type (experiments, feature flags, users, etc.)
- **Services Layer**: Business logic for experiments, feature flags, authentication, safety monitoring
- **Data Layer**: SQLAlchemy models with PostgreSQL backend
- **Authentication**: AWS Cognito integration with role-based access control (RBAC)
- **Middleware**: Security headers, request logging, metrics collection, error tracking

### Database Architecture
- **Primary Database**: PostgreSQL (Aurora) for core application data
- **Caching**: Redis (ElastiCache) for session management and caching
- **Analytics**: Kinesis streams with Lambda processors feeding into OpenSearch
- **Time-series Data**: Specialized storage for metrics and events

### Frontend Architecture
- **Next.js**: React-based dashboard for experiment and feature flag management
- **Components**: Reusable UI components for experiments, feature flags, and analytics
- **API Integration**: TypeScript client services for backend communication

## Development Guidelines

### Python/Backend Standards
- Use Python 3.9+ with type annotations
- Follow PEP 8 style guidelines
- Use Pydantic v2 patterns (field_validator, model_validator, ConfigDict)
- Import with full paths: `from backend.app.models.metrics.metric import RawMetric`
- Never use relative imports like `from app.models...`

### Database Operations
- Use SQLAlchemy for all database operations
- Include schema in table definitions
- Use Alembic for migrations: `alembic revision --autogenerate -m "description"`
- Set proper environment variables: `POSTGRES_DB=experimentation POSTGRES_SCHEMA=experimentation`

### Testing Requirements
- Write comprehensive tests for all new features
- Use `pytest` with appropriate markers (unit, integration, api)
- Clear schema cache between tests with `clear_schema_cache()`
- Ensure PostgreSQL is running locally before tests
- Activate virtualenv: `cd /Users/ashishmarkanday/github/experimentation-platform && source venv/bin/activate`
- Set test environment: `APP_ENV=test TESTING=true`

### Authentication & Permissions
- Feature flag and report dependencies are async (use `await`)
- Experiment dependencies are synchronous
- Use role-based access control (ADMIN, DEVELOPER, ANALYST, VIEWER)
- Permission checking: `check_permission(user, resource_type, action)`
- Mock authentication in tests with proper user objects including `hashed_password`

### Key Implementation Notes

#### Experiment Scheduling
- Experiments support automatic start/end date scheduling
- Background scheduler runs every 15 minutes checking for state transitions
- API endpoint: `PUT /api/v1/experiments/{experiment_id}/schedule`
- Must be in DRAFT or PAUSED status to schedule

#### Feature Flag Rollout Schedules
- Gradual rollout system with configurable stages
- API endpoints under `/api/v1/rollout-schedules`
- Background scheduler processes active rollouts
- Supports time-based, metric-based, and manual triggers

#### Safety Monitoring
- Automated safety checks for feature flags monitoring error rates, latency
- API endpoints under `/api/v1/safety`
- Rollback mechanism for problematic feature flags
- Comprehensive safety reporting

#### Metrics Import Standards
- Always use fully qualified imports: `from backend.app.models.metrics.metric import RawMetric, MetricType`
- Avoid re-exports in `__init__.py` files
- Run `python standardize_metrics_imports.py --check` to verify consistency

## Monitoring & Deployment

### CloudWatch Integration
```bash
# Create log groups
aws logs create-log-group --log-group-name /experimentation-platform/api
aws logs create-log-group --log-group-name /experimentation-platform/services
aws logs create-log-group --log-group-name /experimentation-platform/errors

# Deploy monitoring dashboards
cd infrastructure/cloudwatch
./deploy-dashboards.sh
```

### Application URLs
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Common Development Tasks

### Running Single Tests
```bash
# Run specific test file
python -m pytest backend/tests/unit/services/test_experiment_scheduler.py -v

# Run tests with specific marker
pytest -m "unit" -v
```

### Database Operations
```bash
# Check migration history
python -m alembic -c app/db/alembic.ini history

# Merge conflicting migrations
alembic merge -m "merge heads" revision1 revision2

# Mark current database state
alembic stamp heads
```

### Debugging Common Issues
- Database connections must use `localhost` on macOS
- Clear caches when tests fail unexpectedly: `clear_schema_cache()`
- For "multiple heads" migration errors, create merge migration
- Watch for duplicate SQLAlchemy relationship definitions
- Ensure proper async/await usage in permission functions

## Detailed Development Guidelines (from Cursor Configuration)

### Code Style Standards
- Follow PEP 8 for Python code
- Use type annotations for all functions and methods
- Document public functions with comprehensive docstrings
- Use Pydantic v2 patterns consistently:
  - Replace `validator` with `field_validator`
  - Replace class-based `Config` with `model_config = ConfigDict(...)`
  - Use `model_validator` for complex validations
  - Import from correct paths: `from pydantic import field_validator, model_validator, ConfigDict`
  - Use `from pydantic_settings import BaseSettings, SettingsConfigDict` for settings

### Critical Database Migration Guidelines
- Migration files are located in `backend/app/db/migrations/versions/`
- When creating new migrations:
  - Use `alembic revision --autogenerate -m "description"` to generate migration files
  - **Always** check the generated file for accuracy, especially for complex changes
  - **Verify** that `down_revision` points to the correct previous migration ID
  - **Always use revision IDs, not migration names**, in the `down_revision` field
- Running migrations:
  - Use `python -m alembic -c app/db/alembic.ini upgrade head` to apply migrations
  - Use `python -m alembic -c app/db/alembic.ini history` to view migration history
  - Set environment variables properly: `POSTGRES_DB=experimentation POSTGRES_SCHEMA=experimentation`
- Migration troubleshooting:
  - For "multiple heads" errors, create a merge migration with `alembic merge -m "merge heads" revision1 revision2`
  - For database/migration mismatches, use `alembic stamp heads` to mark the current state
  - **Always verify migration chain integrity before deploying**

### Metrics Model Import Standards (Critical)
**Issue**: Inconsistent import paths for metrics models (especially `RawMetric`) cause Python to treat them as distinct classes, resulting in:
- Memory duplication
- SQLAlchemy "Class is not mapped" errors
- Type checking failures
- Unexpected behavior during runtime

**Solution & Prevention**:
1. **Standardized Import Paths**: Always use fully qualified imports: `from backend.app.models.metrics.metric import RawMetric, MetricType`
2. **Never use relative imports** like `from app.models.metrics...`
3. **Avoid Re-exports**: Don't re-export classes in `__init__.py` files; import directly from the defining module
4. **Verification**: Run `python standardize_metrics_imports.py --check` to detect inconsistencies
5. **Testing**: Run `python -m pytest backend/tests/unit/metrics/test_metrics_imports.py` to verify imports

### Permission System Architecture

#### Role-Based Access Control (RBAC)
The `core/permissions.py` module implements a comprehensive RBAC system with four roles:
- **ADMIN**: Full access to all resources and actions
- **DEVELOPER**: Can create and manage experiments and feature flags
- **ANALYST**: Can view all data but cannot create or modify resources
- **VIEWER**: Read-only access to approved resources

#### Critical Permission Implementation Notes
**Experiment Delete Endpoint Special Case**:
- **Do NOT use** `can_delete_experiment` dependency function in the `delete_experiment` endpoint
- **Design conflict**: The dependency chain requires ACTIVE experiments but delete endpoint requires DRAFT status
- **Solution**: Use inline permission checks directly within the endpoint:
  - Accept required `experiment_key` query parameter
  - Retrieve experiment directly from database
  - Perform permission checks in the endpoint
  - Check experiment status (must be DRAFT)

#### Feature Flag Permissions
- Feature flags use ownership-based permission model
- Endpoints requiring authentication use `deps.get_current_active_user`
- API endpoints for feature flag evaluation use API key authentication via `deps.get_api_key`
- Feature flag permissions are implemented as **async functions** in `deps.py`:
  - `get_feature_flag_access`: Checks if user can access a feature flag (requires `await`)
  - `can_create_feature_flag`: Checks if user can create a feature flag (requires `await`)
  - `can_update_feature_flag`: Checks if user can update a feature flag (requires `await`)
  - `can_delete_feature_flag`: Checks if user can delete a feature flag (requires `await`)

### Async/Sync Pattern Guidelines
- **Feature flag and report-related dependencies are asynchronous** (use `await`)
- **Experiment-related dependencies are synchronous**
- When testing async functions:
  - Use `@pytest.mark.asyncio` decorator on test functions
  - Use `async def` for test function declarations
  - Use `await` when calling async functions
- **Critical**: Check for READ permission before UPDATE permission in the correct order
- Don't mix async and sync patterns incorrectly - follow the implementation in `deps.py`

### Test Environment Configuration

#### Database Setup Requirements
- Ensure PostgreSQL is running locally in Docker for tests
- Database connection string should use `localhost` on macOS
- Test users must have a `hashed_password` value set to avoid integrity errors

#### Complete Authentication Mocking for API Tests
For API tests that use tokens, mock multiple components of the auth system:

1. Mock the `get_current_user` and `get_current_active_user` dependencies
2. Mock token decoding to bypass AWS Cognito validation
3. Mock the Cognito auth service to return user data with appropriate groups

**Example comprehensive auth mocking**:
```python
@pytest.fixture
def admin_token(admin_user, monkeypatch):
    token = "mock_admin_token"

    # Mock get_current_user
    async def mock_get_current_user():
        return admin_user
    monkeypatch.setattr("backend.app.api.deps.get_current_user", mock_get_current_user)

    # Mock get_current_active_user
    def mock_get_current_active_user():
        return admin_user
    monkeypatch.setattr("backend.app.api.deps.get_current_active_user", mock_get_current_active_user)

    # Mock auth_service.get_user_with_groups
    def mock_get_user_with_groups(*args, **kwargs):
        return {
            "username": admin_user.username,
            "attributes": {"email": admin_user.email},
            "groups": ["admin-group"]  # This will map to ADMIN role
        }
    monkeypatch.setattr("backend.app.services.auth_service.CognitoAuthService.get_user_with_groups",
                       mock_get_user_with_groups)

    # Mock token decoder
    def mock_decode_token(*args, **kwargs):
        return {"sub": str(admin_user.id), "username": admin_user.username}
    monkeypatch.setattr("backend.app.core.security.decode_token", mock_decode_token)

    return token
```

#### Permission Testing Patterns
- Test both regular users and superusers when creating test cases
- Verify that proper 403 responses are returned when unauthorized actions are attempted
- Use mock objects that accurately represent actual objects including ownership properties
- All permission tests should validate that:
  - ADMIN users can perform all actions
  - DEVELOPER users can create and manage resources
  - ANALYST users can view but not modify resources
  - VIEWER users have read-only access
  - Unauthorized actions return 403 Forbidden responses

**For feature flag and report tests**:
- Use `@pytest.mark.asyncio` decorator
- Define test functions as `async def test_function_name`
- Use `await` when calling async dependency functions
- Properly mock both `check_permission` and `check_ownership` in permissions tests

**For experiment tests**:
- Use regular synchronous test functions
- Call dependency functions directly without `await`

### Safety Monitoring System

#### Database Schema
The safety monitoring system uses three main tables:
1. **safety_settings**: Global safety configuration
2. **feature_flag_safety_configs**: Per-feature flag safety configuration
3. **safety_rollback_records**: History of safety-triggered rollbacks

#### API Testing Patterns
```python
# For superuser endpoints
with patch("backend.app.api.deps.get_current_superuser", return_value=mock_user):
    response = client.get("/api/v1/safety/settings")

# For rollback endpoints, also mock the permission check
with patch("backend.app.core.permissions.check_permission", return_value=True):
    with patch("backend.app.api.deps.get_current_active_user", return_value=mock_user):
        response = client.post(f"/api/v1/safety/rollback/{feature_flag_id}")
```