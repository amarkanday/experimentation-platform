# EP-013: Monitoring & Logging Implementation

**Status:** 🟡 In Progress
**Priority:** 🔥 High
**Story Points:** 10
**Sprint:** Week 5-6
**Assignee:** DevOps + Backend Team
**Created:** 2025-12-16
**Type:** Infrastructure

---

## 📋 Overview

### User Story
**As a** platform operator
**I want** comprehensive monitoring and structured logging
**So that** I can quickly identify, diagnose, and resolve production issues

### Business Value
- **MTTR:** Reduce mean time to resolution by 70%
- **Uptime:** Improve availability to 99.9%
- **Proactive:** Catch issues before users notice
- **Compliance:** Audit trail for regulatory requirements

---

## 🎯 Problem Statement

From existing tickets (`project/tickets.md`), the following monitoring/logging work is needed:

✅ **Partially Complete:**
- Basic CloudWatch infrastructure exists (`infrastructure/cloudwatch/`)
- Some logging in place

❌ **Missing:**
1. Structured logging throughout application
2. CloudWatch Logs integration and shipping
3. Request/response logging middleware
4. Performance metrics collection
5. Error tracking and reporting system
6. Monitoring dashboards
7. Alerting and on-call setup

---

## 🔧 Technical Specifications

### Architecture

```
┌─────────────────────────────────────────────────────┐
│              Application Logs                        │
│  (FastAPI → structlog → CloudWatch Logs)            │
└─────────────┬───────────────────────────────────────┘
              │
              ├──── Structured JSON logs
              │
┌─────────────▼───────────────────────────────────────┐
│          CloudWatch Logs                             │
│  - /experimentation-platform/api                     │
│  - /experimentation-platform/services                │
│  - /experimentation-platform/errors                  │
└─────────────┬───────────────────────────────────────┘
              │
              ├──── Log Insights Queries
              ├──── Metrics Filters
              │
┌─────────────▼───────────────────────────────────────┐
│          CloudWatch Dashboards                       │
│  - System Health                                     │
│  - API Performance                                   │
│  - Error Tracking                                    │
│  - Business Metrics                                  │
└─────────────────────────────────────────────────────┘
              │
              ├──── Alarms & Notifications
              │
┌─────────────▼───────────────────────────────────────┐
│          SNS → PagerDuty/Slack                       │
└─────────────────────────────────────────────────────┘
```

---

## 📝 Implementation Tasks

### Task 1: Structured Logging (3 days) - FROM TICKET #1

- [ ] **1.1** Research and select logging library
  - Evaluate: `structlog`, `python-json-logger`
  - Decision: Use `structlog` (already in requirements)

- [ ] **1.2** Configure logging levels and formatters
  ```python
  import structlog

  structlog.configure(
      processors=[
          structlog.stdlib.filter_by_level,
          structlog.stdlib.add_logger_name,
          structlog.stdlib.add_log_level,
          structlog.stdlib.PositionalArgumentsFormatter(),
          structlog.processors.TimeStamper(fmt="iso"),
          structlog.processors.StackInfoRenderer(),
          structlog.processors.format_exc_info,
          structlog.processors.UnicodeDecoder(),
          structlog.processors.JSONRenderer()
      ],
      logger_factory=structlog.stdlib.LoggerFactory(),
  )
  ```

- [ ] **1.3** Implement log rotation and retention
  - Local: Use `logging.handlers.RotatingFileHandler`
  - CloudWatch: Configure retention periods (7/30/90 days)

- [ ] **1.4** Add logging context (request ID, user ID, etc.)
  ```python
  logger = logger.bind(
      request_id=request_id,
      user_id=user_id,
      endpoint=request.url.path
  )
  ```

- [ ] **1.5** Document logging standards
  - When to log (errors, key events, security)
  - What to log (context, not sensitive data)
  - How to log (structured fields, levels)

### Task 2: CloudWatch Integration (2 days) - FROM TICKET #2

- [ ] **2.1** Create CloudWatch log groups
  ```bash
  aws logs create-log-group --log-group-name /experimentation-platform/api
  aws logs create-log-group --log-group-name /experimentation-platform/services
  aws logs create-log-group --log-group-name /experimentation-platform/errors
  ```

- [ ] **2.2** Configure IAM roles and permissions
  - Create CloudWatch Logs policy
  - Attach to EC2/ECS task roles
  - Test permissions

- [ ] **2.3** Configure log streaming
  - Use `watchtower` library (already in requirements)
  - Configure batch size and interval
  - Add error handling for failed uploads

- [ ] **2.4** Set up log retention policies
  - API logs: 30 days
  - Service logs: 90 days
  - Error logs: 180 days

### Task 3: Request/Response Logging (3 days) - FROM TICKET #3

- [ ] **3.1** Create FastAPI middleware
  ```python
  @app.middleware("http")
  async def log_requests(request: Request, call_next):
      request_id = str(uuid.uuid4())
      logger.info("request_started",
          method=request.method,
          path=request.url.path,
          request_id=request_id
      )

      start_time = time.time()
      response = await call_next(request)
      duration = time.time() - start_time

      logger.info("request_completed",
          request_id=request_id,
          status_code=response.status_code,
          duration_ms=duration * 1000
      )
      return response
  ```

- [ ] **3.2** Add request/response correlation IDs
- [ ] **3.3** Include timing information
- [ ] **3.4** Implement sensitive data masking
  - Mask passwords, tokens, PII
  - Configurable sensitive fields list

- [ ] **3.5** Log relevant headers and metadata
  - User-Agent, IP address
  - Authentication headers (masked)
  - Custom headers

### Task 4: Performance Metrics (3 days) - FROM TICKET #4

- [ ] **4.1** Identify key metrics to track
  - API latency (P50, P95, P99)
  - Request rate (RPS)
  - Error rate (4xx, 5xx)
  - Database query time
  - Cache hit rate
  - Assignment latency

- [ ] **4.2** Implement metrics collection
  ```python
  from prometheus_client import Counter, Histogram

  request_count = Counter('http_requests_total', 'Total requests')
  request_duration = Histogram('http_request_duration_seconds', 'Request duration')
  ```

- [ ] **4.3** Set up CloudWatch custom metrics
  - Business metrics (experiments created, assignments made)
  - Application metrics (cache hit rate, queue depth)

- [ ] **4.4** Create metrics aggregation system
  - Real-time aggregation
  - Time-windowed metrics (1m, 5m, 1h)

### Task 5: Error Tracking (2 days) - FROM TICKET #5

- [ ] **5.1** Set up error tracking service
  - Option 1: Sentry (recommended)
  - Option 2: CloudWatch Insights + custom solution

- [ ] **5.2** Implement error reporting middleware
  ```python
  from sentry_sdk import init, capture_exception

  @app.exception_handler(Exception)
  async def global_exception_handler(request, exc):
      capture_exception(exc)
      logger.error("unhandled_exception",
          exc_info=exc,
          request_path=request.url.path
      )
  ```

- [ ] **5.3** Create error classification system
  - Critical: Data loss, security breach
  - High: Service down, major feature broken
  - Medium: Feature degraded, performance issue
  - Low: Minor bug, cosmetic issue

- [ ] **5.4** Set up error notifications
  - Critical: PagerDuty (immediate)
  - High: Slack + Email
  - Medium: Slack
  - Low: Dashboard only

### Task 6: Monitoring Dashboards (3 days) - FROM TICKET #6

- [ ] **6.1** System health dashboard
  - CPU, Memory, Disk usage
  - Network I/O
  - Instance health checks

- [ ] **6.2** API performance dashboard
  - Request rate
  - Latency percentiles
  - Error rates
  - Top endpoints

- [ ] **6.3** Business metrics dashboard
  - Active experiments
  - Assignment rate
  - Feature flag evaluations
  - Conversion events

- [ ] **6.4** Error tracking dashboard
  - Error count by type
  - Error rate trends
  - Top errors
  - Error resolution time

### Task 7: Documentation (2 days) - FROM TICKET #7

- [ ] **7.1** Logging standards document
- [ ] **7.2** Dashboard user guide
- [ ] **7.3** Troubleshooting playbook
- [ ] **7.4** On-call runbook
- [ ] **7.5** Alerting procedures

---

## ✅ Acceptance Criteria

### Logging
- [ ] All logs are in structured JSON format
- [ ] Logs include request_id, user_id, timestamp
- [ ] Sensitive data is properly masked
- [ ] Logs are searchable in CloudWatch
- [ ] Log retention policies configured

### Metrics
- [ ] All key metrics are collected
- [ ] Metrics visible in CloudWatch
- [ ] Custom business metrics implemented
- [ ] Metrics aggregation working

### Error Tracking
- [ ] All unhandled exceptions captured
- [ ] Error notifications working
- [ ] Error classification implemented
- [ ] Error trends visible in dashboard

### Dashboards
- [ ] 4 main dashboards created
- [ ] Dashboards auto-refresh
- [ ] Dashboards accessible to team
- [ ] Dashboards documented

### Alerting
- [ ] Critical alerts configured
- [ ] Alert routing to PagerDuty/Slack
- [ ] Alert thresholds tuned
- [ ] Alert fatigue minimized (<5 false alarms/week)

---

## ✔️ Definition of Done

- [ ] All 7 tasks completed
- [ ] Code reviewed and merged
- [ ] Documentation complete
- [ ] Team trained on dashboards and alerts
- [ ] Production deployment successful
- [ ] 1 week of monitoring validated
- [ ] Runbook tested with simulated incident

---

## 📊 Dependencies

### Related Tickets
- From `project/tickets.md`: Tasks 1-7 (Monitoring tickets)
- EP-010: Lambda Functions (need metrics)
- EP-012: Performance Testing (need monitoring)

---

## 🚨 Risks & Mitigation

**Risk:** Excessive logging impacts performance
**Mitigation:** Async logging, sampling, configurable levels

**Risk:** Alert fatigue from too many notifications
**Mitigation:** Careful threshold tuning, alert aggregation

**Risk:** Sensitive data in logs
**Mitigation:** Automated PII detection, masking, audit

---

## 📈 Success Metrics

- MTTR reduced from 2h to 20min (70% improvement)
- 100% of errors captured and tracked
- < 5 false alerts per week
- 99.9% log delivery success rate
- Team can diagnose issues in < 5 minutes

---

**Estimated Completion:** 18 working days (3.6 weeks)
**Target Sprint:** Q1 2026, Sprint 5-6

**Note:** This ticket consolidates all 7 monitoring/logging tickets from `project/tickets.md`
