import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template
from infrastructure.cdk.stacks.vpc_stack import VpcStack

@pytest.fixture
def app():
    return cdk.App()

@pytest.fixture
def stack(app):
    return VpcStack(app, "TestVpcStack")

@pytest.fixture
def template(stack):
    return Template.from_stack(stack)

def test_vpc_created(template):
    # Verify that exactly one VPC is created
    template.resource_count_is("AWS::EC2::VPC", 1)
    # Optionally, check that the VPC uses the expected CIDR/IP configuration
    template.has_resource_properties("AWS::EC2::VPC", {
        "CidrBlock": "10.0.0.0/16"  # This may appear if using ip_addresses as cidr
    })

def test_subnet_outputs(template):
    # Check that outputs for public, private, and isolated subnets exist
    template.has_output("PublicSubnets", {})
    template.has_output("PrivateSubnets", {})
    template.has_output("IsolatedSubnets", {})

def test_security_group_outputs(template):
    # Check that outputs for App, Db, and Bastion security groups exist.
    template.has_output("AppSecurityGroup", {})
    template.has_output("DbSecurityGroup", {})
    # Use the updated output ID for Bastion Security Group to avoid duplication.
    template.has_output("BastionSecurityGroupOutput", {})

def test_gateway_endpoints(template):
    # Check that a VPC endpoint for S3 exists
    template.has_resource_properties("AWS::EC2::VPCEndpoint", {
        "ServiceName": {
            "Fn::Join": [
                "",
                [
                    "com.amazonaws.",
                    { "Ref": "AWS::Region" },
                    ".s3"
                ]
            ]
        }
    })
    # Check that a VPC endpoint for DynamoDB exists
    template.has_resource_properties("AWS::EC2::VPCEndpoint", {
        "ServiceName": {
            "Fn::Join": [
                "",
                [
                    "com.amazonaws.",
                    { "Ref": "AWS::Region" },
                    ".dynamodb"
                ]
            ]
        }
    })
