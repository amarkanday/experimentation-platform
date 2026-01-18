# Backend Development Guide

Backend-specific guidance for the experimentation platform FastAPI application.

## Quick Start

```bash
# Activate virtual environment (ALWAYS DO THIS FIRST!)
source /Users/ashishmarkanday/github/experimentation-platform/venv/bin/activate

# Run development server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
export APP_ENV=test TESTING=true
python -m pytest backend/tests/ -v

# Database migrations
export POSTGRES_DB=experimentation POSTGRES_SCHEMA=experimentation
python -m alembic -c app/db/alembic.ini upgrade head
```

## Directory Structure

```
backend/
├── app/
│   ├── api/           # API endpoints (REST)
│   │   ├── deps.py    # Dependencies (auth, permissions)
│   │   └── v1/        # API version 1 routes
│   ├── core/          # Core functionality
│   │   ├── config.py           # Configuration
│   │   ├── permissions.py      # RBAC system
│   │   ├── rules_engine.py     # Rules evaluation
│   │   ├── rule_compiler.py    # Rule compilation & caching
│   │   └── evaluation_cache.py # Evaluation result caching
│   ├── db/            # Database
│   │   ├── migrations/         # Alembic migrations
│   │   └── session.py          # DB session management
│   ├── models/        # SQLAlchemy models
│   │   ├── experiment.py
│   │   ├── feature_flag.py
│   │   ├── user.py
│   │   └── metrics/            # Metrics models (use full imports!)
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic layer
│   └── main.py        # FastAPI application entry
└── tests/
    ├── unit/          # Unit tests
    └── integration/   # Integration tests
```

## Import Patterns (CRITICAL)

### Always Use Full Qualified Paths

```python
# ✅ CORRECT - Full qualified imports
from backend.app.models.metrics.metric import RawMetric, MetricType
from backend.app.services.experiment_service import ExperimentService
from backend.app.core.permissions import check_permission, UserRole

# ❌ WRONG - Relative imports
from app.models.metrics.metric import RawMetric
from ..services.experiment_service import ExperimentService
```

### Why This Matters

Inconsistent imports cause Python to treat the same class as distinct objects, leading to:
- SQLAlchemy "Class is not mapped" errors
- Memory duplication
- Type checking failures

**Verification**: Run `python standardize_metrics_imports.py --check`

## Async/Sync Patterns

### Feature Flag & Report Dependencies (ASYNC)

```python
# In deps.py - these are ASYNC
async def get_feature_flag_access(...) -> FeatureFlag:
    # Check READ permission first
    if not await check_permission(current_user, "feature_flag", "READ"):
        raise HTTPException(403)
    return feature_flag

# In endpoints - use await
@router.put("/feature-flags/{flag_id}")
async def update_feature_flag(
    flag: FeatureFlag = Depends(get_feature_flag_access),
    ...
):
    # endpoint logic
```

### Experiment Dependencies (SYNC)

```python
# In deps.py - these are SYNC
def get_experiment_access(...) -> Experiment:
    check_permission(current_user, "experiment", "READ")
    return experiment

# In endpoints - no await
@router.put("/experiments/{exp_id}")
def update_experiment(
    experiment: Experiment = Depends(get_experiment_access),
    ...
):
    # endpoint logic
```

### Permission Check Order

Always check READ before UPDATE/DELETE:

```python
# ✅ CORRECT order
if not await check_permission(user, "feature_flag", "READ"):
    raise HTTPException(403, "Not authorized to view this resource")
if not await check_permission(user, "feature_flag", "UPDATE"):
    raise HTTPException(403, "Not authorized to update this resource")

# ❌ WRONG - checking UPDATE before READ
if not await check_permission(user, "feature_flag", "UPDATE"):
    raise HTTPException(403)  # Less informative error
```

## Database Operations

### Schema Configuration

Always set schema environment variables:

```bash
export POSTGRES_DB=experimentation
export POSTGRES_SCHEMA=experimentation
```

### Migration Workflow

```bash
# 1. Update SQLAlchemy model
vim app/models/experiment.py

# 2. Generate migration
alembic revision --autogenerate -m "add experiment status field"

# 3. CRITICAL: Review generated file
# - Check down_revision points to correct previous migration
# - Verify schema changes match your intent
# - Ensure schema prefix is correct

# 4. Apply migration
python -m alembic -c app/db/alembic.ini upgrade head

# 5. Verify
alembic current
alembic history --verbose | head -20
```

### Common Migration Issues

**Multiple heads:**
```bash
alembic merge -m "merge heads" revision1 revision2
```

**Database/migration mismatch:**
```bash
alembic stamp heads  # Mark current state
```

## Testing Best Practices

### Test Environment Setup

```bash
# ALWAYS activate venv first!
source /Users/ashishmarkanday/github/experimentation-platform/venv/bin/activate

# Set test environment
export APP_ENV=test
export TESTING=true

# Run tests
python -m pytest backend/tests/unit/ -v
python -m pytest backend/tests/integration/ -v
python -m pytest backend/tests/ -k "test_feature_name" -v
```

### Test Database Requirements

- PostgreSQL must be running (use Docker: `docker ps | grep postgres`)
- Connection string uses `localhost` on macOS
- Test users must have `hashed_password` set to avoid integrity errors

### Async Test Patterns

```python
import pytest

# For async functions
@pytest.mark.asyncio
async def test_feature_flag_permission():
    result = await get_feature_flag_access(...)
    assert result is not None

# For sync functions
def test_experiment_permission():
    result = get_experiment_access(...)
    assert result is not None
```

### Mocking Authentication

```python
@pytest.fixture
def admin_user(db_session):
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password="hashed_password_value",  # REQUIRED!
        is_superuser=True,
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def admin_token(admin_user, monkeypatch):
    token = "mock_admin_token"

    # Mock get_current_user
    async def mock_get_current_user():
        return admin_user
    monkeypatch.setattr("backend.app.api.deps.get_current_user",
                       mock_get_current_user)

    # Mock token decoder
    def mock_decode_token(*args, **kwargs):
        return {"sub": str(admin_user.id), "username": admin_user.username}
    monkeypatch.setattr("backend.app.core.security.decode_token",
                       mock_decode_token)

    return token
```

## Pydantic V2 Patterns

```python
from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

class ExperimentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Not class Config

    name: str
    status: str

    @field_validator("status")  # Not @validator
    @classmethod
    def validate_status(cls, v):
        if v not in ["DRAFT", "ACTIVE", "PAUSED", "COMPLETED"]:
            raise ValueError("Invalid status")
        return v

    @model_validator(mode="after")  # Not @root_validator
    def validate_dates(self):
        if self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be before end_date")
        return self

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")  # Not class Config
```

## Role-Based Access Control (RBAC)

### User Roles

- **ADMIN**: Full access to all resources
- **DEVELOPER**: Create and manage experiments/feature flags
- **ANALYST**: View all data, cannot create/modify
- **VIEWER**: Read-only access to approved resources

### Permission Checking

```python
from backend.app.core.permissions import check_permission, UserRole

# In sync context
if not check_permission(user, "experiment", "CREATE"):
    raise HTTPException(403, "Not authorized")

# In async context
if not await check_permission(user, "feature_flag", "UPDATE"):
    raise HTTPException(403, "Not authorized")
```

### Special Case: Experiment Delete

Do NOT use dependency function for delete endpoint due to status conflicts.
Instead, check permissions inline:

```python
@router.delete("/experiments/{experiment_id}")
def delete_experiment(
    experiment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Get experiment directly
    experiment = db.query(Experiment).filter_by(id=experiment_id).first()

    # Check permissions inline
    check_permission(current_user, "experiment", "DELETE")

    # Verify status
    if experiment.status != ExperimentStatus.DRAFT:
        raise HTTPException(400, "Can only delete DRAFT experiments")

    # Delete
    db.delete(experiment)
    db.commit()
```

## Code Quality Standards

```bash
# Format code
black backend/

# Sort imports
isort backend/

# Type checking
mypy backend/app/

# Linting
flake8 backend/app/

# Or use slash command:
/quality fix
```

## Performance Optimization

### Rules Engine Caching

The enhanced rules engine includes:
- **Rule compilation cache**: LRU cache (10,000 entries) for compiled rules
- **Evaluation cache**: Thread-safe LRU cache with TTL for results
- **Metrics collection**: P50, P95, P99 latency tracking

```python
from backend.app.services.rules_evaluation_service import RulesEvaluationService

service = RulesEvaluationService(
    cache_size=1000,        # Evaluation result cache size
    cache_ttl_seconds=300,  # 5 minutes TTL
    metrics_window=1000     # Sample window for metrics
)

# Evaluate with caching
result = await service.evaluate_rules_cached(
    rules=targeting_rules,
    context=user_context
)

# Batch evaluation
results = await service.batch_evaluate(
    users=user_list,
    rules=targeting_rules
)
```

## Common Development Tasks

### Adding New API Endpoint

1. Define Pydantic schema in `app/schemas/`
2. Add route in `app/api/v1/`
3. Implement business logic in `app/services/`
4. Add permission checks using dependencies or inline
5. Write unit tests in `tests/unit/api/`
6. Write integration tests in `tests/integration/`

### Adding New Model

1. Create model in `app/models/`
2. Use fully qualified imports everywhere
3. Generate migration: `alembic revision --autogenerate -m "description"`
4. Review and apply migration
5. Update schemas in `app/schemas/`
6. Add service methods in `app/services/`
7. Write comprehensive tests

### Debugging Tips

- Check logs: `docker-compose logs -f api`
- Use breakpoint() for debugging
- Run specific test: `python -m pytest backend/tests/unit/path/to/test.py::test_name -xvs`
- Clear schema cache in tests: `clear_schema_cache()`
- Verify database state: `psql` into container

## Resources

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Alembic Docs: https://alembic.sqlalchemy.org/
- FastAPI Docs: https://fastapi.tiangolo.com/
- Pydantic V2: https://docs.pydantic.dev/2.0/
