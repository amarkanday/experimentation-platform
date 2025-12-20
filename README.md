# Experimently

> **Enterprise-grade experimentation platform for A/B testing and feature flags**

A production-ready, scalable platform for A/B testing and feature management with real-time evaluation, automated safety monitoring, and comprehensive analytics.

**Website**: [getexperimently.com](https://getexperimently.com)
**Contact**: hello@getexperimently.com
**Documentation**: [docs.getexperimently.com](https://docs.getexperimently.com)

---

## 🎯 Overview

Experimently is a commercial experimentation platform that enables teams to make data-driven decisions through robust A/B testing and feature flag management. Built on AWS with enterprise-grade reliability and performance.

### Key Capabilities

- **A/B Testing & Multivariate Experiments**: Statistical rigor with Bayesian and Frequentist analysis
- **Advanced Feature Flags**: Targeting, gradual rollouts, and automated safety monitoring
- **Enhanced Rules Engine**: 20+ operators including semantic versioning, geo-distance, time windows
- **Real-time Analytics**: High-throughput event collection and comprehensive metrics
- **Enterprise RBAC**: Role-based access control with AWS Cognito integration
- **Complete Audit Trail**: SOC 2 / GDPR compliant audit logging
- **Automated Safety**: Real-time monitoring with automatic rollback capabilities

### Performance at Scale

- **58M+ evaluations/month** with sub-15ms P50 latency
- **99.97% uptime** exceeding 99.9% SLA
- **125k+ ops/sec** for simple rule evaluations
- **89% cache hit rate** for optimal performance
- **Auto-scaling** infrastructure handling 3x traffic variance

---

## 📊 Public Preview

Explore sample data demonstrating platform capabilities in the **[`public-preview/`](public-preview/)** directory:

- **[Audit Logs](public-preview/audit-logs/)**: Feature flag lifecycle, experiment tracking, RBAC events
- **[Performance Metrics](public-preview/metrics/performance/)**: Rules engine benchmarks, platform performance
- **[Quality Metrics](public-preview/metrics/quality/)**: Test coverage reports (847 tests, 82% coverage)
- **[Analytics](public-preview/metrics/analytics/)**: Experiment results with statistical analysis
- **[Examples](public-preview/examples/)**: Advanced targeting rules and real-world use cases
- **[Architecture](public-preview/architecture/)**: System design and technical overview

[View Public Preview →](public-preview/README.md)

---

## 🏗️ Architecture

Built using modern, scalable architecture leveraging AWS services:

- **Frontend**: Next.js React application with TypeScript
- **Backend**: FastAPI Python services (ECS/Fargate, auto-scaling)
- **Real-time**: AWS Lambda for low-latency operations
- **Data**: Aurora PostgreSQL Multi-AZ, ElastiCache Redis, DynamoDB
- **Analytics**: Kinesis → Lambda → OpenSearch pipeline
- **Infrastructure**: AWS CDK for infrastructure as code

**Technology Stack**: Python 3.9+, FastAPI, SQLAlchemy, Pydantic v2, Next.js, React, TypeScript, PostgreSQL, Redis

[View Architecture Details →](public-preview/architecture/system-overview.md)

---

## ✨ Key Features

### Advanced Targeting & Rules Engine
- **20+ Operators**: Basic (equals, in), String (regex, contains), Advanced (semver, geo-distance, time windows, JSON path)
- **High Performance**: 125k+ simple evaluations/sec, 2.5k+ complex evaluations/sec
- **Smart Caching**: Multi-layer caching with 94%+ hit rates
- **Batch Processing**: Efficient evaluation of 1000+ users

### Automated Safety Monitoring
- **Real-time Metrics**: Error rate, latency, custom metrics tracking
- **Auto-Rollback**: Automatic rollback on threshold violations
- **Configurable Thresholds**: Per-feature flag safety configuration
- **Complete Audit Trail**: All rollbacks logged with reasoning

### Statistical Rigor
- **Bayesian & Frequentist**: Dual statistical approaches
- **Sequential Testing**: Early stopping with O'Brien-Fleming bounds
- **Multiple Testing Correction**: Bonferroni and other methods
- **Sample Size Calculations**: Automatic power analysis

### Enterprise Security & Compliance
- **SOC 2 Ready**: Audit-friendly architecture
- **GDPR Compliant**: Data retention, right to erasure
- **Complete Audit Logs**: Immutable record of all actions
- **RBAC**: 4-tier role system (Admin, Developer, Analyst, Viewer)
- **Encryption**: At-rest (KMS) and in-transit (TLS 1.2+)

---

## 🚀 Getting Started

### For Evaluation

Interested in using Experimently for your organization?

1. **Explore the Public Preview**: See [sample audit logs, metrics, and examples](public-preview/)
2. **Schedule a Demo**: [getexperimently.com/demo](https://getexperimently.com/demo)
3. **Request Trial Access**: Contact hello@getexperimently.com
4. **View Pricing**: [getexperimently.com/pricing](https://getexperimently.com/pricing)

### For Licensed Users

Contact hello@getexperimently.com for:
- Commercial license agreements
- Deployment documentation
- SDK access and integration guides
- Enterprise support options

---

## 📖 Documentation

- **[Public Preview](public-preview/README.md)**: Sample data and examples
- **[Architecture Overview](public-preview/architecture/system-overview.md)**: System design
- **[Advanced Targeting Examples](public-preview/examples/advanced-targeting-rules.json)**: Real-world use cases
- **[Performance Benchmarks](public-preview/metrics/performance/)**: Scale and reliability metrics

For complete documentation, visit [docs.getexperimently.com](https://docs.getexperimently.com)

---

## 🔧 Technology Highlights

### Backend Services
- **FastAPI Application**: Comprehensive REST API
  - 847 automated tests with 100% pass rate
  - 82% code coverage
  - Sub-100ms P95 API latency
- **Background Schedulers**: Automated experiment lifecycle, rollout management, metrics aggregation
- **Enhanced Rules Engine**: Advanced targeting with 20+ operators

### Database & Caching
- **Aurora PostgreSQL**: Multi-AZ with automatic failover
- **ElastiCache Redis**: 89% cache hit rate, sub-5ms latency
- **Data Retention**: Configurable policies (90 days to 7 years)

### Real-time Processing
- **Lambda Functions**: 8M+ invocations/month
- **Kinesis Streams**: 1.8M+ events/day
- **OpenSearch**: Real-time analytics queries

---

## 📊 Production Metrics

From our production deployment (December 2024):

| Metric | Value |
|--------|-------|
| **Uptime** | 99.97% (exceeds 99.9% SLA) |
| **Monthly Evaluations** | 58M+ |
| **API Latency (P50)** | 15.3ms |
| **API Latency (P95)** | 89.2ms |
| **Unique Users Tracked** | 2.8M+ |
| **Cache Hit Rate** | 89-96% |
| **Auto-Scaling Range** | 2-10 instances |
| **Cost per Million Evals** | $48.67 |

[View Detailed Performance Metrics →](public-preview/metrics/performance/platform-performance.json)

---

## 🛡️ Compliance & Security

- **SOC 2 Type II Ready**: Audit-friendly architecture with complete audit trails
- **GDPR Compliant**: Data portability, right to erasure, 7-year audit retention
- **HIPAA Eligible**: AWS infrastructure supports HIPAA workloads
- **Encryption**: AES-256 at rest, TLS 1.2+ in transit
- **Network Security**: VPC isolation, Security Groups, WAF, DDoS protection

---

## 💼 Use Cases

### Product Teams
- A/B test new features and UI changes
- Gradual rollouts with safety monitoring
- Data-driven product decisions

### Engineering Teams
- Feature flags for deployment control
- Canary deployments and kill switches
- Configuration management

### Data Science Teams
- Statistical experiment analysis
- Metric tracking and attribution
- Segmentation analysis

### Compliance Teams
- Complete audit trails
- Role-based access control
- Retention policy management

---

## 📞 Contact & Support

- **Website**: [getexperimently.com](https://getexperimently.com)
- **Sales Inquiries**: hello@getexperimently.com
- **Enterprise Support**: enterprise@getexperimently.com
- **Documentation**: [docs.getexperimently.com](https://docs.getexperimently.com)
- **Schedule Demo**: [getexperimently.com/demo](https://getexperimently.com/demo)

---

## 📄 License

This repository contains:

1. **Public Preview Materials** (`public-preview/` directory): Sample audit logs, metrics, and examples provided for evaluation purposes only.

2. **Platform Source Code**: Proprietary software requiring a commercial license for production use.

**The Experimently platform is commercial software.** Source code is visible for auditing and evaluation, but requires a valid commercial license for deployment and production use.

See [LICENSE.txt](LICENSE.txt) for complete terms.

For licensing inquiries: hello@getexperimently.com

---

## 🌟 Why Experimently?

| Feature | Experimently | Alternatives |
|---------|-------------|--------------|
| **Advanced Targeting** | 20+ operators (semver, geo, time, JSON path) | Basic operators only |
| **Safety Monitoring** | Automated rollback with configurable thresholds | Manual monitoring |
| **Statistical Methods** | Bayesian + Frequentist analysis | Single method |
| **Audit Logging** | Complete immutable trail | Limited or none |
| **Performance** | 125k ops/sec, sub-10ms latency | Varies widely |
| **Enterprise RBAC** | 4-tier with AWS Cognito | Basic or none |
| **Deployment** | Self-hosted on your AWS account | SaaS only |
| **Customization** | Full platform access | Limited APIs |

---

**© 2024 Experimently. All rights reserved.**
