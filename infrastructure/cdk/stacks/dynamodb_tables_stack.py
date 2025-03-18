from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    Tags,
    aws_dynamodb as dynamodb,
    aws_ssm as ssm,
    aws_iam as iam,
)
from constructs import Construct


class DynamoDBTablesStack(Stack):
    """
    Stack that creates DynamoDB tables for the experimentation platform.

    Tables created:
    - Assignments: Store user experiment variant assignments
    - Events: Store user interaction events for experiment analysis
    - Experiments: Store experiment configurations and metadata
    - FeatureFlags: Store feature flag configurations
    - Overrides: Store user-specific experiment or feature overrides
    """

    def __init__(
        self, scope: Construct, construct_id: str, environment="dev", **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Determine billing mode based on environment
        # Use on-demand for dev/staging for simplicity and cost predictability
        # Use provisioned with auto-scaling for production for cost optimization
        billing_mode = (
            dynamodb.BillingMode.PAY_PER_REQUEST
            if environment in ["dev", "staging"]
            else dynamodb.BillingMode.PROVISIONED
        )

        # Use different removal policies based on environment
        # DESTROY is ok for dev (save costs), but RETAIN for production (data safety)
        removal_policy = (
            RemovalPolicy.DESTROY if environment == "dev" else RemovalPolicy.RETAIN
        )

        # Create tables
        self.assignments_table = self._create_assignments_table(
            billing_mode, removal_policy, environment
        )
        self.events_table = self._create_events_table(
            billing_mode, removal_policy, environment
        )
        self.experiments_table = self._create_experiments_table(
            billing_mode, removal_policy, environment
        )
        self.feature_flags_table = self._create_feature_flags_table(
            billing_mode, removal_policy, environment
        )
        self.overrides_table = self._create_overrides_table(
            billing_mode, removal_policy, environment
        )

        # Store table names in SSM Parameter Store for reference by other services
        self._store_table_references(environment)

        # Export table names as CloudFormation outputs
        self._create_outputs()

    def _create_assignments_table(self, billing_mode, removal_policy, environment):
        """
        Create the Assignments table to track which users are assigned to which experiments/variants.

        Access patterns:
        - Get assignment by ID
        - Get assignments for a specific user
        - Get assignments for a specific experiment
        - Get assignment for a specific user and experiment (most common)
        """
        table = dynamodb.Table(
            self,
            "AssignmentsTable",
            table_name=f"experimentation-assignments-{environment}",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=billing_mode,
            removal_policy=removal_policy,
            point_in_time_recovery=True,
            # Enable TTL to automatically expire assignments when they're no longer needed
            time_to_live_attribute="ttl",
        )

        # Add GSI for user-experiment lookups (most common query pattern)
        table.add_global_secondary_index(
            index_name="user-experiment-index",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="experiment_id", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for finding all users in a specific experiment
        table.add_global_secondary_index(
            index_name="experiment-index",
            partition_key=dynamodb.Attribute(
                name="experiment_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="assigned_at", type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for finding all assignments for a specific user
        table.add_global_secondary_index(
            index_name="user-index",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="assigned_at", type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for finding assignments for a specific variation
        table.add_global_secondary_index(
            index_name="variation-index",
            partition_key=dynamodb.Attribute(
                name="variation", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="assigned_at", type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Configure auto-scaling if using provisioned capacity
        if billing_mode == dynamodb.BillingMode.PROVISIONED:
            self._configure_auto_scaling(table, min_capacity=5, max_capacity=500)

        # Add tags
        Tags.of(table).add("Service", "experimentation-platform")
        Tags.of(table).add("Environment", environment)

        return table

    def _create_events_table(self, billing_mode, removal_policy, environment):
        """
        Create the Events table to track user interaction events for experiment analysis.

        Access patterns:
        - Get event by ID and timestamp
        - Get events for a specific user
        - Get events for a specific experiment
        - Get events within a time range
        - Get events for a specific event type
        """
        table = dynamodb.Table(
            self,
            "EventsTable",
            table_name=f"experimentation-events-{environment}",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=billing_mode,
            removal_policy=removal_policy,
            point_in_time_recovery=True,
            # Enable TTL to automatically expire old events
            time_to_live_attribute="ttl",
            # Enable DynamoDB Streams for event processing
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )

        # Add GSI for user-based queries
        table.add_global_secondary_index(
            index_name="user-event-index",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for experiment-based queries
        table.add_global_secondary_index(
            index_name="experiment-event-index",
            partition_key=dynamodb.Attribute(
                name="experiment_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for event type queries
        table.add_global_secondary_index(
            index_name="event-type-index",
            partition_key=dynamodb.Attribute(
                name="event_type", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Configure auto-scaling if using provisioned capacity
        if billing_mode == dynamodb.BillingMode.PROVISIONED:
            self._configure_auto_scaling(table, min_capacity=10, max_capacity=1000)

        # Add tags
        Tags.of(table).add("Service", "experimentation-platform")
        Tags.of(table).add("Environment", environment)

        return table

    def _create_experiments_table(self, billing_mode, removal_policy, environment):
        """
        Create the Experiments table to store experiment configurations and metadata.

        Access patterns:
        - Get experiment by ID
        - Get experiments by status (active, completed, etc.)
        - Get experiments by owner
        - Get experiments by tag or category
        - Get experiments by creation date
        """
        table = dynamodb.Table(
            self,
            "ExperimentsTable",
            table_name=f"experimentation-experiments-{environment}",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=billing_mode,
            removal_policy=removal_policy,
            point_in_time_recovery=True,
        )

        # Add GSI for status-based queries
        table.add_global_secondary_index(
            index_name="status-index",
            partition_key=dynamodb.Attribute(
                name="status", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for owner-based queries
        table.add_global_secondary_index(
            index_name="owner-index",
            partition_key=dynamodb.Attribute(
                name="owner", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for tag/category-based queries
        table.add_global_secondary_index(
            index_name="tag-index",
            partition_key=dynamodb.Attribute(
                name="tag", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Configure auto-scaling if using provisioned capacity
        if billing_mode == dynamodb.BillingMode.PROVISIONED:
            self._configure_auto_scaling(table, min_capacity=5, max_capacity=100)

        # Add tags
        Tags.of(table).add("Service", "experimentation-platform")
        Tags.of(table).add("Environment", environment)

        return table

    def _create_feature_flags_table(self, billing_mode, removal_policy, environment):
        """
        Create the FeatureFlags table to store feature flag configurations.

        Access patterns:
        - Get feature flag by ID
        - Get feature flags by status (active, inactive)
        - Get feature flags by tag or category
        """
        table = dynamodb.Table(
            self,
            "FeatureFlagsTable",
            table_name=f"experimentation-feature-flags-{environment}",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=billing_mode,
            removal_policy=removal_policy,
            point_in_time_recovery=True,
        )

        # Add GSI for status-based queries
        table.add_global_secondary_index(
            index_name="status-index",
            partition_key=dynamodb.Attribute(
                name="status", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updated_at", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for tag/category-based queries
        table.add_global_secondary_index(
            index_name="tag-index",
            partition_key=dynamodb.Attribute(
                name="tag", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="updated_at", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Configure auto-scaling if using provisioned capacity
        if billing_mode == dynamodb.BillingMode.PROVISIONED:
            self._configure_auto_scaling(table, min_capacity=5, max_capacity=100)

        # Add tags
        Tags.of(table).add("Service", "experimentation-platform")
        Tags.of(table).add("Environment", environment)

        return table

    def _create_overrides_table(self, billing_mode, removal_policy, environment):
        """
        Create the Overrides table to store user-specific experiment or feature overrides.

        Access patterns:
        - Get override by ID
        - Get all overrides for a specific user
        - Get all overrides for a specific experiment or feature
        """
        table = dynamodb.Table(
            self,
            "OverridesTable",
            table_name=f"experimentation-overrides-{environment}",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=billing_mode,
            removal_policy=removal_policy,
            point_in_time_recovery=True,
            # Enable TTL to automatically expire overrides when they're no longer needed
            time_to_live_attribute="ttl",
        )

        # Add GSI for user-based queries
        table.add_global_secondary_index(
            index_name="user-index",
            partition_key=dynamodb.Attribute(
                name="user_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for target-based queries (experiment ID or feature flag ID)
        table.add_global_secondary_index(
            index_name="target-index",
            partition_key=dynamodb.Attribute(
                name="target_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for type-based queries (experiment or feature)
        table.add_global_secondary_index(
            index_name="type-index",
            partition_key=dynamodb.Attribute(
                name="type", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Configure auto-scaling if using provisioned capacity
        if billing_mode == dynamodb.BillingMode.PROVISIONED:
            self._configure_auto_scaling(table, min_capacity=5, max_capacity=100)

        # Add tags
        Tags.of(table).add("Service", "experimentation-platform")
        Tags.of(table).add("Environment", environment)

        return table

    def _configure_auto_scaling(self, table, min_capacity=5, max_capacity=100):
        """Configure auto-scaling for a provisioned capacity table"""
        # Auto-scale read capacity
        read_scaling = table.auto_scale_read_capacity(
            min_capacity=min_capacity,
            max_capacity=max_capacity,
        )

        # Scale up when 70% of provisioned capacity is used
        read_scaling.scale_on_utilization(
            target_utilization_percent=70,
            scale_in_cooldown=Duration.minutes(5),
            scale_out_cooldown=Duration.minutes(1),
        )

        # Auto-scale write capacity
        write_scaling = table.auto_scale_write_capacity(
            min_capacity=min_capacity,
            max_capacity=max_capacity,
        )

        # Scale up when 70% of provisioned capacity is used
        write_scaling.scale_on_utilization(
            target_utilization_percent=70,
            scale_in_cooldown=Duration.minutes(5),
            scale_out_cooldown=Duration.minutes(1),
        )

    def _store_table_references(self, environment):
        """Store table names in SSM Parameter Store for reference by other services"""
        # Assignments table
        ssm.StringParameter(
            self,
            "AssignmentsTableNameParam",
            parameter_name=f"/experimentation/{environment}/dynamodb/assignments-table",
            string_value=self.assignments_table.table_name,
            description="Assignments table name",
        )

        # Events table
        ssm.StringParameter(
            self,
            "EventsTableNameParam",
            parameter_name=f"/experimentation/{environment}/dynamodb/events-table",
            string_value=self.events_table.table_name,
            description="Events table name",
        )

        # Experiments table
        ssm.StringParameter(
            self,
            "ExperimentsTableNameParam",
            parameter_name=f"/experimentation/{environment}/dynamodb/experiments-table",
            string_value=self.experiments_table.table_name,
            description="Experiments table name",
        )

        # Feature flags table
        ssm.StringParameter(
            self,
            "FeatureFlagsTableNameParam",
            parameter_name=f"/experimentation/{environment}/dynamodb/feature-flags-table",
            string_value=self.feature_flags_table.table_name,
            description="Feature flags table name",
        )

        # Overrides table
        ssm.StringParameter(
            self,
            "OverridesTableNameParam",
            parameter_name=f"/experimentation/{environment}/dynamodb/overrides-table",
            string_value=self.overrides_table.table_name,
            description="Overrides table name",
        )

    def _create_outputs(self):
        """Create CloudFormation outputs for table references"""
        # Assignments table
        CfnOutput(
            self,
            "AssignmentsTableNameOutput",
            value=self.assignments_table.table_name,
            description="Assignments table name",
            export_name=f"{self.stack_name}-AssignmentsTableName",
        )

        # Events table
        CfnOutput(
            self,
            "EventsTableNameOutput",
            value=self.events_table.table_name,
            description="Events table name",
            export_name=f"{self.stack_name}-EventsTableName",
        )

        # Experiments table
        CfnOutput(
            self,
            "ExperimentsTableNameOutput",
            value=self.experiments_table.table_name,
            description="Experiments table name",
            export_name=f"{self.stack_name}-ExperimentsTableName",
        )

        # Feature flags table
        CfnOutput(
            self,
            "FeatureFlagsTableNameOutput",
            value=self.feature_flags_table.table_name,
            description="Feature flags table name",
            export_name=f"{self.stack_name}-FeatureFlagsTableName",
        )

        # Overrides table
        CfnOutput(
            self,
            "OverridesTableNameOutput",
            value=self.overrides_table.table_name,
            description="Overrides table name",
            export_name=f"{self.stack_name}-OverridesTableName",
        )
