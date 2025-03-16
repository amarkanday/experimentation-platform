# Experimentation Platform

A scalable, AWS-based platform for A/B testing and feature flags with real-time evaluation capabilities.

## Overview

This platform enables teams to make data-driven decisions through robust experimentation and feature management. Built on AWS, it offers high-throughput event collection, real-time experiment assignment, and comprehensive analytics.

Key capabilities:

-   A/B testing, multivariate testing, and split URL testing
-   Feature flags with targeting and gradual rollouts
-   Real-time metric tracking and statistical analysis
-   User segmentation for targeted experiments
-   Role-based access control

## Architecture

The platform is built using a modern, scalable architecture leveraging AWS services:

-   **Frontend**: Next.js React application for experiment management and analytics dashboards
-   **Backend**: FastAPI Python services running on ECS/Fargate
-   **Real-time Services**: AWS Lambda functions for low-latency operations
-   **Data Storage**: Aurora PostgreSQL, DynamoDB, ElastiCache Redis, S3
-   **Event Pipeline**: Kinesis, Lambda, OpenSearch for real-time analytics
-   **Infrastructure**: Defined with AWS CDK for infrastructure as code

## Directory Structure

```
experimentation-platform/
├── docs/                     # Project documentation
├── infrastructure/           # AWS CDK infrastructure code
│   ├── cdk/                  # CDK app and stack definitions
│   └── tests/                # Infrastructure tests
├── backend/                  # Backend services and APIs
│   ├── app/                  # FastAPI application
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Core functionality
│   │   ├── db/               # Database configuration
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # Business logic
│   ├── tests/                # Backend tests
│   └── lambda/               # AWS Lambda functions
├── frontend/                 # Next.js frontend application
│   ├── src/                  # Source code
│   │   ├── pages/            # Next.js pages
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom React hooks
│   │   ├── services/         # API client services
│   │   └── styles/           # CSS styles
│   └── __tests__/            # Frontend tests
└── sdk/                      # Client SDKs
    ├── js/                   # JavaScript SDK
    └── python/               # Python SDK
```

## Getting Started

### Prerequisites

-   AWS Account with appropriate permissions
-   Node.js 18+ and npm
-   Python 3.9+
-   Docker and Docker Compose

### Local Development Setup

1. **Clone the repository**

```sh
git clone https://github.com/your-org/experimentation-platform.git
cd experimentation-platform
```

2. **Set up Python environment**

```sh
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up frontend dependencies**

```sh
cd frontend
npm install
```

4. **Start the local development environment**

```sh
# From the project root directory
docker-compose up -d
```

5. **Run the backend API**

```sh
cd backend
uvicorn app.main:app --reload
```

6. **Run the frontend application**

```sh
cd frontend
npm run dev
```

The application will be available at:

-   Backend API: http://localhost:8000
-   Frontend: http://localhost:3000
-   API Documentation: http://localhost:8000/docs

### Running Tests

We follow test-driven development practices with comprehensive test coverage.

**Backend Tests**

```sh
cd backend
pytest
```

**Frontend Tests**

```sh
cd frontend
npm test
```

**Infrastructure Tests**

```sh
cd infrastructure
pytest
```

## Deployment

### Infrastructure Deployment

1. **Bootstrap AWS CDK** (if not already done)

```sh
cd infrastructure
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

2. **Deploy the infrastructure**

```sh
cd infrastructure
cdk deploy --all
```

### Application Deployment

The application is deployed automatically via GitHub Actions when changes are pushed to the main branch.

You can also manually deploy:

```sh
# Deploy backend
cd backend
aws ecr get-login-password | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.REGION.amazonaws.com
docker build -t experimentation-backend .
docker tag experimentation-backend:latest ACCOUNT.dkr.ecr.REGION.amazonaws.com/experimentation-backend:latest
docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/experimentation-backend:latest

# Deploy frontend
cd frontend
npm run build
aws s3 sync out/ s3://experimentation-platform-frontend
```

## Using the Platform

### Creating an Experiment

1. Log in to the platform
2. Navigate to "Experiments" and click "New Experiment"
3. Enter experiment details (name, hypothesis, metrics)
4. Add variants and set traffic allocation
5. Configure targeting (optional)
6. Start the experiment

### Managing Feature Flags

1. Navigate to "Feature Flags" and click "New Feature Flag"
2. Enter feature flag details
3. Configure targeting rules
4. Set rollout percentages
5. Toggle the feature flag on/off

### Integrating with Applications

Use our client SDKs to integrate the platform with your applications:

**JavaScript**

```js
import { ExperimentationClient } from "@your-org/experimentation-sdk";

const client = new ExperimentationClient("API_KEY");

// Check experiment variant
const variant = await client.getVariant("experiment-key", userId);
if (variant === "treatment") {
    // Show treatment experience
} else {
    // Show control experience
}

// Check feature flag
const isEnabled = await client.isFeatureEnabled("feature-key", userId);
if (isEnabled) {
    // Enable feature
}

// Track event
client.trackEvent("purchase_completed", userId, { value: 99.99 });
```

**Python**

```python
from experimentation import Client

client = Client(api_key='API_KEY')

# Check experiment variant
variant = client.get_variant('experiment-key', user_id)
if variant == 'treatment':
    # Show treatment experience
else:
    # Show control experience

# Check feature flag
is_enabled = client.is_feature_enabled('feature-key', user_id)
if is_enabled:
    # Enable feature

# Track event
client.track_event('purchase_completed', user_id, metadata={'value': 99.99})
```

## Contributing

We welcome contributions to the platform! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `pytest` and `npm test`
5. Commit your changes: `git commit -m 'Add my feature'`
6. Push to the branch: `git push origin feature/my-feature`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
