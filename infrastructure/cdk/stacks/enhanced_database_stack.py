from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    Tags,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
    aws_ssm as ssm,
)
from constructs import Construct


class EnhancedDatabaseStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, vpc, environment="dev", **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Use existing security group from VPC stack if available, otherwise create one
        if hasattr(vpc, "db_security_group"):
            rds_security_group = vpc.db_security_group
        else:
            rds_security_group = ec2.SecurityGroup(
                self,
                "RDSSecurityGroup",
                vpc=vpc,
                description="Security group for Aurora PostgreSQL",
                allow_all_outbound=False,
            )

            # Add explicit ingress rule for PostgreSQL port from application security group
            if hasattr(vpc, "app_security_group"):
                rds_security_group.add_ingress_rule(
                    peer=vpc.app_security_group,
                    connection=ec2.Port.tcp(5432),
                    description="Allow PostgreSQL access from application tier",
                )

            # Add bastion access if available
            if hasattr(vpc, "bastion_security_group"):
                rds_security_group.add_ingress_rule(
                    peer=vpc.bastion_security_group,
                    connection=ec2.Port.tcp(5432),
                    description="Allow PostgreSQL access from bastion hosts",
                )

        # 1. CREATE KMS KEY FOR ENCRYPTION
        db_encryption_key = kms.Key(
            self,
            "DatabaseEncryptionKey",
            alias=f"alias/{construct_id}-postgres-key",
            description=f"KMS key for {construct_id} PostgreSQL encryption",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Tag the key for easier identification
        Tags.of(db_encryption_key).add("Name", f"{construct_id}-postgres-key")
        Tags.of(db_encryption_key).add("Environment", environment)

        # 2. CREATE CUSTOM PARAMETER GROUPS
        # 2.1 DB Cluster Parameter Group
        db_cluster_parameter_group = rds.ParameterGroup(
            self,
            "ClusterParameterGroup",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_3
            ),
            description=f"Parameter group for {construct_id} Aurora PostgreSQL cluster",
            parameters={
                "shared_preload_libraries": "pg_stat_statements",
                "timezone": "UTC",
                "rds.force_ssl": "1",  # Force SSL connections
            },
        )

        # 2.2 DB Instance Parameter Group
        db_instance_parameter_group = rds.ParameterGroup(
            self,
            "InstanceParameterGroup",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_3
            ),
            description=f"Parameter group for {construct_id} Aurora PostgreSQL instances",
            parameters={
                # Performance tuning
                "shared_buffers": self._get_shared_buffers_for_env(environment),
                "work_mem": self._get_work_mem_for_env(environment),
                "maintenance_work_mem": "64MB",
                "effective_cache_size": self._get_effective_cache_for_env(environment),
                "random_page_cost": "1.1",  # Optimized for SSD storage
                # Logging settings
                "log_statement": "ddl",  # Log DDL statements
                "log_min_duration_statement": "1000",  # Log slow queries (> 1sec)
                "log_connections": "1",
                "log_disconnections": "1",
                "log_lock_waits": "1",
                "log_temp_files": "0",
                # Query optimization
                "autovacuum": "1",
                "autovacuum_vacuum_scale_factor": "0.1",
                "autovacuum_analyze_scale_factor": "0.05",
            },
        )

        # 3. CREATE SUBNET GROUP
        db_subnet_group = rds.SubnetGroup(
            self,
            "DBSubnetGroup",
            description=f"Subnet group for {construct_id} Aurora PostgreSQL",
            vpc=vpc,
            # For production, use isolated subnets for better security
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=(
                    ec2.SubnetType.PRIVATE_ISOLATED
                    if environment == "prod"
                    else ec2.SubnetType.PRIVATE_WITH_EGRESS
                )
            ),
        )

        # 4. CREATE DATABASE CREDENTIALS IN SECRETS MANAGER
        # Generate a descriptive name for the secret
        secret_name = f"{construct_id}-aurora-credentials"

        db_credentials = secretsmanager.Secret(
            self,
            "DBCredentials",
            secret_name=secret_name,
            description=f"Credentials for {construct_id} Aurora PostgreSQL",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "postgres"}',
                generate_string_key="password",
                exclude_characters='"@/\\',  # Exclude problematic characters
                exclude_punctuation=False,  # Include some punctuation for stronger passwords
                password_length=32,
            ),
        )

        # Store the secret ARN in SSM for easy retrieval
        ssm.StringParameter(
            self,
            "DBSecretArnParam",
            parameter_name=f"/experimentation/{environment}/database/aurora-secret-arn",
            string_value=db_credentials.secret_arn,
            description=f"Secret ARN for {construct_id} Aurora PostgreSQL credentials",
        )

        # 5. DETERMINE ENVIRONMENT-SPECIFIC CONFIGURATIONS
        # Scale according to environment
        instance_count = 2 if environment in ["prod", "staging"] else 1

        instance_type = (
            ec2.InstanceType.of(ec2.InstanceClass.MEMORY5, ec2.InstanceSize.LARGE)
            if environment == "prod"
            else ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MEDIUM
            )
        )

        # 6. CREATE AURORA POSTGRESQL CLUSTER WITH MINIMAL SETTINGS
        # Only using the most basic, universally supported parameters
        self.aurora_cluster = rds.DatabaseCluster(
            self,
            "AuroraCluster",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_3
            ),
            credentials=rds.Credentials.from_secret(db_credentials),
            default_database_name="experimentation",
            instances=instance_count,
            instance_props=rds.InstanceProps(
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=(
                        ec2.SubnetType.PRIVATE_ISOLATED
                        if environment == "prod"
                        else ec2.SubnetType.PRIVATE_WITH_EGRESS
                    )
                ),
                instance_type=instance_type,
                security_groups=[rds_security_group],
                parameter_group=db_instance_parameter_group,
            ),
            parameter_group=db_cluster_parameter_group,
            subnet_group=db_subnet_group,
            storage_encrypted=True,
            storage_encryption_key=db_encryption_key,
            removal_policy=RemovalPolicy.SNAPSHOT,
        )

        # Add tags to the database cluster for easier identification and management
        Tags.of(self.aurora_cluster).add("Name", f"{construct_id}-aurora-cluster")
        Tags.of(self.aurora_cluster).add("Environment", environment)
        Tags.of(self.aurora_cluster).add("Service", "experimentation-platform")

        # 7. STORE CONNECTION INFORMATION IN SSM FOR EASY ACCESS
        ssm.StringParameter(
            self,
            "DBHostParam",
            parameter_name=f"/experimentation/{environment}/database/aurora-host",
            string_value=self.aurora_cluster.cluster_endpoint.hostname,
            description=f"Host for {construct_id} Aurora PostgreSQL",
        )

        ssm.StringParameter(
            self,
            "DBPortParam",
            parameter_name=f"/experimentation/{environment}/database/aurora-port",
            string_value=str(self.aurora_cluster.cluster_endpoint.port),
            description=f"Port for {construct_id} Aurora PostgreSQL",
        )

        ssm.StringParameter(
            self,
            "DBNameParam",
            parameter_name=f"/experimentation/{environment}/database/aurora-name",
            string_value="experimentation",
            description=f"Database name for {construct_id} Aurora PostgreSQL",
        )

        # 8. CREATE CLOUDFORMATION OUTPUTS
        CfnOutput(
            self,
            "ClusterEndpoint",
            value=self.aurora_cluster.cluster_endpoint.socket_address,
            description="Aurora PostgreSQL cluster endpoint",
            export_name=f"{self.stack_name}-ClusterEndpoint",
        )

        CfnOutput(
            self,
            "ClusterReadEndpoint",
            value=self.aurora_cluster.cluster_read_endpoint.socket_address,
            description="Aurora PostgreSQL read endpoint",
            export_name=f"{self.stack_name}-ReadEndpoint",
        )

        CfnOutput(
            self,
            "SecretArn",
            value=db_credentials.secret_arn,
            description="Secret ARN for database credentials",
            export_name=f"{self.stack_name}-SecretArn",
        )

    # HELPER METHODS
    def _get_shared_buffers_for_env(self, environment):
        """Return appropriate shared_buffers setting based on environment"""
        if environment == "prod":
            return "4GB"  # For larger instances in production
        elif environment == "staging":
            return "2GB"  # For medium instances in staging
        else:
            return "256MB"  # For smaller instances in dev

    def _get_work_mem_for_env(self, environment):
        """Return appropriate work_mem setting based on environment"""
        if environment == "prod":
            return "16MB"
        elif environment == "staging":
            return "8MB"
        else:
            return "4MB"

    def _get_effective_cache_for_env(self, environment):
        """Return appropriate effective_cache_size setting based on environment"""
        if environment == "prod":
            return "12GB"
        elif environment == "staging":
            return "6GB"
        else:
            return "768MB"
