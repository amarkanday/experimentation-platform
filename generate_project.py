#!/usr/bin/env python3
"""
Experimentation Platform Directory Structure Generator

This script creates a directory structure for an experimentation platform based on the
AWS architecture and requirements we've defined. It sets up folders for backend, frontend,
infrastructure, documentation, and SDK components.
"""

import os
import sys

def create_directory(path):
    """Create a directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def create_file(path, content=""):
    """Create a file with optional content if it doesn't exist"""
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write(content)
        print(f"Created file: {path}")
    else:
        print(f"File already exists: {path}")

def generate_directory_structure(base_dir):
    """Generate the complete directory structure for the experimentation platform"""
    print(f"Generating directory structure in: {base_dir}")
    
    # Create base directory
    create_directory(base_dir)
    
    # Create documentation directory
    docs_dir = os.path.join(base_dir, "docs")
    create_directory(docs_dir)
    create_file(os.path.join(docs_dir, "architecture.md"), "# Experimentation Platform Architecture\n\nDetails of the AWS-based architecture for the experimentation platform.")
    create_file(os.path.join(docs_dir, "requirements.md"), "# Experimentation Platform Requirements\n\nDetailed requirements for the experimentation platform.")
    create_file(os.path.join(docs_dir, "api_specs.md"), "# API Specifications\n\nAPI reference for the experimentation platform.")
    
    # Create infrastructure directory (AWS CDK)
    infra_dir = os.path.join(base_dir, "infrastructure")
    create_directory(infra_dir)
    
    # CDK app
    cdk_dir = os.path.join(infra_dir, "cdk")
    create_directory(cdk_dir)
    create_file(os.path.join(cdk_dir, "app.py"), "#!/usr/bin/env python3\n\nfrom aws_cdk import core\n\n# CDK application entry point")
    
    # CDK stacks
    stacks_dir = os.path.join(cdk_dir, "stacks")
    create_directory(stacks_dir)
    create_file(os.path.join(stacks_dir, "vpc_stack.py"), "# VPC and networking infrastructure")
    create_file(os.path.join(stacks_dir, "compute_stack.py"), "# ECS and Lambda compute resources")
    create_file(os.path.join(stacks_dir, "database_stack.py"), "# Aurora, DynamoDB, and Redis resources")
    create_file(os.path.join(stacks_dir, "api_stack.py"), "# API Gateway configuration")
    create_file(os.path.join(stacks_dir, "analytics_stack.py"), "# Analytics infrastructure (Kinesis, OpenSearch)")
    create_file(os.path.join(stacks_dir, "monitoring_stack.py"), "# CloudWatch monitoring and alerting")
    
    # Create backend directory
    backend_dir = os.path.join(base_dir, "backend")
    create_directory(backend_dir)
    
    # FastAPI application
    app_dir = os.path.join(backend_dir, "app")
    create_directory(app_dir)
    create_file(os.path.join(app_dir, "main.py"), "from fastapi import FastAPI\n\napp = FastAPI(title=\"Experimentation Platform API\")\n\n# Main FastAPI application entry point")
    
    # API routes
    api_dir = os.path.join(app_dir, "api")
    create_directory(api_dir)
    create_directory(os.path.join(api_dir, "v1"))
    
    endpoints_dir = os.path.join(api_dir, "v1", "endpoints")
    create_directory(endpoints_dir)
    create_file(os.path.join(endpoints_dir, "experiments.py"), "# Experiment management endpoints")
    create_file(os.path.join(endpoints_dir, "feature_flags.py"), "# Feature flag management endpoints")
    create_file(os.path.join(endpoints_dir, "events.py"), "# Event collection endpoints")
    create_file(os.path.join(endpoints_dir, "assignments.py"), "# Experiment assignment endpoints")
    create_file(os.path.join(endpoints_dir, "results.py"), "# Results and analysis endpoints")
    create_file(os.path.join(endpoints_dir, "users.py"), "# User management endpoints")
    
    # Core modules
    core_dir = os.path.join(app_dir, "core")
    create_directory(core_dir)
    create_file(os.path.join(core_dir, "config.py"), "# Application configuration")
    create_file(os.path.join(core_dir, "security.py"), "# Authentication and authorization")
    create_file(os.path.join(core_dir, "aws.py"), "# AWS integrations")
    
    # Database
    db_dir = os.path.join(app_dir, "db")
    create_directory(db_dir)
    create_file(os.path.join(db_dir, "session.py"), "# Database session management")
    create_file(os.path.join(db_dir, "init_db.py"), "# Database initialization")
    
    # Models
    models_dir = os.path.join(app_dir, "models")
    create_directory(models_dir)
    create_file(os.path.join(models_dir, "experiment.py"), "# Experiment database models")
    create_file(os.path.join(models_dir, "feature_flag.py"), "# Feature flag database models")
    create_file(os.path.join(models_dir, "event.py"), "# Event database models")
    create_file(os.path.join(models_dir, "user.py"), "# User database models")
    create_file(os.path.join(models_dir, "segment.py"), "# Segmentation models")
    
    # Schemas
    schemas_dir = os.path.join(app_dir, "schemas")
    create_directory(schemas_dir)
    create_file(os.path.join(schemas_dir, "experiment.py"), "# Experiment Pydantic schemas")
    create_file(os.path.join(schemas_dir, "feature_flag.py"), "# Feature flag Pydantic schemas")
    create_file(os.path.join(schemas_dir, "event.py"), "# Event Pydantic schemas")
    create_file(os.path.join(schemas_dir, "user.py"), "# User Pydantic schemas")
    
    # Services
    services_dir = os.path.join(app_dir, "services")
    create_directory(services_dir)
    create_file(os.path.join(services_dir, "experiment_service.py"), "# Experiment management service")
    create_file(os.path.join(services_dir, "feature_flag_service.py"), "# Feature flag management service")
    create_file(os.path.join(services_dir, "assignment_service.py"), "# Experiment assignment service")
    create_file(os.path.join(services_dir, "event_service.py"), "# Event tracking service")
    create_file(os.path.join(services_dir, "analysis_service.py"), "# Analysis and reporting service")
    create_file(os.path.join(services_dir, "user_service.py"), "# User management service")
    
    # Tests
    tests_dir = os.path.join(backend_dir, "tests")
    create_directory(tests_dir)
    create_file(os.path.join(tests_dir, "conftest.py"), "# Pytest configuration")
    create_directory(os.path.join(tests_dir, "api"))
    create_directory(os.path.join(tests_dir, "services"))
    create_directory(os.path.join(tests_dir, "models"))
    
    # Lambda functions
    lambda_dir = os.path.join(backend_dir, "lambda")
    create_directory(lambda_dir)
    
    # Assignment Lambda
    assignment_lambda_dir = os.path.join(lambda_dir, "assignment")
    create_directory(assignment_lambda_dir)
    create_file(os.path.join(assignment_lambda_dir, "lambda_function.py"), "# Experiment assignment Lambda function")
    create_file(os.path.join(assignment_lambda_dir, "requirements.txt"), "# Assignment Lambda dependencies")
    
    # Event processing Lambda
    event_lambda_dir = os.path.join(lambda_dir, "event_processor")
    create_directory(event_lambda_dir)
    create_file(os.path.join(event_lambda_dir, "lambda_function.py"), "# Event processing Lambda function")
    create_file(os.path.join(event_lambda_dir, "requirements.txt"), "# Event processor Lambda dependencies")
    
    # Feature flag evaluation Lambda
    ff_lambda_dir = os.path.join(lambda_dir, "feature_flag_evaluation")
    create_directory(ff_lambda_dir)
    create_file(os.path.join(ff_lambda_dir, "lambda_function.py"), "# Feature flag evaluation Lambda function")
    create_file(os.path.join(ff_lambda_dir, "requirements.txt"), "# Feature flag Lambda dependencies")
    
    # Docker configuration
    create_file(os.path.join(backend_dir, "Dockerfile"), "# Backend Dockerfile\nFROM python:3.10-slim\n\n# Docker build instructions")
    create_file(os.path.join(backend_dir, "requirements.txt"), "# Python dependencies\nfastapi>=0.95.0\nuvicorn>=0.22.0\nsqlalchemy>=2.0.0\npydantic>=1.10.0\naws-sdk-pandas>=2.20.0")
    
    # Create frontend directory
    frontend_dir = os.path.join(base_dir, "frontend")
    create_directory(frontend_dir)
    
    # Next.js configuration
    create_file(os.path.join(frontend_dir, "package.json"), "{\n  \"name\": \"experimentation-platform-frontend\",\n  \"version\": \"0.1.0\",\n  \"private\": true\n}")
    create_file(os.path.join(frontend_dir, "next.config.js"), "/** @type {import('next').NextConfig} */\nmodule.exports = {\n  reactStrictMode: true,\n}")
    create_file(os.path.join(frontend_dir, "tsconfig.json"), "{\n  \"compilerOptions\": {\n    \"target\": \"es5\",\n    \"lib\": [\"dom\", \"dom.iterable\", \"esnext\"],\n    \"allowJs\": true,\n    \"skipLibCheck\": true,\n    \"strict\": true,\n    \"forceConsistentCasingInFileNames\": true,\n    \"noEmit\": true,\n    \"esModuleInterop\": true,\n    \"module\": \"esnext\",\n    \"moduleResolution\": \"node\",\n    \"resolveJsonModule\": true,\n    \"isolatedModules\": true,\n    \"jsx\": \"preserve\",\n    \"baseUrl\": \".\",\n    \"paths\": {\n      \"@/*\": [\"./src/*\"]\n    }\n  },\n  \"include\": [\"next-env.d.ts\", \"**/*.ts\", \"**/*.tsx\"],\n  \"exclude\": [\"node_modules\"]\n}")
    
    # Next.js source directory
    src_dir = os.path.join(frontend_dir, "src")
    create_directory(src_dir)
    
    # Pages
    pages_dir = os.path.join(src_dir, "pages")
    create_directory(pages_dir)
    create_file(os.path.join(pages_dir, "_app.tsx"), "import '@/styles/globals.css';\nimport type { AppProps } from 'next/app';\n\nexport default function App({ Component, pageProps }: AppProps) {\n  return <Component {...pageProps} />;\n}")
    create_file(os.path.join(pages_dir, "index.tsx"), "export default function Home() {\n  return (\n    <div>\n      <h1>Experimentation Platform</h1>\n    </div>\n  );\n}")
    
    # Experiment pages
    exp_pages_dir = os.path.join(pages_dir, "experiments")
    create_directory(exp_pages_dir)
    create_file(os.path.join(exp_pages_dir, "index.tsx"), "// Experiments list page")
    create_file(os.path.join(exp_pages_dir, "new.tsx"), "// New experiment page")
    create_file(os.path.join(exp_pages_dir, "[id].tsx"), "// Experiment details page")
    
    # Feature flag pages
    ff_pages_dir = os.path.join(pages_dir, "feature-flags")
    create_directory(ff_pages_dir)
    create_file(os.path.join(ff_pages_dir, "index.tsx"), "// Feature flags list page")
    create_file(os.path.join(ff_pages_dir, "new.tsx"), "// New feature flag page")
    create_file(os.path.join(ff_pages_dir, "[id].tsx"), "// Feature flag details page")
    
    # Results pages
    results_pages_dir = os.path.join(pages_dir, "results")
    create_directory(results_pages_dir)
    create_file(os.path.join(results_pages_dir, "index.tsx"), "// Results dashboard page")
    create_file(os.path.join(results_pages_dir, "[id].tsx"), "// Experiment results page")
    
    # Components
    components_dir = os.path.join(src_dir, "components")
    create_directory(components_dir)
    create_directory(os.path.join(components_dir, "experiments"))
    create_directory(os.path.join(components_dir, "feature-flags"))
    create_directory(os.path.join(components_dir, "results"))
    create_directory(os.path.join(components_dir, "layout"))
    create_directory(os.path.join(components_dir, "ui"))
    
    # Hooks, utils and services
    create_directory(os.path.join(src_dir, "hooks"))
    create_directory(os.path.join(src_dir, "utils"))
    create_directory(os.path.join(src_dir, "services"))
    create_directory(os.path.join(src_dir, "styles"))
    create_file(os.path.join(src_dir, "styles", "globals.css"), "/* Global styles */")
    
    # Frontend Docker configuration
    create_file(os.path.join(frontend_dir, "Dockerfile"), "# Frontend Dockerfile\nFROM node:18-alpine\n\n# Docker build instructions")
    
    # Create SDKs directory
    sdk_dir = os.path.join(base_dir, "sdk")
    create_directory(sdk_dir)
    
    # JavaScript SDK
    js_sdk_dir = os.path.join(sdk_dir, "js")
    create_directory(js_sdk_dir)
    create_file(os.path.join(js_sdk_dir, "package.json"), "{\n  \"name\": \"experimentation-platform-js-sdk\",\n  \"version\": \"0.1.0\",\n  \"main\": \"dist/index.js\"\n}")
    create_directory(os.path.join(js_sdk_dir, "src"))
    create_file(os.path.join(js_sdk_dir, "src", "index.ts"), "// JavaScript SDK entry point")
    create_file(os.path.join(js_sdk_dir, "src", "experiment.ts"), "// Experiment assignment functionality")
    create_file(os.path.join(js_sdk_dir, "src", "feature-flag.ts"), "// Feature flag functionality")
    create_file(os.path.join(js_sdk_dir, "src", "events.ts"), "// Event tracking functionality")
    
    # Python SDK
    python_sdk_dir = os.path.join(sdk_dir, "python")
    create_directory(python_sdk_dir)
    create_file(os.path.join(python_sdk_dir, "setup.py"), "# Python SDK setup script")
    create_directory(os.path.join(python_sdk_dir, "experimentation"))
    create_file(os.path.join(python_sdk_dir, "experimentation", "__init__.py"), "# Python SDK package")
    create_file(os.path.join(python_sdk_dir, "experimentation", "client.py"), "# Client class for the experimentation platform")
    create_file(os.path.join(python_sdk_dir, "experimentation", "experiments.py"), "# Experiment functionality")
    create_file(os.path.join(python_sdk_dir, "experimentation", "feature_flags.py"), "# Feature flag functionality")
    create_file(os.path.join(python_sdk_dir, "experimentation", "events.py"), "# Event tracking functionality")
    
    # Root project files
    create_file(os.path.join(base_dir, "docker-compose.yml"), "# Docker Compose configuration for local development")
    create_file(os.path.join(base_dir, "README.md"), "# Experimentation Platform\n\nA scalable platform for A/B testing and feature flags built on AWS.")
    create_file(os.path.join(base_dir, ".gitignore"), "# Python\n__pycache__/\n*.py[cod]\n*$py.class\n.pytest_cache/\n.coverage\nvenv/\n.env\n\n# JavaScript\nnode_modules/\n.next/\ndist/\nbuild/\ncoverage/\n\n# Infrastructure\ncdk.out/\n.aws-sam/\n\n# IDE\n.vscode/\n.idea/\n*.swp\n*.swo")
    
    # CI/CD configuration
    github_dir = os.path.join(base_dir, ".github")
    create_directory(github_dir)
    create_directory(os.path.join(github_dir, "workflows"))
    create_file(os.path.join(github_dir, "workflows", "backend-tests.yml"), "# GitHub Actions workflow for backend tests")
    create_file(os.path.join(github_dir, "workflows", "frontend-tests.yml"), "# GitHub Actions workflow for frontend tests")
    create_file(os.path.join(github_dir, "workflows", "infrastructure-tests.yml"), "# GitHub Actions workflow for infrastructure tests")
    create_file(os.path.join(github_dir, "workflows", "deploy-dev.yml"), "# GitHub Actions workflow for development deployment")
    create_file(os.path.join(github_dir, "workflows", "deploy-prod.yml"), "# GitHub Actions workflow for production deployment")

    print("\nDirectory structure creation complete!")
    print(f"Project created at: {os.path.abspath(base_dir)}")

def print_structure_explanation():
    """Print an explanation of the directory structure"""
    explanation = """
Experimentation Platform Directory Structure Explanation
========================================================

/docs
-----
Contains all documentation for the project:
- architecture.md: Details of the AWS architecture
- requirements.md: Platform requirements
- api_specs.md: API specifications

/infrastructure
---------------
Infrastructure as Code (IaC) using AWS CDK:
- /cdk: AWS CDK project
  - /stacks: Individual CloudFormation stack definitions
    - vpc_stack.py: Network infrastructure
    - compute_stack.py: ECS/Lambda compute resources
    - database_stack.py: Database resources (Aurora, DynamoDB, Redis)
    - api_stack.py: API Gateway configuration
    - analytics_stack.py: Analytics resources (Kinesis, OpenSearch)
    - monitoring_stack.py: CloudWatch monitoring

/backend
--------
Backend services using FastAPI:
- /app: Main application code
  - main.py: FastAPI application entry point
  - /api: API endpoint definitions
    - /v1/endpoints: API v1 endpoints for experiments, feature flags, etc.
  - /core: Core application components
  - /db: Database configuration
  - /models: SQLAlchemy database models
  - /schemas: Pydantic schemas for validation
  - /services: Business logic services
- /tests: Backend tests
- /lambda: AWS Lambda functions
  - /assignment: Experiment assignment Lambda
  - /event_processor: Event processing Lambda
  - /feature_flag_evaluation: Feature flag evaluation Lambda
- Dockerfile: Backend container definition
- requirements.txt: Python dependencies

/frontend
---------
Frontend application using Next.js:
- /src: Source code
  - /pages: Next.js page components
    - /experiments: Experiment management pages
    - /feature-flags: Feature flag management pages
    - /results: Results analysis pages
  - /components: Reusable React components
  - /hooks: Custom React hooks
  - /utils: Utility functions
  - /services: API service clients
  - /styles: CSS styles
- next.config.js: Next.js configuration
- tsconfig.json: TypeScript configuration
- Dockerfile: Frontend container definition

/sdk
----
Client SDKs for integrating with the platform:
- /js: JavaScript/TypeScript SDK
  - /src: Source code
    - index.ts: Main entry point
    - experiment.ts: Experiment assignment
    - feature-flag.ts: Feature flag functionality
    - events.ts: Event tracking
- /python: Python SDK
  - /experimentation: Package code
    - client.py: Main client class
    - experiments.py: Experiment functionality
    - feature_flags.py: Feature flag functionality
    - events.py: Event tracking

Root Files
----------
- docker-compose.yml: Local development environment
- README.md: Project documentation
- .gitignore: Git ignore patterns

/.github
--------
CI/CD configuration:
- /workflows: GitHub Actions workflows for testing and deployment
"""
    print(explanation)

if __name__ == "__main__":
    print("Experimentation Platform Directory Structure Generator")
    print("======================================================")
    
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = input("Enter base directory for the project [./experimentation-platform]: ").strip()
        if not base_dir:
            base_dir = "./experimentation-platform"
    
    generate_directory_structure(base_dir)
    print_structure_explanation()
