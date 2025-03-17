#!/usr/bin/env python3

import os
from aws_cdk import App, Environment

from stacks.vpc_stack import VpcStack
from stacks.database_stack import DatabaseStack
from stacks.compute_stack import ComputeStack
from stacks.api_stack import ApiStack
from stacks.analytics_stack import AnalyticsStack
from stacks.monitoring_stack import MonitoringStack

# Environment determination
env_name = os.environ.get("ENVIRONMENT", "dev")

# Define CDK environment (account and region)
account = os.environ.get("CDK_DEFAULT_ACCOUNT", "214117827798")
region = os.environ.get("CDK_DEFAULT_REGION", "us-west-2")
env = Environment(account=account, region=region)

app = App()

# Create the networking stack (VPC, subnets, etc.)
vpc_stack = VpcStack(app, f"experimentation-vpc-{env_name}", env=env)

# Create the database stack (Aurora, DynamoDB, Redis)
database_stack = DatabaseStack(
    app, f"experimentation-database-{env_name}", vpc=vpc_stack.vpc, env=env
)

# Create the compute stack (ECS, Lambda)
compute_stack = ComputeStack(
    app, f"experimentation-compute-{env_name}", vpc=vpc_stack.vpc, env=env
)

# Create the API Gateway stack
api_stack = ApiStack(
    app,
    f"experimentation-api-{env_name}",
    vpc=vpc_stack.vpc,
    compute=compute_stack,
    env=env,
)

# Create the analytics stack (Kinesis, OpenSearch)
analytics_stack = AnalyticsStack(
    app, f"experimentation-analytics-{env_name}", vpc=vpc_stack.vpc, env=env
)

# Create the monitoring stack (CloudWatch, Alarms)
monitoring_stack = MonitoringStack(
    app, f"experimentation-monitoring-{env_name}", vpc=vpc_stack.vpc, env=env
)

app.synth()
