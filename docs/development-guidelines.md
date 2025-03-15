# Experimentation Platform Development Guidelines

This document outlines the development standards, workflows, and best practices for the Experimentation Platform project. All team members should follow these guidelines to ensure code quality, maintainability, and consistency.

## Table of Contents

1. [Development Environment](#development-environment)
2. [Git Workflow](#git-workflow)
3. [Coding Standards](#coding-standards)
4. [Test-Driven Development](#test-driven-development)
5. [Code Review Process](#code-review-process)
6. [Documentation](#documentation)
7. [Continuous Integration](#continuous-integration)
8. [Security Guidelines](#security-guidelines)
9. [Performance Considerations](#performance-considerations)

## Development Environment

### Prerequisites

- Python 3.9+
- Node.js 16+
- Docker and Docker Compose
- AWS CLI v2
- AWS CDK v2

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/experimentation-platform.git
   cd experimentation-platform
   ```

2. Set up the backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pre-commit install
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   ```

4. Start the local development environment:
   ```bash
   # From the project root
   docker-compose up -d
   ```

5. Run the backend server:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

6. Run the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

### Environment Variables

Create a `.env` file in the backend directory with these variables:
```
# Development settings - NEVER use these in production
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/experimentation
REDIS_URL=redis://localhost:6379/0
AWS_PROFILE=experimentation-dev
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

For local AWS services, you can use [localstack](https://github.com/localstack/localstack) which is included in the Docker Compose configuration.

## Git Workflow

We follow a Trunk-Based Development workflow with short-lived feature branches.

### Branch Naming

- Feature branches: `feature/short-description`
- Bug fixes: `fix/issue-reference-description`
- Documentation: `docs/what-is-being-documented`
- Infrastructure: `infra/what-is-being-changed`

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) standard:

```
feat: add user authentication middleware
^--^  ^--------------------------^
|     |
|     +-> Summary in present tense
|
+-------> Type: feat, fix, docs, style, refactor, test, chore
```

Common types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or modifying tests
- `chore`: Changes to the build process, tooling, etc.

### Pull Requests

1. Create a new branch from `main`
2. Make your changes, committing regularly
3. Write or update tests for your changes
4. Ensure all tests pass locally
5. Push your branch and create a Pull Request
6. Fill out the PR template with all required information
7. Request reviews from at least two team members
8. Address review feedback

PRs should be small and focused on a single issue or feature. Large changes should be broken down into smaller PRs.

## Coding Standards

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use [Black](https://github.com/psf/black) for code formatting (line length: 88)
- Sort imports with [isort](https://pycqa.github.io/isort/)
- Use type hints for all function parameters and return values
- Document functions and classes with docstrings (Google style)
- Use meaningful variable and function names

### TypeScript/JavaScript

- Follow the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use TypeScript for all new code
- Use functional components and hooks for React
- Prefer named exports over default exports
- Use ESLint and Prettier for code formatting

### Infrastructure as Code

- Use AWS CDK for all infrastructure definitions
- Document all resources with comments
- Use environment variables for configurable values
- Follow least-privilege principles for IAM roles

## Test-Driven Development

We follow test-driven development (TDD) practices:

1. Write tests first
2. Run the tests to ensure they fail (Red)
3. Write the minimum amount of code to make tests pass (Green)
4. Refactor the code while keeping tests passing (Refactor)

### Test Coverage Requirements

- Backend code: minimum 80% coverage
- Frontend components: minimum 70% coverage
- Critical paths: 100% coverage

### Testing Framework Standards

- **Backend**: pytest with pytest-cov for coverage
  ```bash
  cd backend
  python -m pytest --cov=app
  ```

- **Frontend**: Jest with React Testing Library
  ```bash
  cd frontend
  npm test
  ```

- **Infrastructure**: AWS CDK assertions library
  ```bash
  cd infrastructure
  npm test
  ```

## Code Review Process

All code changes require review before merging:

1. **Automated Checks**: All PRs must pass CI checks (tests, linting, type checking)
2. **Peer Review**: At least one approval from a team member
3. **Maintainer Review**: Final approval from a project maintainer

### Review Checklist

Reviewers should check for:

- Code correctness and quality
- Test coverage and quality
- Documentation
- Performance implications
- Security considerations
- Adherence to coding standards

### Review Etiquette

- Be respectful and constructive
- Focus on the code, not the person
- Provide specific, actionable feedback
- Respond to reviews promptly
- Use GitHub's suggestion feature for simple changes

## Documentation

Documentation is crucial for the project's success:

### Code Documentation

- All public functions must have docstrings
- Complex logic should be explained with comments
- Update README and relevant docs when adding/changing features

### API Documentation

- API endpoints are documented using OpenAPI/Swagger
- The API docs are available at `/docs` when running the backend
- Update API docs when changing endpoints

### Architecture Documentation

- Keep architecture diagrams updated
- Document design decisions and trade-offs
- Update data flow diagrams when changing system behavior

## Continuous Integration

We use GitHub Actions for CI/CD:

- **On Pull Request**: Run tests, linting, type checking
- **On Merge to Main**: Deploy to development environment
- **On Release**: Deploy to staging and production environments

### CI Checks

All PRs must pass these checks:

- Unit tests
- Integration tests
- Code formatting (Black, Prettier)
- Linting (Flake8, ESLint)
- Type checking (MyPy, TypeScript)
- Security scanning (Bandit, npm audit)

## Security Guidelines

Security is a priority for our platform:

- No secrets in code or Git history
- Use AWS Secrets Manager for sensitive configuration
- Follow OWASP secure coding practices
- Implement proper input validation
- Use parameterized queries for database operations
- Apply least privilege principle for all services
- Regularly update dependencies

### Authentication & Authorization

- Use Cognito for user authentication
- Implement role-based access control
- Always verify permissions before operations
- Use JWT tokens with appropriate expiration
- Implement proper token validation and refresh

## Performance Considerations

Performance is critical for experimentation platforms:

### Assignment Service

- Must respond in < 50ms (p99)
- Use caching aggressively
- Implement consistent hashing for stability
- Optimize database queries

### Event Collection

- Design for high throughput (thousands/second)
- Use batch processing where possible
- Implement backpressure mechanisms
- Monitor queue depths and latency

### General Guidelines

- Profile code regularly
- Set up performance benchmarks
- Monitor database query performance
- Use pagination for large result sets
- Implement proper caching strategies
