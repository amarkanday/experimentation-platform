# Backend Toggle API - Execution & Testing Plan

## 📋 Implementation Execution Plan

### Phase 1: Database Foundation (Days 1-2)

#### 1.1 Database Schema
```sql
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
```

**Tasks:**
- [ ] Create Alembic migration script
- [ ] Test migration locally and on staging
- [ ] Verify index performance
- [ ] Create rollback migration

#### 1.2 Database Models
```python
# backend/app/models/audit_log.py
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
```

**Tasks:**
- [ ] Create AuditLog model
- [ ] Update model imports
- [ ] Add User relationship
- [ ] Test model creation

### Phase 2: Core Services (Days 3-4)

#### 2.1 Audit Service
```python
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
        # Async audit logging implementation
        pass

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
        # Paginated audit log retrieval with filtering
        pass
```

**Tasks:**
- [ ] Implement AuditService class
- [ ] Add async logging functionality
- [ ] Implement filtering and pagination
- [ ] Add error handling

#### 2.2 Toggle Service
```python
class ToggleService:
    @staticmethod
    async def toggle_feature_flag(
        db: Session,
        feature_flag_id: UUID,
        user_id: UUID,
        user_email: str,
        reason: Optional[str] = None
    ) -> FeatureFlag:
        # Toggle implementation with transaction management
        pass
```

**Tasks:**
- [ ] Implement ToggleService class
- [ ] Add transaction management
- [ ] Integrate with AuditService
- [ ] Add comprehensive error handling

### Phase 3: API Endpoints (Days 5-6)

#### 3.1 Toggle Endpoints
```python
@router.post("/feature-flags/{feature_flag_id}/toggle")
async def toggle_feature_flag(
    feature_flag_id: UUID,
    request: ToggleRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    # Permission validation and toggle implementation
    pass
```

#### 3.2 Audit Endpoints
```python
@router.get("/audit-logs")
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
    # Audit log retrieval with filtering
    pass
```

**Tasks:**
- [ ] Implement all toggle endpoints (/toggle, /enable, /disable)
- [ ] Implement audit log endpoints
- [ ] Add permission validation
- [ ] Create request/response schemas
- [ ] Add comprehensive error handling

---

## 🧪 Comprehensive Testing Plan

### Unit Tests

#### AC1: Feature Flag Toggle API Testing
```python
class TestToggleAPI:
    @pytest.mark.asyncio
    async def test_toggle_feature_flag_success(self, db_session, test_feature_flag, test_user):
        """Test successful toggle operation."""
        result = await ToggleService.toggle_feature_flag(
            db=db_session,
            feature_flag_id=test_feature_flag.id,
            user_id=test_user.id,
            user_email=test_user.email,
            reason="Test toggle"
        )

        assert result.status != test_feature_flag.status
        assert result.updated_at > test_feature_flag.updated_at

    def test_toggle_api_response_time(self, client, auth_headers, test_feature_flag):
        """Test API response time requirement (<3 seconds)."""
        import time
        start_time = time.time()

        response = client.post(
            f"/api/v1/feature-flags/{test_feature_flag.id}/toggle",
            json={"reason": "Performance test"},
            headers=auth_headers
        )

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 3.0
        assert "id" in response.json()
        assert "status" in response.json()
        assert "updated_at" in response.json()
```

#### AC2: Audit Logging Infrastructure Testing
```python
class TestAuditLogging:
    @pytest.mark.asyncio
    async def test_audit_log_creation(self, db_session):
        """Test audit log entry creation."""
        audit_id = await AuditService.log_toggle_operation(
            db=db_session,
            user_id="123e4567-e89b-12d3-a456-426614174000",
            user_email="test@example.com",
            action_type="toggle_enable",
            entity_id="456e7890-e89b-12d3-a456-426614174001",
            entity_name="test_flag",
            old_value="disabled",
            new_value="enabled",
            reason="Test audit log"
        )

        assert audit_id is not None

        # Verify log contents
        audit_log = db_session.query(AuditLog).filter(AuditLog.id == audit_id).first()
        assert audit_log.user_email == "test@example.com"
        assert audit_log.action_type == "toggle_enable"
        assert audit_log.entity_name == "test_flag"
        assert audit_log.old_value == "disabled"
        assert audit_log.new_value == "enabled"
        assert audit_log.reason == "Test audit log"
        assert audit_log.timestamp is not None

    def test_audit_log_on_failure(self, db_session):
        """Test audit logging occurs even on operation failure."""
        # Test implementation for failure scenarios
        pass
```

#### AC3: Audit Log Query API Testing
```python
class TestAuditLogQuery:
    def test_get_audit_logs_pagination(self, client, auth_headers, sample_audit_logs):
        """Test paginated audit log retrieval."""
        response = client.get(
            "/api/v1/audit-logs?page=1&limit=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert len(data["items"]) <= 10
        assert data["page"] == 1
        assert data["limit"] == 10

    def test_audit_log_filtering(self, client, auth_headers, sample_audit_logs):
        """Test audit log filtering capabilities."""
        test_user_id = sample_audit_logs[0].user_id

        response = client.get(
            f"/api/v1/audit-logs?user_id={test_user_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert all(item["user_id"] == str(test_user_id) for item in data["items"])

    def test_audit_log_ordering(self, client, auth_headers, sample_audit_logs):
        """Test audit logs are ordered by timestamp (newest first)."""
        response = client.get("/api/v1/audit-logs", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        timestamps = [item["timestamp"] for item in data["items"]]

        # Verify descending order
        assert timestamps == sorted(timestamps, reverse=True)
```

#### AC4: Permission Validation Testing
```python
class TestPermissionValidation:
    def test_toggle_without_permissions(self, client, auth_headers_no_toggle_permission):
        """Test toggle operation without proper permissions."""
        response = client.post(
            "/api/v1/feature-flags/123e4567-e89b-12d3-a456-426614174000/toggle",
            json={"reason": "Unauthorized test"},
            headers=auth_headers_no_toggle_permission
        )

        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    def test_permission_denial_logged(self, db_session, client, auth_headers_no_permission):
        """Test that permission denials are logged."""
        initial_count = db_session.query(AuditLog).count()

        response = client.post(
            "/api/v1/feature-flags/123e4567-e89b-12d3-a456-426614174000/toggle",
            headers=auth_headers_no_permission
        )

        assert response.status_code == 403

        # Verify permission denial was logged
        final_count = db_session.query(AuditLog).count()
        assert final_count > initial_count

    def test_audit_view_permissions(self, client, auth_headers_no_audit_permission):
        """Test audit log viewing without proper permissions."""
        response = client.get("/api/v1/audit-logs", headers=auth_headers_no_audit_permission)

        assert response.status_code == 403
```

#### AC5: Error Handling Testing
```python
class TestErrorHandling:
    def test_toggle_nonexistent_flag(self, client, auth_headers):
        """Test toggling non-existent feature flag."""
        response = client.post(
            "/api/v1/feature-flags/nonexistent-id/toggle",
            json={"reason": "Testing error"},
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_invalid_uuid_format(self, client, auth_headers):
        """Test invalid UUID format handling."""
        response = client.post(
            "/api/v1/feature-flags/invalid-uuid/toggle",
            json={"reason": "Testing validation"},
            headers=auth_headers
        )

        assert response.status_code == 422
        assert "validation error" in response.json()["detail"][0]["type"]

    def test_malformed_request_body(self, client, auth_headers, test_feature_flag):
        """Test malformed request body handling."""
        response = client.post(
            f"/api/v1/feature-flags/{test_feature_flag.id}/toggle",
            json={"invalid_field": "value"},
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_no_partial_changes_on_error(self, db_session, test_feature_flag):
        """Test no partial database changes occur on errors."""
        original_status = test_feature_flag.status
        original_updated_at = test_feature_flag.updated_at

        # Simulate error during toggle operation
        with pytest.raises(Exception):
            # Force an error condition
            pass

        # Verify no changes were made
        db_session.refresh(test_feature_flag)
        assert test_feature_flag.status == original_status
        assert test_feature_flag.updated_at == original_updated_at
```

### Integration Tests

```python
class TestToggleWorkflowIntegration:
    def test_complete_toggle_workflow(self, client, db_session, test_user, test_feature_flag):
        """Test complete toggle workflow with audit logging."""
        auth_headers = self.get_auth_headers(client, test_user)

        # Get initial state
        initial_status = test_feature_flag.status

        # Perform toggle
        response = client.post(
            f"/api/v1/feature-flags/{test_feature_flag.id}/toggle",
            json={"reason": "Integration test"},
            headers=auth_headers
        )

        assert response.status_code == 200
        feature_flag_data = response.json()
        assert feature_flag_data["status"] != initial_status.value

        # Verify audit log was created
        audit_response = client.get(
            f"/api/v1/audit-logs?entity_id={test_feature_flag.id}",
            headers=auth_headers
        )

        assert audit_response.status_code == 200
        audit_data = audit_response.json()
        assert audit_data["total"] >= 1

        latest_audit = audit_data["items"][0]
        assert latest_audit["entity_id"] == str(test_feature_flag.id)
        assert latest_audit["reason"] == "Integration test"
        assert latest_audit["old_value"] == initial_status.value
        assert latest_audit["new_value"] == feature_flag_data["status"]
```

### Performance Tests

```python
class TestPerformance:
    def test_concurrent_toggle_operations(self, client, auth_headers, test_feature_flags):
        """Test concurrent toggle operations."""
        from concurrent.futures import ThreadPoolExecutor
        import time

        def toggle_flag(flag_id):
            return client.post(
                f"/api/v1/feature-flags/{flag_id}/toggle",
                json={"reason": "Concurrent test"},
                headers=auth_headers
            )

        start_time = time.time()

        # Test 10 concurrent operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(toggle_flag, flag.id) for flag in test_feature_flags[:10]]
            results = [future.result() for future in futures]

        end_time = time.time()
        total_time = end_time - start_time

        # All operations should succeed
        assert all(result.status_code == 200 for result in results)
        # Should handle 10 concurrent requests efficiently
        assert total_time < 10.0

    def test_audit_log_query_performance(self, client, auth_headers, large_audit_dataset):
        """Test audit log query performance with large dataset (1000+ records)."""
        import time

        start_time = time.time()
        response = client.get("/api/v1/audit-logs?limit=50", headers=auth_headers)
        end_time = time.time()

        query_time = end_time - start_time

        assert response.status_code == 200
        assert query_time < 2.0  # Must complete within 2 seconds
```

### Security Tests

```python
class TestSecurity:
    def test_unauthenticated_access(self, client):
        """Test all endpoints reject unauthenticated requests."""
        endpoints = [
            ("POST", "/api/v1/feature-flags/123/toggle"),
            ("POST", "/api/v1/feature-flags/123/enable"),
            ("POST", "/api/v1/feature-flags/123/disable"),
            ("GET", "/api/v1/audit-logs")
        ]

        for method, endpoint in endpoints:
            response = client.request(method, endpoint)
            assert response.status_code == 401

    def test_sql_injection_protection(self, client, auth_headers):
        """Test SQL injection protection."""
        malicious_inputs = [
            "'; DROP TABLE audit_logs; --",
            "1' OR '1'='1",
            "1; DELETE FROM users; --"
        ]

        for malicious_input in malicious_inputs:
            response = client.post(
                f"/api/v1/feature-flags/{malicious_input}/toggle",
                headers=auth_headers
            )
            # Should return validation error, not execute SQL
            assert response.status_code in [422, 404]
```

---

## 📊 Test Coverage & Success Metrics

### Coverage Requirements
- **Unit Tests**: ≥90% line coverage
- **Integration Tests**: 100% API endpoint coverage
- **Performance Tests**: All critical paths
- **Security Tests**: All auth/authz scenarios

### Acceptance Criteria Validation

| Acceptance Criteria | Test Methods | Success Criteria |
|-------------------|-------------|-----------------|
| AC1: Toggle API | `test_toggle_feature_flag_success`, `test_toggle_api_response_time` | ✅ Status changes, ✅ <3s response, ✅ Proper response format |
| AC2: Audit Logging | `test_audit_log_creation`, `test_audit_log_on_failure` | ✅ Complete audit data, ✅ Success & failure logging |
| AC3: Audit Query | `test_get_audit_logs_pagination`, `test_audit_log_filtering` | ✅ Pagination, ✅ Filtering, ✅ Timestamp ordering |
| AC4: Permissions | `test_toggle_without_permissions`, `test_permission_denial_logged` | ✅ 403 response, ✅ No changes, ✅ Denial logged |
| AC5: Error Handling | `test_toggle_nonexistent_flag`, `test_no_partial_changes_on_error` | ✅ Proper HTTP codes, ✅ Error details, ✅ No partial changes |

### Performance Targets
- Toggle API response: <3 seconds (target: <1 second)
- Concurrent requests: Handle 10 simultaneous operations
- Audit queries: <2 seconds for 1000+ records
- Database operations: <500ms per operation

### Quality Gates
- [ ] All acceptance criteria tests pass
- [ ] Performance benchmarks meet requirements
- [ ] Security tests show no vulnerabilities
- [ ] Code coverage ≥90%
- [ ] Integration tests cover all workflows
- [ ] Error handling covers all failure scenarios

This comprehensive testing plan ensures that all acceptance criteria are thoroughly validated while maintaining high standards for performance, security, and reliability.
