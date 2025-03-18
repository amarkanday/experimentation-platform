from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
)
from constructs import Construct


class ComputeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Environment determination
        env_name = self.node.try_get_context("env") or "dev"

        # Create an ECS cluster for the backend services
        self.ecs_cluster = ecs.Cluster(
            self, "ECSCluster", vpc=vpc, container_insights=True
        )

        # Create a security group for the ECS tasks
        self.ecs_security_group = ec2.SecurityGroup(
            self,
            "ECSSecurityGroup",
            vpc=vpc,
            description="Allow ECS access",
            allow_all_outbound=True,
        )

        # Allow inbound traffic on port 8000 (FastAPI)
        self.ecs_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(8000), "Allow inbound HTTP traffic"
        )

        # Create a Lambda role
        lambda_role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # Add VPC access policy to allow Lambdas to be placed in VPC
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaVPCAccessExecutionRole"
            )
        )

        # Create a dummy Lambda function for assignment
        self.assignment_lambda = lambda_.Function(
            self,
            "AssignmentLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_inline(
                "def handler(event, context):\n"
                "    return {\n"
                "        'statusCode': 200,\n"
                "        'body': '{\"message\": \"Assignment Lambda placeholder\"}'\n"
                "    }\n"
            ),
            handler="index.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
            environment={
                "ENVIRONMENT": env_name,
            },
        )

        # Create a dummy Lambda function for event processing
        self.event_processor_lambda = lambda_.Function(
            self,
            "EventProcessorLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_inline(
                "def handler(event, context):\n"
                "    return {\n"
                "        'statusCode': 200,\n"
                "        'body': '{\"message\": \"Event Processor Lambda placeholder\"}'\n"
                "    }\n"
            ),
            handler="index.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
            environment={
                "ENVIRONMENT": env_name,
            },
        )

        # Create a dummy Lambda function for feature flag evaluation
        self.feature_flag_lambda = lambda_.Function(
            self,
            "FeatureFlagLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_inline(
                "def handler(event, context):\n"
                "    return {\n"
                "        'statusCode': 200,\n"
                "        'body': '{\"message\": \"Feature Flag Lambda placeholder\"}'\n"
                "    }\n"
            ),
            handler="index.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
            environment={
                "ENVIRONMENT": env_name,
            },
        )

        # Create database access Lambda role with additional permissions
        db_lambda_role = iam.Role(
            self,
            "DatabaseLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                ),
            ],
        )

        # Add specific policy for database access (Secrets Manager and SSM)
        db_access_policy = iam.Policy(
            self,
            "DatabaseAccessPolicy",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret",
                    ],
                    resources=["*"],  # In production, restrict to specific secrets
                ),
                iam.PolicyStatement(
                    actions=[
                        "ssm:GetParameter",
                        "ssm:GetParameters",
                    ],
                    resources=[
                        f"arn:aws:ssm:{self.region}:{self.account}:parameter/experimentation/{env_name}/database/*"
                    ],
                ),
            ],
        )

        # Attach the policy to the role
        db_access_policy.attach_to_role(db_lambda_role)

        # Create a simplified database access Lambda
        # Note: In a real application, you should store this code in a separate file
        self.db_access_lambda = lambda_.Function(
            self,
            "DatabaseAccessLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_inline(
                "def handler(event, context):\n"
                "    # This is a simplified placeholder\n"
                "    # In production, use lambda_.Code.from_asset() instead\n"
                "    return {\n"
                "        'statusCode': 200,\n"
                "        'body': '{\"message\": \"Database access placeholder\"}'\n"
                "    }\n"
            ),
            handler="index.handler",
            timeout=Duration.seconds(60),
            memory_size=512,
            role=db_lambda_role,
            environment={
                "ENVIRONMENT": env_name,
            },
        )

        # Create a log group with retention policy
        db_logs = logs.LogGroup(
            self,
            "DatabaseLambdaLogs",
            log_group_name=f"/aws/lambda/{self.db_access_lambda.function_name}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )
