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
