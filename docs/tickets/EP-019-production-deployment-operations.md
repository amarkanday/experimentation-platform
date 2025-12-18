# EP-019: Production Deployment & Operations

**Status:** 🔴 Not Started
**Priority:** 🔥 Critical (Blocker for Production)
**Story Points:** 5
**Sprint:** Phase 6 - Testing & Launch (Week 12)
**Assignee:** DevOps + Backend Team
**Created:** 2025-12-16
**Type:** Infrastructure / Operations

---

## 📋 Overview

### User Story
**As a** DevOps engineer and platform operator
**I want** automated, reliable production deployment procedures with rollback capabilities
**So that** we can deploy safely, minimize downtime, and quickly recover from issues

### Business Value
- **Reliability:** Zero-downtime deployments
- **Speed:** Deploy in < 30 minutes
- **Safety:** Automated rollback on failures
- **Confidence:** Tested deployment procedures

---

## 🎯 Problem Statement

### Current State
- ✅ Infrastructure defined in AWS CDK
- ✅ Staging environment exists
- ❌ **No production deployment automation**
- ❌ **No blue/green deployment strategy**
- ❌ **No automated rollback procedures**
- ❌ **No database migration automation**
- ❌ **No secrets management in production**
- ❌ **No launch checklist**
- ❌ **No disaster recovery plan**

### Risks Without Proper Deployment Procedures
1. **Downtime:** Manual deployments cause service interruptions
2. **Data Loss:** Failed migrations without rollback
3. **Configuration Errors:** Wrong environment variables
4. **Security Issues:** Exposed secrets, misconfigurations
5. **Recovery Delays:** No clear rollback process

---

## 🔧 Technical Specifications

### Deployment Architecture

```
┌──────────────────────────────────────────────────┐
│           Blue/Green Deployment                   │
├──────────────────────────────────────────────────┤
│                                                   │
│  ┌─────────────┐         ┌─────────────┐        │
│  │   BLUE      │         │   GREEN     │        │
│  │  (Current)  │         │   (New)     │        │
│  │             │         │             │        │
│  │  ECS Tasks  │◄────────│  ECS Tasks  │        │
│  │  Running    │  Switch │  Testing    │        │
│  └─────────────┘  Traffic└─────────────┘        │
│         │                        │               │
│         └────────┬───────────────┘               │
│                  │                               │
│         ┌────────▼─────────┐                     │
│         │   ALB / Route53  │                     │
│         │  Traffic Mgmt    │                     │
│         └──────────────────┘                     │
└──────────────────────────────────────────────────┘
```

### Deployment Pipeline

```yaml
Deployment Stages:
  1. Pre-deployment Checks
     - Health checks pass
     - No active incidents
     - Team notification
     - Backup verification

  2. Database Migrations
     - Run migrations in transaction
     - Verify migration success
     - Rollback on failure
     - Compatibility check

  3. Deploy New Version
     - Build and push Docker images
     - Deploy to green environment
     - Run smoke tests
     - Warm up caches

  4. Traffic Cutover
     - Gradual traffic shift (10%, 50%, 100%)
     - Monitor error rates
     - Monitor latency
     - Auto-rollback on errors

  5. Post-deployment
     - Verify metrics
     - Run integration tests
     - Team notification
     - Update status page

  6. Cleanup
     - Remove old version (after 24h)
     - Clean up resources
     - Archive logs
```

---

## 📝 Implementation Tasks

### Phase 1: Secrets Management (0.5 days)

- [ ] **Task 1.1:** Set up AWS Secrets Manager
  ```bash
  # Create secrets
  aws secretsmanager create-secret \
    --name /prod/experimentation/db-password \
    --secret-string "secure-password"

  aws secretsmanager create-secret \
    --name /prod/experimentation/jwt-secret \
    --secret-string "jwt-secret-key"
  ```

- [ ] **Task 1.2:** Update application to use Secrets Manager
  ```python
  import boto3

  def get_secret(secret_name):
      client = boto3.client('secretsmanager')
      response = client.get_secret_value(SecretId=secret_name)
      return response['SecretString']
  ```

- [ ] **Task 1.3:** Configure IAM permissions for secrets access
- [ ] **Task 1.4:** Remove hardcoded secrets from codebase
- [ ] **Task 1.5:** Document secrets rotation procedures

### Phase 2: Database Migration Automation (0.5 days)

- [ ] **Task 2.1:** Create migration CI/CD workflow
  ```yaml
  # .github/workflows/db-migrate.yml
  name: Database Migration
  on:
    workflow_dispatch:
      inputs:
        environment:
          required: true
          type: choice
          options:
            - staging
            - production
  ```

- [ ] **Task 2.2:** Implement migration pre-checks
  ```bash
  # Check pending migrations
  alembic current
  alembic heads

  # Backup database before migration
  pg_dump > backup-$(date +%Y%m%d-%H%M%S).sql
  ```

- [ ] **Task 2.3:** Add migration verification tests
- [ ] **Task 2.4:** Create rollback procedures
  ```bash
  # Rollback last migration
  alembic downgrade -1

  # Restore from backup
  psql < backup-20251216-120000.sql
  ```

### Phase 3: Blue/Green Deployment Setup (1 day)

- [ ] **Task 3.1:** Configure ECS blue/green deployment
  ```python
  # infrastructure/cdk/stacks/deployment_stack.py
  deployment_controller = ecs.DeploymentController(
      type=ecs.DeploymentControllerType.CODE_DEPLOY
  )

  service = ecs.FargateService(
      deployment_controller=deployment_controller,
      health_check_grace_period=Duration.seconds(60)
  )
  ```

- [ ] **Task 3.2:** Set up AWS CodeDeploy
  - Create CodeDeploy application
  - Configure deployment groups
  - Set traffic shifting configuration
  - Define rollback triggers

- [ ] **Task 3.3:** Configure ALB target groups
  ```python
  # Blue target group
  blue_tg = elbv2.ApplicationTargetGroup(...)

  # Green target group
  green_tg = elbv2.ApplicationTargetGroup(...)

  # Listener rules for traffic shifting
  listener.add_action(...)
  ```

- [ ] **Task 3.4:** Set up health checks
  ```python
  health_check = elbv2.HealthCheck(
      path="/health",
      interval=Duration.seconds(30),
      timeout=Duration.seconds(5),
      healthy_threshold_count=2,
      unhealthy_threshold_count=3
  )
  ```

### Phase 4: CI/CD Pipeline (1 day)

- [ ] **Task 4.1:** Create production deployment workflow
  ```yaml
  # .github/workflows/deploy-production.yml
  name: Deploy to Production

  on:
    workflow_dispatch:
      inputs:
        version:
          required: true

  jobs:
    deploy:
      runs-on: ubuntu-latest
      steps:
        - name: Pre-deployment checks
        - name: Run database migrations
        - name: Build Docker images
        - name: Push to ECR
        - name: Deploy to ECS
        - name: Run smoke tests
        - name: Shift traffic
        - name: Post-deployment verification
  ```

- [ ] **Task 4.2:** Implement smoke tests
  ```python
  # tests/smoke/test_production.py
  def test_api_health():
      response = requests.get("https://api.prod.com/health")
      assert response.status_code == 200

  def test_assignment_endpoint():
      response = requests.get("/api/v1/assignments/test")
      assert response.status_code == 200
  ```

- [ ] **Task 4.3:** Add deployment gates
  - Require approval for production
  - Check no active incidents
  - Verify backup exists
  - Check deployment time (office hours only)

- [ ] **Task 4.4:** Configure notifications
  - Slack notifications for deployments
  - Email notifications for failures
  - PagerDuty for critical errors

### Phase 5: Rollback Automation (0.5 days)

- [ ] **Task 5.1:** Implement automated rollback triggers
  ```python
  # Monitor error rate and rollback if needed
  if error_rate > 5% or latency_p99 > 1000ms:
      trigger_rollback()
  ```

- [ ] **Task 5.2:** Create manual rollback workflow
  ```yaml
  # .github/workflows/rollback.yml
  name: Rollback Production
  on:
    workflow_dispatch:
      inputs:
        version:
          description: 'Version to rollback to'
          required: true
  ```

- [ ] **Task 5.3:** Document rollback procedures
  ```markdown
  # Rollback Runbook
  1. Identify last known good version
  2. Run rollback workflow
  3. Verify health checks
  4. Monitor metrics
  5. Notify team
  ```

- [ ] **Task 5.4:** Test rollback procedures
  - Simulate failures
  - Practice rollback in staging
  - Time the rollback process
  - Document lessons learned

### Phase 6: Environment Configuration (0.5 days)

- [ ] **Task 6.1:** Create environment-specific configs
  ```python
  # config/production.py
  DATABASE_URL = get_secret('/prod/db-url')
  REDIS_URL = get_secret('/prod/redis-url')
  LOG_LEVEL = 'INFO'
  DEBUG = False
  RATE_LIMIT = 10000  # requests per minute
  ```

- [ ] **Task 6.2:** Set up environment variables in ECS
  ```python
  task_definition.add_container(
      environment={
          'APP_ENV': 'production',
          'LOG_LEVEL': 'INFO',
          'PYTHONUNBUFFERED': '1'
      },
      secrets={
          'DATABASE_URL': ecs.Secret.from_secrets_manager(db_secret),
          'JWT_SECRET': ecs.Secret.from_secrets_manager(jwt_secret)
      }
  )
  ```

- [ ] **Task 6.3:** Configure auto-scaling
  ```python
  scaling = service.auto_scale_task_count(
      min_capacity=3,
      max_capacity=10
  )

  scaling.scale_on_cpu_utilization('CpuScaling',
      target_utilization_percent=70
  )

  scaling.scale_on_memory_utilization('MemoryScaling',
      target_utilization_percent=80
  )
  ```

### Phase 7: Launch Checklist & Documentation (0.5 days)

- [ ] **Task 7.1:** Create pre-launch checklist
  ```markdown
  ## Pre-Launch Checklist

  ### Security
  - [ ] Security audit completed (EP-018)
  - [ ] All secrets in Secrets Manager
  - [ ] WAF enabled
  - [ ] HTTPS enforced

  ### Infrastructure
  - [ ] Auto-scaling configured
  - [ ] Backups automated
  - [ ] Monitoring dashboards ready
  - [ ] Alerts configured

  ### Application
  - [ ] All tests passing
  - [ ] Performance benchmarks met
  - [ ] Database migrations tested
  - [ ] API documentation updated

  ### Operations
  - [ ] On-call rotation set up
  - [ ] Runbooks documented
  - [ ] Team trained
  - [ ] Status page ready
  ```

- [ ] **Task 7.2:** Document deployment procedures
  - Step-by-step deployment guide
  - Rollback procedures
  - Emergency contact list
  - Escalation procedures

- [ ] **Task 7.3:** Create disaster recovery plan
  ```markdown
  ## Disaster Recovery Plan

  ### RTO (Recovery Time Objective): 1 hour
  ### RPO (Recovery Point Objective): 5 minutes

  ### Scenarios:
  1. Database failure → Restore from backup
  2. Region failure → Failover to DR region
  3. Complete data loss → Restore from S3
  4. Security breach → Isolate and investigate
  ```

- [ ] **Task 7.4:** Create operations runbook
  - Common issues and solutions
  - Performance troubleshooting
  - Scaling procedures
  - Backup and restore procedures

### Phase 8: Post-Launch Monitoring (0.5 days)

- [ ] **Task 8.1:** Set up production monitoring
  - CloudWatch dashboards
  - Synthetic monitors
  - User journey monitoring
  - Business metrics tracking

- [ ] **Task 8.2:** Configure alerting thresholds
  ```yaml
  Alerts:
    - name: High Error Rate
      condition: error_rate > 1%
      action: page_on_call

    - name: High Latency
      condition: p99_latency > 500ms
      action: page_on_call

    - name: Low Success Rate
      condition: success_rate < 99%
      action: slack_notification
  ```

- [ ] **Task 8.3:** Set up status page
  - Public status page (e.g., Statuspage.io)
  - Automated incident updates
  - Subscribe for notifications

---

## ✅ Acceptance Criteria

### Deployment Automation
- [ ] One-click production deployment
- [ ] Automated database migrations
- [ ] Blue/green deployment working
- [ ] Zero-downtime deployment verified
- [ ] Deployment time < 30 minutes

### Rollback Capability
- [ ] Automated rollback on errors
- [ ] Manual rollback in < 5 minutes
- [ ] Rollback tested successfully
- [ ] Database rollback procedures documented

### Security
- [ ] No secrets in code/config
- [ ] All secrets in Secrets Manager
- [ ] IAM least privilege enforced
- [ ] Audit trail for deployments

### Reliability
- [ ] Health checks configured
- [ ] Auto-scaling working
- [ ] Backups automated
- [ ] Disaster recovery plan tested

### Documentation
- [ ] Deployment guide complete
- [ ] Rollback runbook ready
- [ ] Operations runbook available
- [ ] Team trained on procedures

---

## ✔️ Definition of Done

### Automation
- [ ] CI/CD pipeline operational
- [ ] Blue/green deployment working
- [ ] Automated rollback configured
- [ ] Database migrations automated

### Testing
- [ ] Smoke tests passing
- [ ] Rollback tested in staging
- [ ] Load test in production-like environment
- [ ] Disaster recovery drill completed

### Documentation
- [ ] All runbooks created
- [ ] Team walkthrough completed
- [ ] Launch checklist finalized
- [ ] On-call procedures documented

### Approval
- [ ] DevOps team sign-off
- [ ] Engineering manager approval
- [ ] Dry-run deployment successful
- [ ] Ready for production launch

---

## 📊 Dependencies

### Blocked By
- EP-018: Security Audit (must pass before production)
- EP-012: Performance Testing (must meet benchmarks)

### Blocking
- Production launch (final blocker)

### Related Tickets
- EP-013: Monitoring & Logging (monitoring setup)
- EP-018: Security Audit (security requirements)

---

## 🚨 Risks & Mitigation

### Risk 1: Failed Migration in Production
**Impact:** Critical
**Probability:** Low
**Mitigation:**
- Test migrations in staging first
- Always backup before migration
- Have rollback plan ready
- Use backward-compatible migrations

### Risk 2: Traffic Shift Issues
**Impact:** High
**Probability:** Low
**Mitigation:**
- Gradual traffic shifting (10%, 50%, 100%)
- Automated rollback on errors
- Monitor metrics during shift
- Practice in staging

### Risk 3: Configuration Errors
**Impact:** High
**Probability:** Medium
**Mitigation:**
- Environment-specific validation
- Pre-deployment checks
- Configuration drift detection
- Immutable infrastructure

---

## 📈 Success Metrics

### Deployment Performance
- Deployment time < 30 minutes
- Zero-downtime deployments
- Rollback time < 5 minutes
- 100% successful deployments (first 10)

### Reliability
- 99.9% uptime
- < 5 minute incident response time
- < 15 minute recovery time
- Zero data loss incidents

### Team Efficiency
- 100% team confident in deployment
- < 1 hour for new engineer to deploy
- Zero manual deployment steps
- All procedures documented

---

## 📚 Reference Materials

### AWS Documentation
- [ECS Blue/Green Deployment](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-bluegreen.html)
- [AWS CodeDeploy](https://docs.aws.amazon.com/codedeploy/)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)

### Best Practices
- [The Twelve-Factor App](https://12factor.net/)
- [Google SRE Book](https://sre.google/books/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

---

## 🔄 Change Log

| Date       | Author | Change Description |
|------------|--------|-------------------|
| 2025-12-16 | Claude | Initial ticket creation |

---

**Estimated Completion:** 5 working days (1 week)
**Target Sprint:** Q1 2026, Sprint 12 (Launch week)
**Critical for:** Production Launch
**Must Complete Before:** Go-live date
