# VPC Implementation with Public and Private Subnets

This document provides the implementation of a VPC with public, private, and isolated subnets for the Experimentation Platform using AWS CDK.

## VPC Stack Implementation

```python
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
```

## Architecture Details

This VPC implementation includes:

### Subnet Types

1. **Public Subnets**
   - Direct internet access via Internet Gateway
   - Resources receive public IP addresses
   - Ideal for load balancers, bastion hosts, NAT gateways
   - Located in 2 different Availability Zones for high availability

2. **Private Subnets**
   - No direct internet access
   - Outbound internet access via NAT Gateway
   - Ideal for application servers, containers, and Lambda functions
   - Protected from direct internet exposure while maintaining outbound access

3. **Isolated Subnets**
   - No internet access (inbound or outbound)
   - Completely isolated from the internet
   - Ideal for databases and internal services that don't need internet connectivity
   - Maximum security for sensitive data

### Network Architecture

- **CIDR Range**: 10.0.0.0/16 (65,536 IP addresses)
- **Availability Zones**: 2 AZs for cost optimization in development (increase for production)
- **NAT Gateways**: 1 for cost optimization (use 1 per AZ for high availability in production)

### VPC Endpoints

1. **Gateway Endpoints** (free):
   - Amazon S3
   - DynamoDB

2. **Interface Endpoints** (paid):
   - AWS Secrets Manager
   - Amazon ECR API
   - Amazon ECR Docker
   - CloudWatch Logs

These endpoints allow services within the VPC to access AWS services without going through the internet, improving security and reducing data transfer costs.

### Resource Management

- **Resource Tagging**: All subnets are tagged with their type and name for easy identification
- **SSM Parameters**: VPC and subnet IDs are stored in SSM Parameter Store for easy reference
- **CloudFormation Outputs**: Exported for cross-stack references

## Deployment Considerations

- For development environments, this configuration uses 2 AZs and 1 NAT Gateway to optimize costs
- For production environments, consider:
  - Increasing to 3+ AZs for higher availability
  - Using 1 NAT Gateway per AZ for resilience
  - Adding more interface endpoints for additional AWS services
  - Implementing more granular security groups

## Cost Components

- **VPC**: No charge
- **Subnets**: No charge
- **Route Tables**: No charge 
- **Internet Gateway**: No charge
- **NAT Gateway**: ~$32/month per gateway + data processing charges
- **Interface Endpoints**: ~$7.30/month per endpoint per AZ
- **Gateway Endpoints**: Free

The primary cost drivers are NAT Gateways and Interface Endpoints.
