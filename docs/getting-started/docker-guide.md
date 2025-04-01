
# Comprehensive Guide for Docker Local Development

## Overview

This guide will help you set up and manage your local development environment using Docker Compose, tailored specifically for the Experimentation Platform. The setup includes a PostgreSQL database, Redis caching, LocalStack for AWS service emulation, and optional tools such as PGAdmin for database management.

## Prerequisites

- Docker installed (version 20.x+ recommended)
- Docker Compose installed (version 2.x recommended)
- AWS CLI installed (configured to use LocalStack endpoint)

## Project Structure

Your project structure should look similar to:

```bash
project-root/
├── backend/
├── frontend/
├── localstack/
│   └── init scripts if needed
├── docker-compose.yml
└── .env (optional for environment variables)
```

## Docker Compose File Overview

The provided `docker-compose.yml` includes the following key services:

- **PostgreSQL**: Database storage
- **Redis**: Caching layer
- **LocalStack**: Local emulation of AWS services
- **PGAdmin** *(optional)*: Database administration UI
- **Backend API** *(optional, commented)*
- **Frontend Web** *(optional, commented)*

## Getting Started

### Step 1: Start Services

Navigate to your project root directory:

```bash
cd project-root
```

Start your Docker environment:

```bash
docker-compose up -d
```

This command spins up PostgreSQL, Redis, LocalStack, and PGAdmin (if uncommented).

### Step 2: Verify Services

Check that all services are running:

```bash
docker-compose ps
```

### Step 3: Connect to PostgreSQL

Use PGAdmin at `http://localhost:5050` or connect via terminal:

```bash
docker exec -it experimentation-postgres psql -U postgres
```

Credentials:
- User: `postgres`
- Password: `postgres`
- Database: `experimentation`

### Step 4: Interact with Redis

Check Redis health:

```bash
docker exec -it experimentation-redis redis-cli ping
```

Should return:

```
PONG
```

### Step 5: Working with LocalStack

LocalStack is accessible at:

```bash
http://localhost:4566
```

#### AWS CLI Configuration for LocalStack

Configure AWS CLI to interact with LocalStack:

```bash
aws configure --profile localstack
```

Use the following dummy credentials:

- AWS Access Key ID: `test`
- AWS Secret Access Key: `test`
- Default region: `us-west-2`
- Default output format: `json`

Example AWS CLI usage with LocalStack:

```bash
aws --endpoint-url=http://localhost:4566 --profile localstack dynamodb list-tables
```

#### Creating and Listing DynamoDB Tables

Create a table using AWS CLI:

```bash
aws --endpoint-url=http://localhost:4566 --profile localstack dynamodb create-table --table-name testTable --attribute-definitions AttributeName=id,AttributeType=S --key-schema AttributeName=id,KeyType=HASH --billing-mode PAY_PER_REQUEST
```

List tables:

```bash
aws --endpoint-url=http://localhost:4566 --profile localstack dynamodb list-tables
```

#### Working with S3

Create a bucket:

```bash
aws --endpoint-url=http://localhost:4566 --profile localstack s3 mb s3://my-bucket
```

List buckets:

```bash
aws --endpoint-url=http://localhost:4566 --profile localstack s3 ls
```

### Step 6: Optional Backend and Frontend

To enable and start backend and frontend services, uncomment the respective sections in your `docker-compose.yml`.

Rebuild and start:

```bash
docker-compose up --build -d
```

Backend API is accessible at `http://localhost:8000`, frontend at `http://localhost:3000`.

## Development Workflow

### Backend Development

Mount your backend directory for hot-reloading during development. Modify code within `./backend`, and the changes will reflect automatically without rebuilding the container. Ensure your backend Dockerfile or Docker Compose configuration uses a command like `uvicorn app.main:app --reload` for FastAPI or similar tools for your chosen framework to enable automatic reloading.

**Example (FastAPI)**:

Your `Dockerfile.dev`:

```Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY ./requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . /app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Frontend Development

The frontend setup utilizes Next.js with hot-reloading enabled by default. Modify frontend code in `./frontend`, and the browser will automatically reflect these changes. Ensure your frontend Dockerfile.dev or Docker Compose configuration uses Next.js development mode.

**Example (Next.js)**:

Your `Dockerfile.dev`:

```Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]
```

---

This setup will streamline your local development, ensure consistency across environments, and simplify collaboration across your development team.
