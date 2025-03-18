from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    Tags,
    aws_ec2 as ec2,
    aws_elasticache as elasticache,
    aws_ssm as ssm,
)
from constructs import Construct


class ElastiCacheRedisStack(Stack):
    """
    CDK Stack for creating an ElastiCache Redis cluster.

    Features:
    - Environment-based scaling
    - Subnet group configuration
    - Security group restrictions
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        environment: str = "dev",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. CONFIGURE SUBNET GROUP
        # Create a subnet group for Redis using private subnets
        subnet_ids = vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
        ).subnet_ids

        redis_subnet_group = elasticache.CfnSubnetGroup(
            self,
            "RedisSubnetGroup",
            description=f"Subnet group for {construct_id} Redis cluster",
            subnet_ids=subnet_ids,
            cache_subnet_group_name=f"{construct_id}-redis-subnet-group".lower().replace(
                "_", "-"
            )[
                :40
            ],
        )

        # 2. CONFIGURE SECURITY GROUP
        # Create a security group for Redis
        redis_security_group = ec2.SecurityGroup(
            self,
            "RedisSecurityGroup",
            vpc=vpc,
            description=f"Security group for {construct_id} Redis cluster",
            allow_all_outbound=False,
        )

        # Allow access from VPC CIDR
        redis_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(6379),
            description="Allow Redis access from within VPC",
        )

        # 3. ENVIRONMENT-SPECIFIC CONFIGURATIONS
        # Different settings based on environment
        cluster_size = self._get_cluster_size_for_env(environment)
        instance_type = self._get_instance_type_for_env(environment)

        # 4. CREATE REDIS REPLICATION GROUP
        self.redis_cluster = elasticache.CfnReplicationGroup(
            self,
            "RedisCluster",
            replication_group_id=f"{construct_id}-redis".lower().replace("_", "-")[:40],
            replication_group_description=f"Redis cluster for {construct_id}",
            engine="redis",
            engine_version="7.0",
            port=6379,
            cache_node_type=instance_type,
            num_cache_clusters=cluster_size,
            automatic_failover_enabled=cluster_size > 1,
            auto_minor_version_upgrade=True,
            multi_az_enabled=cluster_size > 1,
            security_group_ids=[redis_security_group.security_group_id],
            cache_subnet_group_name=redis_subnet_group.ref,
            snapshot_retention_limit=self._get_snapshot_retention_for_env(environment),
            snapshot_window="02:00-03:00",  # UTC
            preferred_maintenance_window="sun:04:00-sun:05:00",  # UTC
            at_rest_encryption_enabled=True,
            transit_encryption_enabled=True,
        )

        # Add tags
        Tags.of(self.redis_cluster).add("Name", f"{construct_id}-redis")
        Tags.of(self.redis_cluster).add("Environment", environment)
        Tags.of(self.redis_cluster).add("Service", "experimentation-platform")

        # 5. STORE CONNECTION INFORMATION IN SSM
        ssm.StringParameter(
            self,
            "RedisEndpointParam",
            parameter_name=f"/experimentation/{environment}/redis/endpoint",
            string_value=self.redis_cluster.attr_primary_end_point_address,
            description=f"Redis primary endpoint for {construct_id}",
        )

        ssm.StringParameter(
            self,
            "RedisPortParam",
            parameter_name=f"/experimentation/{environment}/redis/port",
            string_value=self.redis_cluster.attr_primary_end_point_port,
            description=f"Redis port for {construct_id}",
        )

        if cluster_size > 1:
            ssm.StringParameter(
                self,
                "RedisReaderEndpointParam",
                parameter_name=f"/experimentation/{environment}/redis/reader-endpoint",
                string_value=self.redis_cluster.attr_reader_end_point_address,
                description=f"Redis reader endpoint for {construct_id}",
            )

        # 6. CREATE CLOUDFORMATION OUTPUTS
        CfnOutput(
            self,
            "RedisEndpoint",
            value=self.redis_cluster.attr_primary_end_point_address,
            description="Redis primary endpoint",
            export_name=f"{self.stack_name}-RedisEndpoint",
        )

        CfnOutput(
            self,
            "RedisPort",
            value=self.redis_cluster.attr_primary_end_point_port,
            description="Redis port",
            export_name=f"{self.stack_name}-RedisPort",
        )

        if cluster_size > 1:
            CfnOutput(
                self,
                "RedisReaderEndpoint",
                value=self.redis_cluster.attr_reader_end_point_address,
                description="Redis reader endpoint",
                export_name=f"{self.stack_name}-RedisReaderEndpoint",
            )

    def _get_instance_type_for_env(self, environment: str) -> str:
        """
        Get the appropriate Redis instance type based on environment.
        """
        if environment == "prod":
            return "cache.r6g.large"  # Memory optimized instances for production
        elif environment == "staging":
            return "cache.m6g.large"  # Balanced instance type for staging
        else:  # dev, test, etc.
            return "cache.t4g.medium"  # Burstable instances for dev/test

    def _get_cluster_size_for_env(self, environment: str) -> int:
        """
        Get the appropriate Redis cluster size based on environment.
        """
        if environment == "prod":
            return 3  # Primary + 2 replicas for high availability
        elif environment == "staging":
            return 2  # Primary + 1 replica for testing HA
        else:  # dev, test, etc.
            return 1  # Single node to save costs

    def _get_snapshot_retention_for_env(self, environment: str) -> int:
        """
        Get the appropriate Redis snapshot retention period based on environment.
        """
        if environment == "prod":
            return 7  # 7 days retention in production
        elif environment == "staging":
            return 3  # 3 days retention in staging
        else:  # dev, test, etc.
            return 1  # 1 day retention in dev/test
