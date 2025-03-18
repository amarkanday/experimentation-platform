from aws_cdk import Stack, aws_ec2 as ec2, aws_ssm as ssm, CfnOutput, Tags
from constructs import Construct


class VpcStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC with public and private subnets across two AZs
        self.vpc = ec2.Vpc(
            self,
            "ExperimentationVPC",
            max_azs=2,
            nat_gateways=2,  # One NAT Gateway per AZ for high availability
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                    map_public_ip_on_launch=True,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
            gateway_endpoints={
                "S3": ec2.GatewayVpcEndpointOptions(
                    service=ec2.GatewayVpcEndpointAwsService.S3
                ),
                "DynamoDB": ec2.GatewayVpcEndpointOptions(
                    service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
                ),
            },
        )

        # Add interface endpoints for additional AWS services
        self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
        )

        self.vpc.add_interface_endpoint(
            "ECREndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR
        )

        self.vpc.add_interface_endpoint(
            "ECRDockerEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER
        )

        self.vpc.add_interface_endpoint(
            "CloudWatchLogsEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
        )

        # 1. CONFIGURE SECURITY GROUPS
        # Create baseline security groups
        self.app_security_group = ec2.SecurityGroup(
            self,
            "ApplicationSecurityGroup",
            vpc=self.vpc,
            description="Security group for application servers",
            allow_all_outbound=True,
        )

        self.db_security_group = ec2.SecurityGroup(
            self,
            "DatabaseSecurityGroup",
            vpc=self.vpc,
            description="Security group for database instances",
            allow_all_outbound=False,
        )

        # Allow application tier to access database tier
        self.db_security_group.add_ingress_rule(
            peer=self.app_security_group,
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL access from application tier",
        )

        # Create a bastion host security group
        self.bastion_security_group = ec2.SecurityGroup(
            self,
            "BastionSecurityGroup",
            vpc=self.vpc,
            description="Security group for bastion hosts",
            allow_all_outbound=True,
        )

        # Allow SSH access to bastion from specific IP ranges (replace with your corporate IP)
        self.bastion_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(
                "0.0.0.0/0"
            ),  # IMPORTANT: Replace with your specific IP range in production!
            connection=ec2.Port.tcp(22),
            description="Allow SSH from specified IP ranges",
        )

        # Allow bastion to access application and database tiers
        self.app_security_group.add_ingress_rule(
            peer=self.bastion_security_group,
            connection=ec2.Port.tcp(22),
            description="Allow SSH from bastion hosts",
        )

        self.db_security_group.add_ingress_rule(
            peer=self.bastion_security_group,
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL access from bastion hosts",
        )

        # 3. ADD NETWORK ACLS FOR SECURITY
        # Create Network ACLs for each subnet type
        public_nacl = ec2.NetworkAcl(
            self,
            "PublicNetworkAcl",
            vpc=self.vpc,
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        )

        private_nacl = ec2.NetworkAcl(
            self,
            "PrivateNetworkAcl",
            vpc=self.vpc,
            subnet_selection=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )

        isolated_nacl = ec2.NetworkAcl(
            self,
            "IsolatedNetworkAcl",
            vpc=self.vpc,
            subnet_selection=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
        )

        # Configure rules for Public Network ACL
        # Inbound rules
        public_nacl.add_entry(
            "AllowAllInbound",
            rule_number=100,
            traffic=ec2.AclTraffic.all_traffic(),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
            cidr=ec2.AclCidr.any_ipv4(),
        )

        # Outbound rules
        public_nacl.add_entry(
            "AllowAllOutbound",
            rule_number=100,
            traffic=ec2.AclTraffic.all_traffic(),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW,
            cidr=ec2.AclCidr.any_ipv4(),
        )

        # Configure rules for Private Network ACL
        # Inbound rules - Allow specific traffic
        private_nacl.add_entry(
            "AllowHTTPInbound",
            rule_number=100,
            traffic=ec2.AclTraffic.tcp_port(80),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
            cidr=ec2.AclCidr.any_ipv4(),
        )

        private_nacl.add_entry(
            "AllowHTTPSInbound",
            rule_number=110,
            traffic=ec2.AclTraffic.tcp_port(443),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
            cidr=ec2.AclCidr.any_ipv4(),
        )

        private_nacl.add_entry(
            "AllowSSHInbound",
            rule_number=120,
            traffic=ec2.AclTraffic.tcp_port(22),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
            cidr=ec2.AclCidr.any_ipv4(),
        )

        # Allow return traffic (ephemeral ports)
        private_nacl.add_entry(
            "AllowReturnTraffic",
            rule_number=140,
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
            cidr=ec2.AclCidr.any_ipv4(),
        )

        # Outbound rules
        private_nacl.add_entry(
            "AllowAllOutbound",
            rule_number=100,
            traffic=ec2.AclTraffic.all_traffic(),
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW,
            cidr=ec2.AclCidr.any_ipv4(),
        )

        # Configure rules for Isolated Network ACL
        # Inbound rules - Strict control
        isolated_nacl.add_entry(
            "AllowDatabaseInbound",
            rule_number=100,
            traffic=ec2.AclTraffic.tcp_port(5432),  # PostgreSQL
            direction=ec2.TrafficDirection.INGRESS,
            rule_action=ec2.Action.ALLOW,
            cidr=ec2.AclCidr.ipv4("10.0.0.0/16"),  # Only from within VPC
        )

        # Outbound rules - Restricted
        isolated_nacl.add_entry(
            "AllowDatabaseOutbound",
            rule_number=100,
            traffic=ec2.AclTraffic.tcp_port_range(1024, 65535),  # Return traffic
            direction=ec2.TrafficDirection.EGRESS,
            rule_action=ec2.Action.ALLOW,
            cidr=ec2.AclCidr.ipv4("10.0.0.0/16"),  # Only within VPC
        )

        # Tag all subnets for easy identification
        for subnet in self.vpc.public_subnets:
            Tags.of(subnet).add("SubnetType", "Public")
            Tags.of(subnet).add(
                "Name", f"{self.stack_name}-Public-{subnet.availability_zone}"
            )

        for subnet in self.vpc.private_subnets:
            Tags.of(subnet).add("SubnetType", "Private")
            Tags.of(subnet).add(
                "Name", f"{self.stack_name}-Private-{subnet.availability_zone}"
            )

        for subnet in self.vpc.isolated_subnets:
            Tags.of(subnet).add("SubnetType", "Isolated")
            Tags.of(subnet).add(
                "Name", f"{self.stack_name}-Isolated-{subnet.availability_zone}"
            )

        # Output NAT Gateway information
        #        for i, nat_gateway_id in enumerate(self.vpc.nat_gateway_ids):
        #            CfnOutput(
        #                self,
        #                f"NatGateway{i+1}",
        #                value=nat_gateway_id,
        #                description=f"NAT Gateway {i+1} ID",
        #                export_name=f"{self.stack_name}-NatGateway{i+1}",
        #            )

        # Store VPC and subnet information in SSM Parameter Store for cross-stack reference
        ssm.StringParameter(
            self,
            "VpcId",
            parameter_name="/experimentation/vpc/id",
            string_value=self.vpc.vpc_id,
        )

        # Store comma-separated lists of subnet IDs in SSM for easy lookup
        ssm.StringParameter(
            self,
            "PublicSubnetIds",
            parameter_name="/experimentation/vpc/public-subnet-ids",
            string_value=",".join(
                [subnet.subnet_id for subnet in self.vpc.public_subnets]
            ),
        )

        ssm.StringParameter(
            self,
            "PrivateSubnetIds",
            parameter_name="/experimentation/vpc/private-subnet-ids",
            string_value=",".join(
                [subnet.subnet_id for subnet in self.vpc.private_subnets]
            ),
        )

        ssm.StringParameter(
            self,
            "IsolatedSubnetIds",
            parameter_name="/experimentation/vpc/isolated-subnet-ids",
            string_value=",".join(
                [subnet.subnet_id for subnet in self.vpc.isolated_subnets]
            ),
        )

        # Store security group IDs
        ssm.StringParameter(
            self,
            "AppSecurityGroupId",
            parameter_name="/experimentation/vpc/app-sg-id",
            string_value=self.app_security_group.security_group_id,
        )

        ssm.StringParameter(
            self,
            "DbSecurityGroupId",
            parameter_name="/experimentation/vpc/db-sg-id",
            string_value=self.db_security_group.security_group_id,
        )

        ssm.StringParameter(
            self,
            "BastionSecurityGroupId",
            parameter_name="/experimentation/vpc/bastion-sg-id",
            string_value=self.bastion_security_group.security_group_id,
        )

        # Create CloudFormation outputs for easy reference
        CfnOutput(
            self,
            "VpcIdOutput",
            value=self.vpc.vpc_id,
            description="VPC ID",
            export_name=f"{self.stack_name}-VpcId",
        )

        CfnOutput(
            self,
            "PublicSubnets",
            value=",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            description="Public Subnet IDs",
            export_name=f"{self.stack_name}-PublicSubnets",
        )

        CfnOutput(
            self,
            "PrivateSubnets",
            value=",".join([subnet.subnet_id for subnet in self.vpc.private_subnets]),
            description="Private Subnet IDs",
            export_name=f"{self.stack_name}-PrivateSubnets",
        )

        CfnOutput(
            self,
            "IsolatedSubnets",
            value=",".join([subnet.subnet_id for subnet in self.vpc.isolated_subnets]),
            description="Isolated Subnet IDs",
            export_name=f"{self.stack_name}-IsolatedSubnets",
        )

        CfnOutput(
            self,
            "AppSecurityGroup",
            value=self.app_security_group.security_group_id,
            description="Application Security Group ID",
            export_name=f"{self.stack_name}-AppSecurityGroup",
        )

        CfnOutput(
            self,
            "DbSecurityGroup",
            value=self.db_security_group.security_group_id,
            description="Database Security Group ID",
            export_name=f"{self.stack_name}-DbSecurityGroup",
        )

        CfnOutput(
            self,
            "BastionSecurityGroupOutput",
            value=self.bastion_security_group.security_group_id,
            description="Bastion Host Security Group ID",
            export_name=f"{self.stack_name}-BastionSecurityGroup",
        )
