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

        # Create a dummy Lambda function for assignment since you may not have the actual code yet
        self.assignment_lambda = lambda_.Function(
            self,
            "AssignmentLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_inline(
                """
                def handler(event, context):
                    return {
                        'statusCode': 200,
                        'body': '{"message": "Assignment Lambda placeholder"}'
                    }
                """
            ),
            handler="index.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
        )

        # Create a dummy Lambda function for event processing
        self.event_processor_lambda = lambda_.Function(
            self,
            "EventProcessorLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_inline(
                """
                def handler(event, context):
                    return {
                        'statusCode': 200,
                        'body': '{"message": "Event Processor Lambda placeholder"}'
                    }
                """
            ),
            handler="index.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
        )

        # Create a dummy Lambda function for feature flag evaluation
        self.feature_flag_lambda = lambda_.Function(
            self,
            "FeatureFlagLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_inline(
                """
                def handler(event, context):
                    return {
                        'statusCode': 200,
                        'body': '{"message": "Feature Flag Lambda placeholder"}'
                    }
                """
            ),
            handler="index.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
        )
