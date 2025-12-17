# Docker Compose Configuration for Local Development

Below is a comprehensive `docker-compose.yml` file for setting up a local development environment for the experimentation platform. This configuration includes all necessary services: PostgreSQL, Redis, LocalStack (for AWS services emulation), and optional application containers.

```yaml
version:"3.8"

services:
    # PostgreSQL database
    postgres:
        image: postgres:15-alpine
        container_name: experimentation-postgres
        ports:
            - "5432:5432"
        environment:
            POSTGRES_USER: postgres
            POSTGRES_PASSWORD: postgres
            POSTGRES_DB: experimentation
        volumes:
            - postgres_data:/var/lib/postgresql/data
        healthcheck:
            test: ["CMD-SHELL", "pg_isready -U postgres"]
            interval: 5s
            timeout: 5s
            retries: 5

    # Redis for caching
    redis:
        image: redis:7-alpine
        container_name: experimentation-redis
        ports:
            - "6379:6379"
        volumes:
            - redis_data:/data
        command: redis-server --appendonly yes
        healthcheck:
            test: ["CMD", "redis-cli", "ping"]
            interval: 5s
            timeout: 5s
            retries: 5

    # LocalStack for AWS services emulation
    localstack:
        image: localstack/localstack:latest
        container_name: experimentation-localstack
        ports:
            - "4566:4566" # LocalStack edge port
        environment:
            - SERVICES=dynamodb,s3,kinesis,lambda,cognito,sqs,opensearch
            - DEBUG=1
            - DATA_DIR=/tmp/localstack/data
        volumes:
            - ./localstack:/docker-entrypoint-initaws.d
            - localstack_data:/tmp/localstack

    # PGAdmin for database management (optional)
    pgadmin:
        image: dpage/pgadmin4:latest
        container_name: experimentation-pgadmin
        depends_on:
            - postgres
        ports:
            - "5050:80"
        environment:
            PGADMIN_DEFAULT_EMAIL: admin@example.com
            PGADMIN_DEFAULT_PASSWORD: admin
        volumes:
            - pgadmin_data:/var/lib/pgadmin

    # Backend API service (optional - uncomment to use)
    # api:
    #   build:
    #     context: ./backend
    #     dockerfile: Dockerfile.dev
    #   container_name: experimentation-api
    #   ports:
    #     - "8000:8000"
    #   volumes:
    #     - ./backend:/app
    #   environment:
    #     - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/experimentation
    #     - REDIS_URL=redis://redis:6379/0
    #     - AWS_ENDPOINT_URL=http://localstack:4566
    #     - AWS_REGION=us-east-1
    #     - AWS_ACCESS_KEY_ID=test
    #     - AWS_SECRET_ACCESS_KEY=test
    #   depends_on:
    #     postgres:
    #       condition: service_healthy
    #     redis:
    #       condition: service_healthy
    #     localstack:
    #       condition: service_started

    # Frontend service (optional - uncomment to use)
    # web:
    #   build:
    #     context: ./frontend
    #     dockerfile: Dockerfile.dev
    #   container_name: experimentation-web
    #   ports:
    #     - "3000:3000"
    #   volumes:
    #     - ./frontend:/app
    #     - /app/node_modules
    #   environment:
    #     - NEXT_PUBLIC_API_URL=http://localhost:8000
    #   depends_on:
    #     - api

volumes:
    postgres_data:
    redis_data:
    pgadmin_data:
    localstack_data:
```

## Usage Instructions

1. Save this file as `docker-compose.yml` in the root directory of your project.

2. Create a folder named `localstack` in the root directory to store initialization scripts for LocalStack:

```bash
mkdir -p localstack
```

3. Create a basic LocalStack initialization script (`localstack/init-aws.sh`):

```bash
#!/bin/bash

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
aws --endpoint-url=http://localhost:4566 --region=us-east-1 dynamodb list-tables

# Create DynamoDB tables
echo "Creating DynamoDB tables..."
aws --endpoint-url=http://localhost:4566 --region=us-east-1 dynamodb create-table \
    --table-name assignments \
    --attribute-definitions AttributeName=id,AttributeType=S AttributeName=user_id,AttributeType=S AttributeName=experiment_id,AttributeType=S \
    --key-schema AttributeName=id,KeyType=HASH \
    --global-secondary-indexes \
        "IndexName=user_experiment_index,KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=experiment_id,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
    --billing-mode PAY_PER_REQUEST

aws --endpoint-url=http://localhost:4566 --region=us-east-1 dynamodb create-table \
    --table-name events \
    --attribute-definitions AttributeName=id,AttributeType=S \
    --key-schema AttributeName=id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# Create S3 bucket
echo "Creating S3 bucket..."
aws --endpoint-url=http://localhost:4566 --region=us-east-1 s3 mb s3://experimentation-events

# Create Kinesis Stream
echo "Creating Kinesis stream..."
aws --endpoint-url=http://localhost:4566 --region=us-east-1 kinesis create-stream \
    --stream-name event-stream \
    --shard-count 1

echo "LocalStack initialization complete!"
```

4. Make the script executable:

```bash
chmod +x localstack/init-aws.sh
```

5. Start the services:

```bash
docker-compose up -d
```

6. Access the services:

    - PostgreSQL: localhost:5432
    - Redis: localhost:6379
    - LocalStack AWS services: localhost:4566
    - PGAdmin: http://localhost:5050 (login with admin@example.com / admin)

7. Stop the services:

```bash
docker-compose down
```

## Notes

-   The backend and frontend services are commented out by default. Uncomment them if you want to run the application services in Docker as well.
-   LocalStack provides emulation for AWS services which allows you to develop and test without connecting to actual AWS services.
-   PGAdmin is included for easy database management through a web interface.
-   All data is persisted in Docker volumes, so your data will remain between container restarts.
-   You may need to adjust environment variables and configurations based on your specific application requirements.
