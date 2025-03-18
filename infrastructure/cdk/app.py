#!/usr/bin/env python3

import os
from aws_cdk import App, Environment

from stacks.vpc_stack import VpcStack
from stacks.compute_stack import ComputeStack
from stacks.api_stack import ApiStack
from stacks.analytics_stack import AnalyticsStack
from stacks.monitoring_stack import MonitoringStack
from stacks.enhanced_database_stack import EnhancedDatabaseStack
from stacks.dynamodb_tables_stack import DynamoDBTablesStack
from stacks.elasticache_redis_stack import ElastiCacheRedisStack  # Import the Redis stack


# Environment determination
env_name = os.environ.get("ENVIRONMENT", "dev")

# Define CDK environment (account and region)
account = os.environ.get("CDK_DEFAULT_ACCOUNT", "214117827798")
region = os.environ.get("CDK_DEFAULT_REGION", "us-west-2")
env = Environment(account=account, region=region)

app = App()

# Create the networking stack (VPC, subnets, etc.)
vpc_stack = VpcStack(app, f"experimentation-vpc-{env_name}", env=env)

# Create the DynamoDB tables stack
dynamodb_stack = DynamoDBTablesStack(
    app,
    f"experimentation-dynamodb-{env_name}",
    environment=env_name,
    env=env
)

# Create the enhanced database stack (with improved Aurora PostgreSQL)
database_stack = EnhancedDatabaseStack(
    app,
    f"experimentation-database-{env_name}",
    vpc=vpc_stack.vpc,
    environment=env_name,
    env=env,
)
database_stack.add_dependency(vpc_stack)

# Create the ElastiCache Redis stack
redis_stack = ElastiCacheRedisStack(
    app,
    f"experimentation-redis-{env_name}",
    vpc=vpc_stack.vpc,
    environment=env_name,
    env=env,
)
redis_stack.add_dependency(vpc_stack)

# Create the compute stack (ECS, Lambda)
compute_stack = ComputeStack(
    app, f"experimentation-compute-{env_name}", vpc=vpc_stack.vpc, env=env
)
compute_stack.add_dependency(vpc_stack)
compute_stack.add_dependency(database_stack)
compute_stack.add_dependency(dynamodb_stack)
compute_stack.add_dependency(redis_stack)  # Add dependency on Redis stack

# Create the API Gateway stack
api_stack = ApiStack(
    app,
    f"experimentation-api-{env_name}",
    vpc=vpc_stack.vpc,
    compute=compute_stack,
    env=env,
)
api_stack.add_dependency(compute_stack)

# Create the analytics stack (Kinesis, OpenSearch)
analytics_stack = AnalyticsStack(
    app, f"experimentation-analytics-{env_name}", vpc=vpc_stack.vpc, env=env
)
analytics_stack.add_dependency(vpc_stack)
analytics_stack.add_dependency(dynamodb_stack)

# Create the monitoring stack (CloudWatch, Alarms)
monitoring_stack = MonitoringStack(
    app, f"experimentation-monitoring-{env_name}", vpc=vpc_stack.vpc, env=env
)
monitoring_stack.add_dependency(vpc_stack)

app.synth()
