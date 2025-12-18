# EP-010: Implement Lambda Functions for Real-time Services

**Status:** 🔴 Not Started
**Priority:** 🔥 High
**Story Points:** 13
**Sprint:** Phase 3 - Real-time Services
**Assignee:** Backend Team
**Created:** 2025-12-16
**Type:** Feature

---

## 📋 Overview

### User Story
**As a** platform operator
**I want** real-time Lambda-based services for experiment assignments and event processing
**So that** we can handle high-volume, low-latency operations with automatic scaling and minimal infrastructure management

### Business Value
- **Performance:** Sub-50ms experiment assignment latency
- **Scalability:** Automatic scaling for 100K+ requests/second
- **Cost:** Pay-per-use model reduces infrastructure costs by ~60%
- **Reliability:** Built-in fault tolerance and retry mechanisms

---

## 🎯 Problem Statement

Currently, the platform has infrastructure defined for Lambda functions in CDK but lacks the actual Lambda function implementations. This creates a gap in the real-time services layer, preventing:

1. Fast, consistent experiment variant assignments
2. Real-time event collection and processing
3. High-throughput feature flag evaluations
4. Scalable assignment persistence to DynamoDB

### Current State
- ✅ AWS CDK infrastructure defined (`infrastructure/cdk/stacks/analytics_stack.py`, `compute_stack.py`)
- ✅ Kinesis streams configured
- ✅ DynamoDB tables defined
- ✅ Lambda IAM roles created
- ❌ Lambda function code not implemented
- ❌ Assignment service Lambda missing
- ❌ Event processor Lambda missing
- ❌ Real-time evaluation Lambda missing

---

## 🔧 Technical Specifications

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Application                       │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├─── GET /assign ──────────────┐
               │                              │
               └─── POST /events ─────────────┤
                                              │
               ┌──────────────────────────────▼─────────────┐
               │           API Gateway / ALB                 │
               └──────────────┬────────────────┬─────────────┘
                              │                │
            ┌─────────────────▼───┐   ┌────────▼─────────────┐
            │  Assignment Lambda  │   │ Event Processor      │
            │  (Python 3.11)      │   │ Lambda (Python 3.11) │
            └─────────┬───────────┘   └──────────┬───────────┘
                      │                          │
                      ├──────── Read ────────────┤
                      │                          │
              ┌───────▼──────────┐      ┌────────▼──────────┐
              │   DynamoDB       │      │  Kinesis Stream   │
              │   Assignments    │      │  (Events)         │
              └──────────────────┘      └───────────────────┘
                      │                          │
                      │                          │
              ┌───────▼──────────┐      ┌────────▼──────────┐
              │   PostgreSQL     │      │  S3 Data Lake     │
              │   (Sync)         │      │  (Archive)        │
              └──────────────────┘      └───────────────────┘
```

### Lambda Functions to Implement

#### 1. **Assignment Lambda** (`backend/lambda/assignment/handler.py`)

**Purpose:** Handle experiment variant assignments using consistent hashing

**Inputs:**
```python
{
    "user_id": str,
    "experiment_key": str,
    "context": dict,  # User attributes for targeting
}
```

**Outputs:**
```python
{
    "variant": str,
    "experiment_id": str,
    "assignment_id": str,
    "timestamp": str,
}
```

**Logic:**
1. Validate experiment is ACTIVE
2. Evaluate targeting rules (if any)
3. Calculate variant using consistent hashing
4. Store assignment in DynamoDB
5. Async sync to PostgreSQL (if needed)
6. Return variant assignment

**Performance Requirements:**
- P50 latency: < 20ms
- P99 latency: < 50ms
- Throughput: 10K requests/second per Lambda

#### 2. **Event Processor Lambda** (`backend/lambda/events/handler.py`)

**Purpose:** Process incoming events from Kinesis stream

**Trigger:** Kinesis stream events (batch processing)

**Inputs:**
```python
{
    "Records": [
        {
            "kinesis": {
                "data": base64_encoded_event
            }
        }
    ]
}
```

**Logic:**
1. Decode and validate events
2. Enrich with assignment data
3. Aggregate metrics (if applicable)
4. Store in DynamoDB counters
5. Archive to S3 (via Firehose)
6. Handle errors and retries

**Performance Requirements:**
- Batch size: 100-500 events
- Processing latency: < 100ms per batch
- Error rate: < 0.1%

#### 3. **Feature Flag Evaluation Lambda** (`backend/lambda/feature_flags/handler.py`)

**Purpose:** Real-time feature flag evaluation with targeting

**Inputs:**
```python
{
    "flag_key": str,
    "user_id": str,
    "context": dict,
}
```

**Outputs:**
```python
{
    "enabled": bool,
    "variant": str | None,
    "reason": str,
}
```

**Logic:**
1. Fetch flag configuration (with caching)
2. Evaluate targeting rules
3. Apply rollout percentage
4. Return evaluation result
5. Record evaluation event (async)

**Performance Requirements:**
- P50 latency: < 15ms
- P99 latency: < 40ms
- Cache hit rate: > 95%

---

## 📝 Implementation Tasks

### Phase 1: Setup & Infrastructure (3 days)

- [ ] **Task 1.1:** Create Lambda function directory structure
  ```bash
  backend/lambda/
  ├── assignment/
  │   ├── handler.py
  │   ├── requirements.txt
  │   └── tests/
  ├── events/
  │   ├── handler.py
  │   ├── requirements.txt
  │   └── tests/
  ├── feature_flags/
  │   ├── handler.py
  │   ├── requirements.txt
  │   └── tests/
  └── shared/
      ├── utils.py
      ├── consistent_hash.py
      └── models.py
  ```

- [ ] **Task 1.2:** Set up Lambda deployment configuration
  - Configure deployment scripts
  - Set up environment variables
  - Configure IAM permissions

- [ ] **Task 1.3:** Create shared utilities module
  - Consistent hashing algorithm
  - DynamoDB helpers
  - Kinesis helpers
  - Logging utilities

### Phase 2: Assignment Lambda (4 days)

- [ ] **Task 2.1:** Implement consistent hashing algorithm
  - Use MurmurHash3 for deterministic assignments
  - Support traffic allocation
  - Handle experiment variants

- [ ] **Task 2.2:** Implement targeting rules evaluation
  - Reuse backend rules engine logic
  - Add caching layer
  - Handle complex rule conditions

- [ ] **Task 2.3:** Implement DynamoDB assignment storage
  - Schema: `user_id`, `experiment_id`, `variant`, `timestamp`
  - Add TTL for automatic cleanup
  - Implement conditional writes

- [ ] **Task 2.4:** Add error handling and retries
  - Graceful degradation
  - Circuit breaker pattern
  - Dead letter queue (DLQ)

- [ ] **Task 2.5:** Implement caching layer
  - Use Lambda environment for warm start caching
  - Cache experiment configurations
  - Cache targeting rules
  - TTL: 5 minutes

### Phase 3: Event Processor Lambda (3 days)

- [ ] **Task 3.1:** Implement Kinesis event parsing
  - Decode base64 events
  - Validate event schema
  - Handle malformed events

- [ ] **Task 3.2:** Implement event enrichment
  - Fetch assignment data
  - Add experiment metadata
  - Calculate metrics

- [ ] **Task 3.3:** Implement DynamoDB aggregation
  - Real-time counters
  - Atomic increments
  - Time-windowed aggregation

- [ ] **Task 3.4:** Implement S3 archival
  - Batch events for S3
  - Compress data (gzip)
  - Organize by date partition

- [ ] **Task 3.5:** Add batch processing logic
  - Handle partial batch failures
  - Implement checkpointing
  - Add retry logic

### Phase 4: Feature Flag Lambda (2 days)

- [ ] **Task 4.1:** Implement flag evaluation logic
  - Fetch flag configuration
  - Evaluate targeting rules
  - Apply rollout percentage

- [ ] **Task 4.2:** Implement caching
  - Cache flag configurations
  - Invalidation strategy
  - Handle cache misses

- [ ] **Task 4.3:** Add evaluation tracking
  - Record evaluation events
  - Async write to Kinesis
  - Minimal performance impact

### Phase 5: Testing & Optimization (3 days)

- [ ] **Task 5.1:** Write unit tests
  - Test each Lambda function independently
  - Mock AWS services
  - Test edge cases

- [ ] **Task 5.2:** Write integration tests
  - Test with actual DynamoDB local
  - Test with Kinesis local
  - End-to-end test scenarios

- [ ] **Task 5.3:** Performance testing
  - Load test with 10K RPS
  - Measure cold start times
  - Optimize warm start performance
  - Analyze CloudWatch metrics

- [ ] **Task 5.4:** Add monitoring and alerts
  - CloudWatch metrics
  - Custom metrics for business logic
  - Error rate alerts
  - Latency alerts

### Phase 6: Deployment & Documentation (2 days)

- [ ] **Task 6.1:** Update CDK stacks
  - Add Lambda function definitions
  - Configure event sources
  - Set environment variables
  - Configure VPC settings (if needed)

- [ ] **Task 6.2:** Create deployment pipeline
  - CI/CD integration
  - Automated testing
  - Blue/green deployment
  - Rollback strategy

- [ ] **Task 6.3:** Write documentation
  - Lambda function documentation
  - API documentation
  - Operations runbook
  - Troubleshooting guide

---

## ✅ Acceptance Criteria

### Functional Requirements

1. **Assignment Lambda**
   - [ ] Returns consistent variant assignments for same user+experiment
   - [ ] Respects traffic allocation percentages (±2% accuracy)
   - [ ] Evaluates targeting rules correctly (100% match with backend logic)
   - [ ] Stores assignments in DynamoDB with <50ms P99 latency
   - [ ] Handles errors gracefully with proper status codes

2. **Event Processor Lambda**
   - [ ] Processes Kinesis batches of 100-500 events
   - [ ] Validates and filters invalid events
   - [ ] Aggregates metrics in real-time
   - [ ] Archives events to S3 with proper partitioning
   - [ ] Handles partial batch failures without data loss

3. **Feature Flag Lambda**
   - [ ] Evaluates flags with <40ms P99 latency
   - [ ] Caches flag configurations effectively (>95% hit rate)
   - [ ] Respects rollout percentages accurately
   - [ ] Evaluates targeting rules correctly
   - [ ] Records evaluation events asynchronously

### Performance Requirements

1. **Latency**
   - [ ] Assignment Lambda: P99 < 50ms
   - [ ] Event Processor: P99 < 100ms per batch
   - [ ] Feature Flag Lambda: P99 < 40ms

2. **Throughput**
   - [ ] Assignment Lambda: 10K RPS per function
   - [ ] Event Processor: 1M events/hour
   - [ ] Feature Flag Lambda: 20K RPS per function

3. **Reliability**
   - [ ] 99.9% success rate
   - [ ] < 0.1% error rate
   - [ ] Automatic retry on failures
   - [ ] DLQ for failed messages

### Operational Requirements

1. **Monitoring**
   - [ ] CloudWatch dashboards created
   - [ ] Metrics for invocations, errors, duration
   - [ ] Custom business metrics
   - [ ] Alerts configured for errors and latency

2. **Cost**
   - [ ] Lambda cost < $500/month for 100M requests
   - [ ] Efficient memory allocation (512MB-1GB)
   - [ ] Cold start optimization

3. **Security**
   - [ ] IAM least privilege permissions
   - [ ] Encryption at rest (DynamoDB, S3)
   - [ ] Encryption in transit (TLS)
   - [ ] No hardcoded credentials

---

## ✔️ Definition of Done

### Code Quality
- [ ] All Lambda functions implemented and working
- [ ] Code follows Python PEP 8 style guidelines
- [ ] Type hints added for all functions
- [ ] Docstrings for all public functions
- [ ] No hardcoded values (use environment variables)

### Testing
- [ ] Unit tests written with >85% coverage
- [ ] Integration tests pass
- [ ] Load tests completed successfully
- [ ] Edge cases tested and handled

### Documentation
- [ ] Code documented with inline comments
- [ ] README created for each Lambda function
- [ ] API documentation updated
- [ ] Architecture diagrams updated
- [ ] Operations runbook created

### Deployment
- [ ] CDK stacks updated and tested
- [ ] CI/CD pipeline configured
- [ ] Deployed to staging environment
- [ ] Smoke tests pass in staging
- [ ] Production deployment plan created

### Monitoring
- [ ] CloudWatch dashboards created
- [ ] Metrics and logs configured
- [ ] Alerts set up and tested
- [ ] On-call runbook updated

### Review & Approval
- [ ] Code review completed by senior engineer
- [ ] Security review completed
- [ ] Performance benchmarks met
- [ ] Product owner approval
- [ ] Ready for production deployment

---

## 📊 Dependencies

### Blocked By
- None (infrastructure already exists)

### Blocking
- EP-011: Integration Testing (needs Lambda functions to test)
- EP-012: Performance & Load Testing (needs real-time services)

### Related Tickets
- EP-001: Advanced Rules Engine (shares targeting logic)
- EP-013: Monitoring & Logging (needs metrics from Lambdas)

---

## 🚨 Risks & Mitigation

### Risk 1: Cold Start Latency
**Impact:** High
**Probability:** Medium
**Mitigation:**
- Use provisioned concurrency for critical functions
- Optimize package size (<50MB)
- Use Lambda SnapStart (Python 3.11)
- Implement warming strategy

### Risk 2: DynamoDB Throttling
**Impact:** High
**Probability:** Low
**Mitigation:**
- Use on-demand capacity mode
- Implement exponential backoff
- Add circuit breaker
- Monitor write capacity units

### Risk 3: Inconsistent Assignment Logic
**Impact:** Critical
**Probability:** Low
**Mitigation:**
- Share code with backend services
- Comprehensive integration tests
- Canary deployments
- A/B test Lambda vs backend

### Risk 4: Cost Overruns
**Impact:** Medium
**Probability:** Low
**Mitigation:**
- Set AWS budgets and alerts
- Monitor Lambda invocation counts
- Optimize memory and duration
- Use reserved capacity if needed

---

## 📈 Success Metrics

### Technical Metrics
- Assignment latency P99 < 50ms
- Event processing throughput > 1M events/hour
- Error rate < 0.1%
- Cache hit rate > 95%

### Business Metrics
- 60% reduction in infrastructure costs
- 10x improvement in scalability
- 50% reduction in assignment latency
- 99.9% uptime

---

## 📚 Reference Materials

### Documentation
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Kinesis Stream Processing](https://docs.aws.amazon.com/streams/latest/dev/building-consumers.html)

### Internal Resources
- `backend/app/core/rules_engine.py` - Rules evaluation logic
- `backend/app/services/assignment_service.py` - Assignment logic
- `infrastructure/cdk/stacks/analytics_stack.py` - Kinesis setup
- `infrastructure/cdk/stacks/compute_stack.py` - Lambda roles

### Similar Implementations
- Statsig: Consistent hashing implementation
- LaunchDarkly: Feature flag evaluation
- Optimizely: Real-time event processing

---

## 🔄 Change Log

| Date       | Author | Change Description |
|------------|--------|-------------------|
| 2025-12-16 | Claude | Initial ticket creation |

---

**Estimated Completion:** 17 working days (3.5 weeks)
**Target Sprint:** Q1 2026, Sprint 3-4
