# Experimently - Public Preview

Welcome to the Experimently public preview! This directory contains sample audit logs, performance metrics, and examples that demonstrate the capabilities of our enterprise experimentation platform.

## Overview

Experimently is a production-ready, enterprise-grade A/B testing and feature flag platform built on AWS. This preview showcases real-world examples of the platform's audit trail, performance characteristics, and advanced features.

## What's Included

### 1. Audit Logs (`audit-logs/`)

Sample audit logs demonstrating:
- **Compliance & Governance**: Complete audit trail for all platform actions
- **RBAC Integration**: Role-based access control with AWS Cognito
- **Change Tracking**: Before/after values for all modifications
- **Safety Monitoring**: Automated rollback audit trails
- **User Attribution**: Full user context for every action

Use cases: SOC 2 compliance, GDPR audit requirements, security monitoring, debugging

### 2. Performance Metrics (`metrics/performance/`)

Real-world performance benchmarks showing:
- **Enhanced Rules Engine**: 125k+ ops/sec for simple evaluations
- **Advanced Operators**: Semantic versioning, geo-distance, time windows
- **Cache Performance**: 94%+ hit rates with sub-millisecond lookups
- **Batch Evaluation**: Process 1000+ users in under 4 seconds
- **Production Scale**: 58M+ evaluations/month, 99.97% uptime

### 3. Quality Metrics (`metrics/quality/`)

Test coverage and quality metrics demonstrating:
- **847 automated tests** with 100% pass rate
- **82% overall code coverage**
- **Test-driven development** practices
- Component-level coverage breakdown
- Performance benchmarks included in test suite

### 4. Analytics Metrics (`metrics/analytics/`)

Business value metrics showing:
- **Experiment Results**: Statistical analysis with confidence intervals
- **Conversion Tracking**: Multi-variant testing results
- **Platform Usage**: Scale and reliability statistics
- **Business Impact**: Revenue lift, conversion rate improvements

### 5. Advanced Examples (`examples/`)

Real-world targeting and configuration examples:
- **Multi-condition targeting rules**
- **Advanced operators** (semver, geo-distance, time windows, JSON path)
- **Gradual rollout schedules**
- **Safety monitoring configurations**
- **SDK integration patterns**

### 6. Architecture Documentation (`architecture/`)

System design and technical details:
- **High-level architecture diagrams**
- **Technology stack overview**
- **Scalability characteristics**
- **Security and compliance features**
- **Integration patterns**

## Key Platform Features Demonstrated

### Enterprise-Grade Audit Trail
- Every action logged with full context
- Immutable audit records
- Filterable by user, entity, action type, time range
- Retention policies and archival support

### High-Performance Evaluation Engine
- Sub-10ms P50 latency for feature flag evaluations
- Advanced targeting with 20+ operators
- Intelligent caching with configurable TTLs
- Batch evaluation support

### Automated Safety Monitoring
- Real-time error rate and latency tracking
- Automatic rollback on threshold violations
- Configurable safety metrics per feature flag
- Complete rollback audit trail

### Statistical Rigor
- Bayesian and Frequentist analysis
- Automatic sample size calculations
- Multiple testing correction
- Sequential testing support

### AWS-Native Architecture
- ECS/Fargate for compute
- Aurora PostgreSQL for data
- Lambda for real-time operations
- CloudWatch for monitoring
- Cognito for authentication

## Technology Stack

**Backend**: FastAPI (Python 3.9+), SQLAlchemy, Pydantic v2
**Frontend**: Next.js, React, TypeScript
**Database**: PostgreSQL (Aurora), Redis (ElastiCache)
**Infrastructure**: AWS CDK, Docker
**Analytics**: Kinesis, Lambda, OpenSearch
**Authentication**: AWS Cognito with RBAC

## Use Cases

Experimently is designed for:

- **Product Teams**: A/B testing, feature flags, gradual rollouts
- **Engineering Teams**: Canary deployments, kill switches, configuration management
- **Data Science Teams**: Experimentation analysis, metric tracking, statistical testing
- **Compliance Teams**: Audit trails, access control, change tracking
- **DevOps Teams**: Infrastructure flags, deployment automation

## Performance Characteristics

Based on production-equivalent load testing:

- **API Latency**: P50: 15ms, P95: 45ms, P99: 120ms
- **Throughput**: 58M+ evaluations/month
- **Availability**: 99.97% uptime
- **Scalability**: Auto-scaling to handle traffic spikes
- **Reliability**: Automated failover, multi-AZ deployment

## Compliance & Security

- **SOC 2 Type II** ready architecture
- **GDPR** compliant audit logs and data retention
- **HIPAA** eligible infrastructure (AWS)
- **Role-based access control** (Admin, Developer, Analyst, Viewer)
- **Audit logging** for all sensitive operations
- **Encryption** at rest and in transit

## Getting Started

Interested in using Experimently for your organization?

**Website**: [getexperimently.com](https://getexperimently.com)
**Contact**: hello@getexperimently.com
**Documentation**: [docs.getexperimently.com](https://docs.getexperimently.com)

### Quick Links

- [Schedule a Demo](https://getexperimently.com/demo)
- [View Pricing](https://getexperimently.com/pricing)
- [Request Trial Access](https://getexperimently.com/trial)
- [Enterprise Inquiry](mailto:enterprise@getexperimently.com)

## What's Not Included

This preview does **not** include:
- Production source code (available under commercial license)
- Customer data or configurations
- Infrastructure deployment scripts
- API keys or credentials
- Internal documentation

## License

The materials in this `public-preview/` directory are provided for evaluation purposes only.

The Experimently platform source code in this repository is proprietary and requires a commercial license for use. See [LICENSE.txt](../LICENSE.txt) for details.

---

**© 2024 Experimently. All rights reserved.**
