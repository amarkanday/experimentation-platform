# Execution & Testing Plan: EP-243A Backend Toggle API

## 📋 Implementation Execution Plan

### Phase 1: Database Foundation (Days 1-2)

#### 1.1 Database Schema Implementation
```sql
-- Create audit_logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES users(id),
    user_email VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_name VARCHAR(255) NOT NULL,
    old_value VARCHAR(50),
    new_value VARCHAR(50),
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_action_type ON audit_logs(action_type);
```

**Tasks:**
- [ ] Create Alembic migration script
- [ ] Test migration on local database
- [ ] Test migration on staging database
- [ ] Verify index creation and performance
- [ ] Create rollback migration script

#### 1.2 Database Models
```python
# backend/app/models/audit_log.py
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    user_email = Column(String(255), nullable=False)
    action_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    entity_name = Column(String(255), nullable=False)
    old_value = Column(String(50))
    new_value = Column(String(50))
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="audit_logs")
```

**Tasks:**
- [ ] Create AuditLog model in `backend/app/models/audit_log.py`
- [ ] Update `backend/app/models/__init__.py` to include AuditLog
- [ ] Add relationship to User model
- [ ] Test model creation and relationships

### Phase 2: Core Services Implementation (Days 3-4)

#### 2.1 Audit Service
```python
# backend/app/services/audit_service.py
import asyncio
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from backend.app.models.audit_log import AuditLog
from backend.app.schemas.audit_log import AuditLogCreate, AuditLogResponse

class AuditService:
    @staticmethod
    async def log_toggle_operation(
        db: Session,
        user_id: UUID,
        user_email: str,
        action_type: str,
        entity_id: UUID,
        entity_name: str,
        old_value: str,
        new_value: str,
        reason: Optional[str] = None
    ) -> UUID:
        """Log a toggle operation asynchronously."""

        audit_log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action_type=action_type,
            entity_type="feature_flag",
            entity_id=entity_id,
            entity_name=entity_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log.id

    @staticmethod
    def get_audit_logs(
        db: Session,
        user_id: Optional[UUID] = None,
        entity_id: Optional[UUID] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """Get paginated audit logs with filters."""

        query = db.query(AuditLog)

        # Apply filters
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
        if from_date:
            query = query.filter(AuditLog.timestamp >= from_date)
        if to_date:
            query = query.filter(AuditLog.timestamp <= to_date)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        offset = (page - 1) * limit
        logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()

        return logs, total
```

**Tasks:**
- [ ] Implement AuditService class
- [ ] Create Pydantic schemas for audit logs
- [ ] Add error handling and logging
- [ ] Create unit tests for all methods

#### 2.2 Toggle Service
```python
# backend/app/services/toggle_service.py
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from backend.app.services.audit_service import AuditService
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

class ToggleService:
    @staticmethod
    async def toggle_feature_flag(
        db: Session,
        feature_flag_id: UUID,
        user_id: UUID,
        user_email: str,
        reason: Optional[str] = None
    ) -> FeatureFlag:
        """Toggle a feature flag and log the operation."""

        try:
            # Get the feature flag
            feature_flag = db.query(FeatureFlag).filter(
                FeatureFlag.id == feature_flag_id
            ).first()

            if not feature_flag:
                raise ValueError(f"Feature flag not found: {feature_flag_id}")

            # Store old value
            old_status = feature_flag.status.value

            # Toggle the status
            new_status = (
                FeatureFlagStatus.DISABLED
                if feature_flag.status == FeatureFlagStatus.ENABLED
                else FeatureFlagStatus.ENABLED
            )

            feature_flag.status = new_status
            feature_flag.updated_at = datetime.utcnow()

            # Commit the change
            db.commit()
            db.refresh(feature_flag)

            # Log the operation asynchronously
            await AuditService.log_toggle_operation(
                db=db,
                user_id=user_id,
                user_email=user_email,
                action_type=f"toggle_{new_status.value}",
                entity_id=feature_flag_id,
                entity_name=feature_flag.name,
                old_value=old_status,
                new_value=new_status.value,
                reason=reason
            )

            logger.info(f"Feature flag {feature_flag_id} toggled to {new_status.value} by {user_email}")

            return feature_flag

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error toggling feature flag {feature_flag_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error toggling feature flag {feature_flag_id}: {str(e)}")
            raise
```

**Tasks:**
- [ ] Implement ToggleService class
- [ ] Add transaction management
- [ ] Implement error handling and rollback
- [ ] Create unit tests with mocked dependencies

### Phase 3: API Endpoints Implementation (Days 5-6)

#### 3.1 Toggle Endpoints
```python
# backend/app/api/v1/endpoints/toggle.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from backend.app.api import deps
from backend.app.services.toggle_service import ToggleService
from backend.app.schemas.feature_flag import FeatureFlagResponse
from backend.app.schemas.toggle import ToggleRequest
from backend.app.models.user import User
from backend.app.core.permissions import require_permission

router = APIRouter()

@router.post("/feature-flags/{feature_flag_id}/toggle", response_model=FeatureFlagResponse)
async def toggle_feature_flag(
    feature_flag_id: UUID,
    request: ToggleRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Toggle a feature flag status."""

    # Check permissions
    require_permission(current_user, "toggle_feature_flags")

    try:
        feature_flag = await ToggleService.toggle_feature_flag(
            db=db,
            feature_flag_id=feature_flag_id,
            user_id=current_user.id,
            user_email=current_user.email,
            reason=request.reason
        )

        return feature_flag

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle feature flag"
        )

@router.post("/feature-flags/{feature_flag_id}/enable", response_model=FeatureFlagResponse)
async def enable_feature_flag(
    feature_flag_id: UUID,
    request: ToggleRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Enable a feature flag."""
    # Implementation similar to toggle but specific to enable
    pass

@router.post("/feature-flags/{feature_flag_id}/disable", response_model=FeatureFlagResponse)
async def disable_feature_flag(
    feature_flag_id: UUID,
    request: ToggleRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Disable a feature flag."""
    # Implementation similar to toggle but specific to disable
    pass
```

#### 3.2 Audit Log Endpoints
```python
# backend/app/api/v1/endpoints/audit_logs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from uuid import UUID

from backend.app.api import deps
from backend.app.services.audit_service import AuditService
from backend.app.schemas.audit_log import AuditLogListResponse
from backend.app.models.user import User
from backend.app.core.permissions import require_permission

router = APIRouter()

@router.get("/audit-logs", response_model=AuditLogListResponse)
def get_audit_logs(
    user_id: Optional[UUID] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Get paginated audit logs with filters."""

    # Check permissions
    require_permission(current_user, "view_audit_logs")

    logs, total = AuditService.get_audit_logs(
        db=db,
        user_id=user_id,
        entity_id=entity_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        limit=limit
    )

    return {
        "items": logs,
        "total": total,
        "page": page,
        "limit": limit
    }
```

**Tasks:**
- [ ] Implement all toggle endpoints
- [ ] Implement audit log endpoints
- [ ] Add comprehensive error handling
- [ ] Create Pydantic request/response schemas
- [ ] Add permission decorators

### Phase 4: Integration & Testing (Days 7-8)

#### 4.1 Permission Middleware
```python
# backend/app/core/permissions.py
from fastapi import HTTPException, status
from backend.app.models.user import User

def require_permission(user: User, permission: str):
    """Check if user has required permission."""
    if not user.has_permission(permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions: {permission} required"
        )
```

**Tasks:**
- [ ] Implement permission checking logic
- [ ] Add permission-based middleware
- [ ] Create permission constants
- [ ] Test permission validation

---

## 🧪 Comprehensive Testing Plan

### Unit Tests

#### Database Models Tests
```python
# tests/unit/models/test_audit_log.py
import pytest
from backend.app.models.audit_log import AuditLog

class TestAuditLogModel:
    def test_audit_log_creation(self, db_session):
        """Test audit log model creation."""
        audit_log = AuditLog(
            user_id="123e4567-e89b-12d3-a456-426614174000",
            user_email="test@example.com",
            action_type="toggle_enable",
            entity_type="feature_flag",
            entity_id="456e7890-e89b-12d3-a456-426614174001",
            entity_name="test_flag",
            old_value="disabled",
            new_value="enabled"
        )

        db_session.add(audit_log)
        db_session.commit()

        assert audit_log.id is not None
        assert audit_log.timestamp is not None
        assert audit_log.user_email == "test@example.com"

    def test_audit_log_relationships(self, db_session, test_user):
        """Test audit log relationships."""
        # Test implementation
        pass
```

#### Service Layer Tests
```python
# tests/unit/services/test_audit_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.services.audit_service import AuditService

class TestAuditService:
    @pytest.mark.asyncio
    async def test_log_toggle_operation(self, db_session):
        """Test audit logging functionality."""
        audit_id = await AuditService.log_toggle_operation(
            db=db_session,
            user_id="123e4567-e89b-12d3-a456-426614174000",
            user_email="test@example.com",
            action_type="toggle_enable",
            entity_id="456e7890-e89b-12d3-a456-426614174001",
            entity_name="test_flag",
            old_value="disabled",
            new_value="enabled",
            reason="Testing toggle"
        )

        assert audit_id is not None

        # Verify log was created
        logs, total = AuditService.get_audit_logs(db_session)
        assert total == 1
        assert logs[0].action_type == "toggle_enable"

    def test_get_audit_logs_pagination(self, db_session, sample_audit_logs):
        """Test audit log pagination."""
        logs, total = AuditService.get_audit_logs(
            db=db_session,
            page=1,
            limit=10
        )

        assert len(logs) <= 10
        assert total >= len(logs)

    def test_get_audit_logs_filtering(self, db_session, sample_audit_logs):
        """Test audit log filtering."""
        # Test user filtering
        user_id = sample_audit_logs[0].user_id
        logs, total = AuditService.get_audit_logs(
            db=db_session,
            user_id=user_id
        )

        assert all(log.user_id == user_id for log in logs)
```

```python
# tests/unit/services/test_toggle_service.py
import pytest
from unittest.mock import AsyncMock, patch
from backend.app.services.toggle_service import ToggleService
from backend.app.models.feature_flag import FeatureFlagStatus

class TestToggleService:
    @pytest.mark.asyncio
    @patch('backend.app.services.audit_service.AuditService.log_toggle_operation')
    async def test_toggle_feature_flag_enable(self, mock_audit, db_session, test_feature_flag):
        """Test toggling feature flag from disabled to enabled."""
        # Set initial state
        test_feature_flag.status = FeatureFlagStatus.DISABLED
        db_session.commit()

        result = await ToggleService.toggle_feature_flag(
            db=db_session,
            feature_flag_id=test_feature_flag.id,
            user_id="123e4567-e89b-12d3-a456-426614174000",
            user_email="test@example.com",
            reason="Test toggle"
        )

        assert result.status == FeatureFlagStatus.ENABLED
        mock_audit.assert_called_once()

    @pytest.mark.asyncio
    async def test_toggle_nonexistent_feature_flag(self, db_session):
        """Test toggling non-existent feature flag."""
        with pytest.raises(ValueError, match="Feature flag not found"):
            await ToggleService.toggle_feature_flag(
                db=db_session,
                feature_flag_id="nonexistent-id",
                user_id="123e4567-e89b-12d3-a456-426614174000",
                user_email="test@example.com"
            )
```

#### API Endpoint Tests
```python
# tests/unit/api/test_toggle_endpoints.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

class TestToggleEndpoints:
    def test_toggle_feature_flag_success(self, client: TestClient, auth_headers, test_feature_flag):
        """Test successful feature flag toggle."""
        with patch('backend.app.services.toggle_service.ToggleService.toggle_feature_flag') as mock_toggle:
            mock_toggle.return_value = test_feature_flag

            response = client.post(
                f"/api/v1/feature-flags/{test_feature_flag.id}/toggle",
                json={"reason": "Testing"},
                headers=auth_headers
            )

            assert response.status_code == 200
            assert response.json()["id"] == str(test_feature_flag.id)

    def test_toggle_feature_flag_permission_denied(self, client: TestClient, auth_headers_no_permissions):
        """Test toggle with insufficient permissions."""
        response = client.post(
            "/api/v1/feature-flags/123e4567-e89b-12d3-a456-426614174000/toggle",
            json={"reason": "Testing"},
            headers=auth_headers_no_permissions
        )

        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    def test_toggle_feature_flag_not_found(self, client: TestClient, auth_headers):
        """Test toggle non-existent feature flag."""
        with patch('backend.app.services.toggle_service.ToggleService.toggle_feature_flag') as mock_toggle:
            mock_toggle.side_effect = ValueError("Feature flag not found")

            response = client.post(
                "/api/v1/feature-flags/nonexistent-id/toggle",
                json={"reason": "Testing"},
                headers=auth_headers
            )

            assert response.status_code == 404
```

### Integration Tests

```python
# tests/integration/test_toggle_workflow.py
import pytest
from fastapi.testclient import TestClient

class TestToggleWorkflow:
    def test_complete_toggle_workflow(self, client: TestClient, db_session, test_user, test_feature_flag):
        """Test complete toggle workflow with audit logging."""
        # Login and get auth headers
        auth_headers = self.get_auth_headers(client, test_user)

        # Toggle feature flag
        response = client.post(
            f"/api/v1/feature-flags/{test_feature_flag.id}/toggle",
            json={"reason": "Integration test"},
            headers=auth_headers
        )

        assert response.status_code == 200
        feature_flag_data = response.json()

        # Verify audit log was created
        audit_response = client.get(
            f"/api/v1/audit-logs?entity_id={test_feature_flag.id}",
            headers=auth_headers
        )

        assert audit_response.status_code == 200
        audit_data = audit_response.json()
        assert audit_data["total"] >= 1
        assert audit_data["items"][0]["entity_id"] == str(test_feature_flag.id)
        assert audit_data["items"][0]["reason"] == "Integration test"
```

### Performance Tests

```python
# tests/performance/test_toggle_performance.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestTogglePerformance:
    def test_toggle_response_time(self, client: TestClient, auth_headers, test_feature_flag):
        """Test toggle API response time requirement (<3 seconds)."""
        start_time = time.time()

        response = client.post(
            f"/api/v1/feature-flags/{test_feature_flag.id}/toggle",
            json={"reason": "Performance test"},
            headers=auth_headers
        )

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 3.0  # Must complete within 3 seconds

    def test_concurrent_toggles(self, client: TestClient, auth_headers, test_feature_flags):
        """Test concurrent toggle operations."""
        def toggle_flag(flag_id):
            return client.post(
                f"/api/v1/feature-flags/{flag_id}/toggle",
                json={"reason": "Concurrent test"},
                headers=auth_headers
            )

        # Test 10 concurrent toggle operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(toggle_flag, flag.id) for flag in test_feature_flags[:10]]
            results = [future.result() for future in futures]

        # All should succeed
        assert all(result.status_code == 200 for result in results)

    def test_audit_log_query_performance(self, client: TestClient, auth_headers, large_audit_dataset):
        """Test audit log query performance with large dataset."""
        start_time = time.time()

        response = client.get(
            "/api/v1/audit-logs?limit=50",
            headers=auth_headers
        )

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 2.0  # Must complete within 2 seconds
```

### Security Tests

```python
# tests/security/test_toggle_security.py
import pytest

class TestToggleSecurity:
    def test_unauthenticated_access_denied(self, client: TestClient):
        """Test unauthenticated access is denied."""
        response = client.post("/api/v1/feature-flags/123/toggle")
        assert response.status_code == 401

    def test_insufficient_permissions_denied(self, client: TestClient, auth_headers_read_only):
        """Test insufficient permissions are denied."""
        response = client.post(
            "/api/v1/feature-flags/123/toggle",
            headers=auth_headers_read_only
        )
        assert response.status_code == 403

    def test_sql_injection_protection(self, client: TestClient, auth_headers):
        """Test SQL injection protection."""
        malicious_id = "'; DROP TABLE audit_logs; --"
        response = client.post(
            f"/api/v1/feature-flags/{malicious_id}/toggle",
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
```

---

## 📊 Test Coverage Requirements

### Coverage Targets
- **Unit Tests**: ≥90% line coverage
- **Integration Tests**: All API endpoints covered
- **Performance Tests**: All critical paths tested
- **Security Tests**: All authentication/authorization paths

### Test Data Setup
```python
# tests/conftest.py
@pytest.fixture
def test_feature_flag(db_session):
    """Create test feature flag."""
    feature_flag = FeatureFlag(
        name="test_flag",
        key="test_flag",
        description="Test feature flag",
        status=FeatureFlagStatus.DISABLED
    )
    db_session.add(feature_flag)
    db_session.commit()
    return feature_flag

@pytest.fixture
def sample_audit_logs(db_session, test_user, test_feature_flag):
    """Create sample audit logs."""
    logs = []
    for i in range(20):
        log = AuditLog(
            user_id=test_user.id,
            user_email=test_user.email,
            action_type="toggle_enable" if i % 2 == 0 else "toggle_disable",
            entity_type="feature_flag",
            entity_id=test_feature_flag.id,
            entity_name=test_feature_flag.name,
            old_value="disabled" if i % 2 == 0 else "enabled",
            new_value="enabled" if i % 2 == 0 else "disabled"
        )
        logs.append(log)
        db_session.add(log)

    db_session.commit()
    return logs
```

---

## 🎯 Success Criteria

### Functional Requirements
- [ ] All 5 acceptance criteria pass automated tests
- [ ] API response times consistently <3 seconds
- [ ] 100% audit log coverage for toggle operations
- [ ] Permission system blocks unauthorized access
- [ ] Error handling provides clear, actionable feedback

### Quality Requirements
- [ ] ≥90% unit test coverage
- [ ] All integration tests pass
- [ ] Performance tests meet SLA requirements
- [ ] Security tests pass vulnerability scans
- [ ] Code review approval from senior developer

### Deployment Requirements
- [ ] Database migrations tested on staging
- [ ] API documentation updated
- [ ] Monitoring and logging configured
- [ ] Performance benchmarks established
- [ ] Error tracking configured

This execution and testing plan ensures comprehensive coverage of all functional requirements while maintaining high quality and performance standards.
