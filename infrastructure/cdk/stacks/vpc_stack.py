from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    CfnOutput,
    Tags
)
from constructs import Construct

class VpcStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC with public and private subnets across two AZs
        self.vpc = ec2.Vpc(
            self, "ExperimentationVPC",
            max_azs=2,  # Use 2 Availability Zones for cost optimization in development
            nat_gateways=1,  # Single NAT Gateway for cost optimization (use one per AZ for production)
            cidr="10.0.0.0/16",  # VPC CIDR block
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                    map_public_ip_on_launch=True
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ],
            gateway_endpoints={
                "S3": ec2.GatewayVpcEndpointOptions(
                    service=ec2.GatewayVpcEndpointAwsService.S3
                ),
                "DynamoDB": ec2.GatewayVpcEndpointOptions(
                    service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
                )
            }
        )

        # Add interface endpoints for additional AWS services
        self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER
        )

        self.vpc.add_interface_endpoint(
            "ECREndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.ECR
        )

        self.vpc.add_interface_endpoint(
            "ECRDockerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER
        )

        self.vpc.add_interface_endpoint(
            "CloudWatchLogsEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS
        )

        # Tag all subnets for easy identification
        for subnet in self.vpc.public_subnets:
            Tags.of(subnet).add("SubnetType", "Public")
            Tags.of(subnet).add("Name", f"{self.stack_name}-Public-{subnet.availability_zone}")

        for subnet in self.vpc.private_subnets:
            Tags.of(subnet).add("SubnetType", "Private")
            Tags.of(subnet).add("Name", f"{self.stack_name}-Private-{subnet.availability_zone}")

        for subnet in self.vpc.isolated_subnets:
            Tags.of(subnet).add("SubnetType", "Isolated")
            Tags.of(subnet).add("Name", f"{self.stack_name}-Isolated-{subnet.availability_zone}")

        # Store VPC and subnet information in SSM Parameter Store for cross-stack reference
        ssm.StringParameter(
            self, "VpcId",
            parameter_name="/experimentation/vpc/id",
            string_value=self.vpc.vpc_id
        )

        # Store comma-separated lists of subnet IDs in SSM for easy lookup
        ssm.StringParameter(
            self, "PublicSubnetIds",
            parameter_name="/experimentation/vpc/public-subnet-ids",
            string_value=",".join([subnet.subnet_id for subnet in self.vpc.public_subnets])
        )

        ssm.StringParameter(
            self, "PrivateSubnetIds",
            parameter_name="/experimentation/vpc/private-subnet-ids",
            string_value=",".join([subnet.subnet_id for subnet in self.vpc.private_subnets])
        )

        ssm.StringParameter(
            self, "IsolatedSubnetIds",
            parameter_name="/experimentation/vpc/isolated-subnet-ids",
            string_value=",".join([subnet.subnet_id for subnet in self.vpc.isolated_subnets])
        )

        # Create CloudFormation outputs for easy reference
        CfnOutput(
            self, "VpcIdOutput",
            value=self.vpc.vpc_id,
            description="VPC ID",
            export_name=f"{self.stack_name}-VpcId"
        )

        CfnOutput(
            self, "PublicSubnets",
            value=",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            description="Public Subnet IDs",
            export_name=f"{self.stack_name}-PublicSubnets"
        )

        CfnOutput(
            self, "PrivateSubnets",
            value=",".join([subnet.subnet_id for subnet in self.vpc.private_subnets]),
            description="Private Subnet IDs",
            export_name=f"{self.stack_name}-PrivateSubnets"
        )

        CfnOutput(
            self, "IsolatedSubnets",
            value=",".join([subnet.subnet_id for subnet in self.vpc.isolated_subnets]),
            description="Isolated Subnet IDs",
            export_name=f"{self.stack_name}-IsolatedSubnets"
        )
