from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_dynamodb as dynamodb,
    aws_elasticache as elasticache,
)
from constructs import Construct


class DatabaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a security group for the RDS cluster
        rds_security_group = ec2.SecurityGroup(
            self,
            "RDSSecurityGroup",
            vpc=vpc,
            description="Allow database access",
            allow_all_outbound=True,
        )

        # Create an Aurora PostgreSQL cluster
        self.aurora_cluster = rds.DatabaseCluster(
            self,
            "AuroraCluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_3
            ),
            credentials=rds.Credentials.from_generated_secret("postgres"),
            default_database_name="experimentation",
            instances=1,  # Use 2+ for production
            instance_props=rds.InstanceProps(
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ),
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MEDIUM
                ),
                security_groups=[rds_security_group],
            ),
            removal_policy=RemovalPolicy.SNAPSHOT,
            # Removed backup retention parameter completely
        )

        # Rest of the code remains the same...
        # Create DynamoDB tables, Redis, etc.

        # Create a DynamoDB table for assignments
        self.assignments_table = dynamodb.Table(
            self,
            "AssignmentsTable",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Add Global Secondary Indexes for assignments table
        self.assignments_table.add_global_secondary_index(
            index_name="user-experiment-index",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="experiment_id", type=dynamodb.AttributeType.STRING
            ),
        )

        # Create a DynamoDB table for events
        self.events_table = dynamodb.Table(
            self,
            "EventsTable",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Add GSIs for querying events
        self.events_table.add_global_secondary_index(
            index_name="user-event-index",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
        )

        self.events_table.add_global_secondary_index(
            index_name="experiment-event-index",
            partition_key=dynamodb.Attribute(
                name="experiment_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
        )

        # Create Redis for caching
        redis_subnet_group = elasticache.CfnSubnetGroup(
            self,
            "RedisSubnetGroup",
            description="Subnet group for Redis",
            subnet_ids=vpc.select_subnets(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ).subnet_ids,
        )

        redis_security_group = ec2.SecurityGroup(
            self,
            "RedisSecurityGroup",
            vpc=vpc,
            description="Allow Redis access",
            allow_all_outbound=True,
        )

        # Create Redis replication group
        self.redis = elasticache.CfnReplicationGroup(
            self,
            "Redis",
            replication_group_description="Redis cache for experimentation platform",
            engine="redis",
            engine_version="7.0",
            cache_node_type="cache.t3.medium",
            num_cache_clusters=1,  # Use 2+ for production
            automatic_failover_enabled=False,  # Enable for production
            auto_minor_version_upgrade=True,
            security_group_ids=[redis_security_group.security_group_id],
            cache_subnet_group_name=redis_subnet_group.ref,
            multi_az_enabled=False,  # Enable for production
        )
