# Experimently Platform - System Architecture Overview

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Applications                           │
│  (Web Apps, Mobile Apps, Backend Services via SDK)                  │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 ├─── JavaScript SDK
                 ├─── Python SDK
                 └─── REST API
                 │
┌────────────────▼────────────────────────────────────────────────────┐
│                      CloudFront CDN + API Gateway                    │
│              (SSL/TLS, DDoS Protection, Rate Limiting)               │
└────────────────┬────────────────────────────────────────────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
┌─────▼─────────┐    ┌─────▼──────────────────────────────────────────┐
│ Lambda@Edge   │    │   Application Layer (ECS Fargate)              │
│ (A/B Testing) │    │   - FastAPI Backend (2-10 instances)           │
│               │    │   - Auto-scaling based on CPU/requests         │
└───────────────┘    │   - Multi-AZ deployment                        │
                     └─────┬──────────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
    ┌─────────▼──┐  ┌─────▼─────┐  ┌──▼────────────┐
    │ Aurora PG  │  │  ElastiCache│  │   DynamoDB    │
    │ (Primary)  │  │   (Redis)   │  │ (Session Store│
    │ Multi-AZ   │  │  Multi-AZ   │  │  & KV Store)  │
    └────────────┘  └─────────────┘  └───────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
         ┌──────▼─────┐        ┌─────▼──────┐
         │  Kinesis   │        │  Lambda    │
         │  Stream    │───────▶│ Processors │
         └────────────┘        └─────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │ OpenSearch  │
                              │ (Analytics) │
                              └─────────────┘
```

## Core Components

### 1. Application Layer

**FastAPI Backend (Python 3.9+)**
- **API Server**: RESTful API with comprehensive endpoints
  - Experiments: CRUD, assignment, scheduling
  - Feature Flags: CRUD, evaluation, rollout management
  - Users: Authentication, RBAC, team management
  - Metrics: Event tracking, aggregation, reporting
  - Audit Logs: Complete audit trail
  - Safety Monitoring: Automated rollback system

- **Background Services**:
  - Experiment Scheduler: Automatic start/stop based on dates
  - Rollout Scheduler: Gradual feature flag rollouts
  - Metrics Aggregator: Real-time and batch aggregation
  - Safety Monitor: Continuous monitoring with auto-rollback

- **Enhanced Rules Engine**:
  - 20+ operators (basic, string, advanced)
  - Rule compilation with LRU caching
  - Evaluation result caching (5-minute TTL)
  - Sub-10ms P50 latency for evaluations
  - Batch processing support

### 2. Data Layer

**Aurora PostgreSQL (Primary Database)**
- Multi-AZ deployment for high availability
- Automatic failover (< 2 minutes)
- Point-in-time recovery
- Schema: `experimentation`
- Key tables:
  - `experiments`, `feature_flags`, `users`
  - `audit_logs`, `raw_metrics`, `aggregated_metrics`
  - `safety_settings`, `rollout_schedules`

**ElastiCache Redis (Caching Layer)**
- Multi-AZ with automatic failover
- Use cases:
  - Feature flag evaluation cache (89% hit rate)
  - Session management
  - Rate limiting
  - Rule compilation cache
- Eviction policy: LRU
- TTL: Configurable per key (default 5 minutes)

**DynamoDB (NoSQL Storage)**
- Session store for authentication
- Configuration key-value store
- High-throughput, low-latency access

### 3. Real-Time Processing

**Lambda Functions**
- **Assignment Lambda**: Real-time experiment assignment
  - Provisioned concurrency (5 instances)
  - Cold start: <900ms, Warm: <10ms
  - 8M+ invocations/month

- **Metrics Processor Lambda**: Process events from Kinesis
  - Batch processing (50 events/batch)
  - Writes to OpenSearch and PostgreSQL

**Kinesis Data Stream**
- Event ingestion pipeline
- 1.8M+ events/day
- Buffering and batching for efficiency

**OpenSearch**
- Real-time analytics queries
- Dashboards and visualizations
- Event log retention: 90 days

### 4. Authentication & Authorization

**AWS Cognito**
- User authentication
- OAuth 2.0 / OpenID Connect
- MFA support
- Group-based role assignment

**RBAC System**
- 4 roles: Admin, Developer, Analyst, Viewer
- Fine-grained permissions per resource
- Owner-based access control
- Complete audit trail

### 5. Monitoring & Observability

**CloudWatch**
- Application logs (7-day retention)
- Error logs (30-day retention)
- Performance metrics
- Custom dashboards:
  - System Health Dashboard
  - API Performance Dashboard

**CloudWatch Alarms**
- High error rates
- Latency spikes
- Database connection pool exhaustion
- Lambda timeout rates

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.9+
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic v2
- **Testing**: pytest, pytest-asyncio
- **Code Quality**: black, isort, mypy, flake8

### Frontend
- **Framework**: Next.js 13+
- **Language**: TypeScript 5.0+
- **UI Library**: React 18+
- **Styling**: Tailwind CSS
- **State Management**: React Context + hooks
- **API Client**: axios

### Infrastructure
- **IaC**: AWS CDK (TypeScript)
- **Compute**: ECS Fargate
- **Database**: Aurora PostgreSQL 14.9
- **Cache**: ElastiCache Redis 7.0
- **Serverless**: Lambda (Python 3.9)
- **CDN**: CloudFront
- **Container Registry**: ECR

### SDKs
- **JavaScript/TypeScript**: Node.js 16+, browser support
- **Python**: Python 3.7+

## Performance Characteristics

### API Latency
- **P50**: 15ms
- **P95**: 89ms
- **P99**: 246ms
- **Throughput**: 5 req/sec average, 247 req/sec peak

### Feature Flag Evaluation
- **Simple rules**: 125k+ ops/sec
- **Complex rules**: 2.5k-3k ops/sec
- **Cache hit rate**: 89-96%
- **Batch processing**: 312 users/sec (1000-user batch)

### Database
- **Query latency P50**: 12ms
- **Query latency P99**: 124ms
- **Connections**: 42 avg, 187 peak (500 max)
- **Storage growth**: 2.1 GB/month

### Availability
- **Uptime**: 99.97% (SLA: 99.9%)
- **MTTR**: 6.5 minutes
- **Auto-scaling**: 2-10 instances
- **Multi-AZ**: Automatic failover

## Security Features

### Data Protection
- **Encryption at rest**: AWS KMS
- **Encryption in transit**: TLS 1.2+
- **Database encryption**: Aurora native encryption
- **Backup encryption**: AES-256

### Access Control
- **API Authentication**: JWT tokens via Cognito
- **API Keys**: For SDK/service authentication
- **RBAC**: 4-tier role system
- **MFA**: Optional for admin accounts

### Network Security
- **VPC**: Isolated network
- **Security Groups**: Restrictive ingress/egress
- **WAF**: Web Application Firewall
- **DDoS Protection**: AWS Shield Standard

### Compliance
- **Audit Logging**: Complete trail of all actions
- **Data Retention**: Configurable per data type
- **SOC 2 Ready**: Audit-friendly architecture
- **GDPR**: Right to erasure, data portability

## Scalability Design

### Horizontal Scaling
- **API Servers**: Auto-scaling 2-10 instances
- **Database Read Replicas**: Up to 15 replicas
- **Lambda**: Automatic scaling to demand
- **Cache**: Redis cluster mode available

### Vertical Scaling
- **Database**: db.r6g.2xlarge → db.r6g.16xlarge
- **Cache**: cache.r6g.xlarge → cache.r6g.4xlarge
- **Lambda**: 1024MB → 10240MB memory

### Performance Optimization
- **Caching**: Multi-layer (Redis, in-memory, CDN)
- **Connection Pooling**: Optimized pool sizes
- **Batch Processing**: Reduce database round-trips
- **Async Processing**: Non-blocking I/O
- **CDN**: Static asset caching

## Disaster Recovery

### Backup Strategy
- **Database**: Automated daily snapshots (35-day retention)
- **Point-in-time**: 5-minute granularity
- **Cross-region**: Optional backup replication

### Failover
- **Database**: Automatic Multi-AZ failover (<2 min)
- **Cache**: Automatic Redis failover
- **Application**: Health checks + auto-restart
- **DNS**: Route 53 health checks

### RTO/RPO Targets
- **RTO**: < 15 minutes (application layer)
- **RPO**: < 5 minutes (database)
- **Data Loss**: Minimal (continuous replication)

## Cost Optimization

### Reserved Capacity
- Aurora Reserved Instances: 35% savings
- ElastiCache Reserved Nodes: 30% savings

### Auto-Scaling
- Scale down during off-peak hours
- Peak-to-off-peak ratio: 3.2x

### Data Lifecycle
- Raw metrics: 90-day retention
- Aggregated metrics: 2-year retention
- Audit logs: 7-year retention
- S3 Lifecycle: Glacier after 90 days

### Cost Per Million Evaluations
- **Current**: $48.67/million
- **At scale (100M/month)**: $32/million (projected)

## Integration Patterns

### SDK Integration
```javascript
// JavaScript Example
import { ExperimentationClient } from '@experimently/sdk';

const client = new ExperimentationClient({
  apiKey: 'your-api-key',
  environment: 'production'
});

const variant = await client.getVariant('experiment-key', userId);
const isEnabled = await client.isFeatureEnabled('feature-key', userId);
```

### REST API Integration
```bash
# Direct API calls
curl -X POST https://api.experimently.com/v1/feature-flags/my-flag/evaluate \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "context": {"country": "US"}}'
```

### Webhook Integration
- Real-time event notifications
- Experiment status changes
- Safety rollback alerts
- Metric threshold breaches

## Deployment Architecture

### CI/CD Pipeline
1. **GitHub Actions**: Automated testing
2. **Build**: Docker image creation
3. **ECR**: Image storage
4. **ECS**: Rolling deployment
5. **Health Checks**: Automated validation
6. **Rollback**: Automatic on failure

### Environments
- **Development**: Local Docker Compose
- **Staging**: AWS (smaller instance sizes)
- **Production**: AWS (full redundancy)

### Blue-Green Deployment
- Zero-downtime deployments
- Traffic shifting via load balancer
- Automatic rollback capability
- Smoke tests before cutover

---

**For more information**: hello@getexperimently.com
**Documentation**: https://docs.getexperimently.com
