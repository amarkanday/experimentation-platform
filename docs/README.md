# Experimentation Platform Documentation

This directory contains documentation for the experimentation platform project.

## Contents

- [Issue Fixes](issue_fixes/index.md) - Documentation of issues fixed and improvements made to the platform
  - [Logging System Improvements](issue_fixes/logging_system_improvements.md)
  - [Logging Middleware and CloudWatch Integration](issue_fixes/logging_middleware_fixes.md)
  - [Feature Flag Testing](issue_fixes/feature_flag_testing.md)
  - [Experiment Testing](issue_fixes/experiment_testing.md)
  - And more...

## Getting Started

For installation instructions and getting started with the experimentation platform, please refer to the main [README.md](../README.md) file at the root of the repository.

## Directory Structure

```
docs/
├── getting-started/           # Getting started guides
│   ├── environment-setup.md
│   ├── docker-guide.md
│   └── requirements.md
│
├── architecture/             # Architecture and design docs
│   ├── overview.md
│   ├── models.md
│   └── infrastructure/
│
├── api/                     # API documentation
│   ├── endpoints.md
│   ├── authentication.md
│   └── specs.md
│
├── development/             # Development guides
│   ├── guidelines.md
│   ├── database/
│   │   ├── migrations.md
│   │   ├── usage.md
│   │   └── backup.md
│   └── dependency-injection.md
│
├── auth/                    # Authentication documentation
│   ├── flow.md
│   ├── environment.md
│   └── user-guide.md
│
└── issue-fixes/            # Issue fixes and troubleshooting
    └── request-validation.md
```

## Quick Links

### Getting Started
- [Environment Setup Guide](getting-started/environment-setup.md)
- [Docker Guide](getting-started/docker-guide.md)
- [Requirements](getting-started/requirements.md)

### API Documentation
- [API Endpoints](api/endpoints.md)
- [API Specifications](api/specs.md)
- [Authentication](api/authentication.md)

### Development
- [Development Guidelines](development/guidelines.md)
- [Database Migrations](development/database/migrations.md)
- [Database Usage](development/database/usage.md)

### Architecture
- [Architecture Overview](architecture/overview.md)
- [Models Documentation](architecture/models.md)
- [Infrastructure](architecture/infrastructure/)

### Authentication
- [Auth Flow](auth/flow.md)
- [Environment Variables](auth/environment.md)
- [User Guide](auth/user-guide.md)

## Common Workflows

### 1. Setting Up Development Environment
1. Check [Requirements](getting-started/requirements.md)
2. Follow [Environment Setup](getting-started/environment-setup.md)
3. Use [Docker Guide](getting-started/docker-guide.md) for container setup
4. Review [Development Guidelines](development/guidelines.md)

### 2. API Integration
1. Review [API Overview](api/README.md)
2. Check [Authentication](api/authentication.md)
3. Use [API Endpoints](api/endpoints.md) for implementation
4. Follow [API Specifications](api/specs.md) for details

### 3. Database Management
1. Follow [Migrations Guide](development/database/migrations.md)
2. Review [Database Usage](development/database/usage.md)
3. Implement [Backup Procedures](development/database/backup.md)
4. Check [Models Documentation](architecture/models.md)

### 4. Authentication Setup
1. Review [Auth Flow](auth/flow.md)
2. Configure [Environment Variables](auth/environment.md)
3. Follow [User Guide](auth/user-guide.md)
4. Check [Developer Guide](auth/auth-developer-docs.md)

## Related Documentation

### Architecture & Design
- [System Overview](architecture/overview.md)
- [Data Models](architecture/models.md)
- [Infrastructure Setup](architecture/infrastructure/)

### Development & Implementation
- [Coding Standards](development/guidelines.md)
- [Dependency Injection](development/dependency-injection.md)
- [Database Management](development/database/)

### Security & Authentication
- [Auth Implementation](auth/auth-developer-docs.md)
- [Security Best Practices](auth/flow.md#security)
- [User Management](auth/user-guide.md)

## Documentation Sections

### Architecture
- [System Architecture](architecture/system-architecture.md)
- [Component Diagrams](architecture/component-diagrams.md)
- [Data Flow](architecture/data-flow.md)

### API
- [API Reference](api/reference.md)
- [Authentication](api/authentication.md)
- [Rate Limiting](api/rate-limiting.md)

### Getting Started
- [Quick Start Guide](getting-started/quick-start.md)
- [Installation](getting-started/installation.md)
- [Configuration](getting-started/configuration.md)

### Development
- [Development Setup](development/setup.md)
- [Coding Standards](development/coding-standards.md)
- [Testing Guide](development/testing.md)
- [CI/CD Pipeline](development/cicd.md)

### Infrastructure
- [AWS Resources](infrastructure/aws-resources.md)
- [CDK Deployment](infrastructure/cdk-deployment.md)
- [Database Setup](infrastructure/database-setup.md)

### Authentication
- [Authentication Flow](auth/authentication-flow.md)
- [Authorization](auth/authorization.md)
- [User Management](auth/user-management.md)

### Monitoring and Error Tracking
- [Monitoring Overview](monitoring/monitoring-overview.md)
- [Setup Guide](monitoring/setup-guide.md)
- [Dashboard Reference](monitoring/dashboard-reference.md)
- [Log Insights Queries](monitoring/log-insights-queries.md)
- [Troubleshooting Guide](monitoring/troubleshooting-guide.md)

## Contributing to Documentation

1. Place new documentation in the appropriate subdirectory
2. Update the relevant index files to link to your new documentation
3. Follow the established markdown formatting patterns

## Documentation Style Guide

1. Use Markdown for all documentation files
2. Include a clear title and description at the top of each file
3. Use proper heading hierarchy (h1, h2, h3)
4. Include code examples with proper syntax highlighting
5. Add cross-references to related documentation
6. Keep files focused and concise
7. Update the table of contents when adding new sections

## Need Help?

- Check the [Getting Started Guide](getting-started/README.md)
- Review the [Development Documentation](development/README.md)
- See the [API Documentation](api/README.md)
- Contact the documentation team for assistance
