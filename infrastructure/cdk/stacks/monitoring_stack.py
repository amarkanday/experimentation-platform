from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class MonitoringStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an SNS topic for alerts
        self.alerts_topic = sns.Topic(
            self,
            "AlertsTopic",
            display_name="Experimentation Platform Alerts",
            topic_name="experimentation-alerts",
        )

        # Add an email subscription (replace with actual email)
        self.alerts_topic.add_subscription(
            sns_subscriptions.EmailSubscription("alerts@example.com")
        )

        # Create a CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(
            self, "ExperimentationDashboard", dashboard_name="experimentation-platform"
        )

        # Add API Gateway metrics
        api_widget = cloudwatch.GraphWidget(
            title="API Gateway",
            left=[
                cloudwatch.Metric(
                    namespace="AWS/ApiGateway",
                    metric_name="Count",
                    dimensions_map={"ApiName": "ExperimentationApi"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/ApiGateway",
                    metric_name="Latency",
                    dimensions_map={"ApiName": "ExperimentationApi"},
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
            ],
        )

        # Add Lambda metrics
        lambda_widget = cloudwatch.GraphWidget(
            title="Lambda Functions",
            left=[
                cloudwatch.Metric(
                    namespace="AWS/Lambda",
                    metric_name="Invocations",
                    dimensions_map={"FunctionName": "AssignmentLambda"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/Lambda",
                    metric_name="Invocations",
                    dimensions_map={"FunctionName": "EventProcessorLambda"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/Lambda",
                    metric_name="Invocations",
                    dimensions_map={"FunctionName": "FeatureFlagLambda"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
            ],
            right=[
                cloudwatch.Metric(
                    namespace="AWS/Lambda",
                    metric_name="Duration",
                    dimensions_map={"FunctionName": "AssignmentLambda"},
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/Lambda",
                    metric_name="Duration",
                    dimensions_map={"FunctionName": "EventProcessorLambda"},
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/Lambda",
                    metric_name="Duration",
                    dimensions_map={"FunctionName": "FeatureFlagLambda"},
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
            ],
        )

        # Add DynamoDB metrics
        dynamodb_widget = cloudwatch.GraphWidget(
            title="DynamoDB",
            left=[
                cloudwatch.Metric(
                    namespace="AWS/DynamoDB",
                    metric_name="ConsumedReadCapacityUnits",
                    dimensions_map={"TableName": "AssignmentsTable"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/DynamoDB",
                    metric_name="ConsumedWriteCapacityUnits",
                    dimensions_map={"TableName": "AssignmentsTable"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/DynamoDB",
                    metric_name="ConsumedReadCapacityUnits",
                    dimensions_map={"TableName": "EventsTable"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/DynamoDB",
                    metric_name="ConsumedWriteCapacityUnits",
                    dimensions_map={"TableName": "EventsTable"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
            ],
        )

        # Add Kinesis metrics
        kinesis_widget = cloudwatch.GraphWidget(
            title="Kinesis",
            left=[
                cloudwatch.Metric(
                    namespace="AWS/Kinesis",
                    metric_name="IncomingRecords",
                    dimensions_map={"StreamName": "experimentation-events"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/Kinesis",
                    metric_name="IncomingBytes",
                    dimensions_map={"StreamName": "experimentation-events"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
            ],
            right=[
                cloudwatch.Metric(
                    namespace="AWS/Kinesis",
                    metric_name="GetRecords.IteratorAgeMilliseconds",
                    dimensions_map={"StreamName": "experimentation-events"},
                    statistic="Maximum",
                    period=Duration.minutes(1),
                )
            ],
        )

        # Add RDS metrics
        rds_widget = cloudwatch.GraphWidget(
            title="RDS Aurora",
            left=[
                cloudwatch.Metric(
                    namespace="AWS/RDS",
                    metric_name="CPUUtilization",
                    dimensions_map={"DBClusterIdentifier": "AuroraCluster"},
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/RDS",
                    metric_name="DatabaseConnections",
                    dimensions_map={"DBClusterIdentifier": "AuroraCluster"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
            ],
            right=[
                cloudwatch.Metric(
                    namespace="AWS/RDS",
                    metric_name="FreeableMemory",
                    dimensions_map={"DBClusterIdentifier": "AuroraCluster"},
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/RDS",
                    metric_name="ReadLatency",
                    dimensions_map={"DBClusterIdentifier": "AuroraCluster"},
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/RDS",
                    metric_name="WriteLatency",
                    dimensions_map={"DBClusterIdentifier": "AuroraCluster"},
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
            ],
        )

        # Add Redis metrics
        redis_widget = cloudwatch.GraphWidget(
            title="ElastiCache Redis",
            left=[
                cloudwatch.Metric(
                    namespace="AWS/ElastiCache",
                    metric_name="CPUUtilization",
                    dimensions_map={"CacheClusterId": "Redis"},
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/ElastiCache",
                    metric_name="CurrConnections",
                    dimensions_map={"CacheClusterId": "Redis"},
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
            ],
            right=[
                cloudwatch.Metric(
                    namespace="AWS/ElastiCache",
                    metric_name="CacheHits",
                    dimensions_map={"CacheClusterId": "Redis"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="AWS/ElastiCache",
                    metric_name="CacheMisses",
                    dimensions_map={"CacheClusterId": "Redis"},
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
            ],
        )

        # Add all widgets to the dashboard
        dashboard.add_widgets(
            api_widget,
            lambda_widget,
            dynamodb_widget,
            kinesis_widget,
            rds_widget,
            redis_widget,
        )

        # Create CloudWatch Alarms

        # API Gateway 5XX errors alarm
        api_5xx_alarm = cloudwatch.Alarm(
            self,
            "Api5xxAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/ApiGateway",
                metric_name="5XXError",
                dimensions_map={"ApiName": "ExperimentationApi"},
                statistic="Sum",
                period=Duration.minutes(1),
            ),
            evaluation_periods=1,
            threshold=5,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="API Gateway is returning 5XX errors",
            alarm_name="ExperimentationApi5xxErrors",
        )

        api_5xx_alarm.add_alarm_action(cloudwatch_actions.SnsAction(self.alerts_topic))

        # Lambda error alarm
        lambda_error_alarm = cloudwatch.Alarm(
            self,
            "LambdaErrorAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Errors",
                dimensions_map={"FunctionName": "AssignmentLambda"},
                statistic="Sum",
                period=Duration.minutes(5),
            ),
            evaluation_periods=1,
            threshold=5,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Lambda function is experiencing errors",
            alarm_name="AssignmentLambdaErrors",
        )

        lambda_error_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alerts_topic)
        )

        # DynamoDB throttling alarm
        dynamodb_throttling_alarm = cloudwatch.Alarm(
            self,
            "DynamoDBThrottlingAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/DynamoDB",
                metric_name="ThrottledRequests",
                dimensions_map={"TableName": "AssignmentsTable"},
                statistic="Sum",
                period=Duration.minutes(5),
            ),
            evaluation_periods=1,
            threshold=10,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="DynamoDB table is experiencing throttling",
            alarm_name="AssignmentsTableThrottling",
        )

        dynamodb_throttling_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alerts_topic)
        )

        # Aurora high CPU alarm
        aurora_cpu_alarm = cloudwatch.Alarm(
            self,
            "AuroraCpuAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/RDS",
                metric_name="CPUUtilization",
                dimensions_map={"DBClusterIdentifier": "AuroraCluster"},
                statistic="Average",
                period=Duration.minutes(5),
            ),
            evaluation_periods=3,
            threshold=80,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Aurora cluster CPU is high",
            alarm_name="AuroraHighCPU",
        )

        aurora_cpu_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alerts_topic)
        )

        # Kinesis iterator age alarm (potential processing backlog)
        iterator_age_alarm = cloudwatch.Alarm(
            self,
            "KinesisIteratorAgeAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/Kinesis",
                metric_name="GetRecords.IteratorAgeMilliseconds",
                dimensions_map={"StreamName": "experimentation-events"},
                statistic="Maximum",
                period=Duration.minutes(5),
            ),
            evaluation_periods=3,
            threshold=300000,  # 5 minutes
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Kinesis stream processing is falling behind",
            alarm_name="KinesisProcessingDelay",
        )

        iterator_age_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alerts_topic)
        )

        # Lambda duration alarm
        lambda_duration_alarm = cloudwatch.Alarm(
            self,
            "LambdaDurationAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Duration",
                dimensions_map={"FunctionName": "AssignmentLambda"},
                statistic="p95",
                period=Duration.minutes(5),
            ),
            evaluation_periods=3,
            threshold=5000,  # 5 seconds
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Lambda function execution time is high",
            alarm_name="AssignmentLambdaDuration",
        )

        lambda_duration_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alerts_topic)
        )

        # Redis CPU alarm
        redis_cpu_alarm = cloudwatch.Alarm(
            self,
            "RedisCpuAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/ElastiCache",
                metric_name="CPUUtilization",
                dimensions_map={"CacheClusterId": "Redis"},
                statistic="Average",
                period=Duration.minutes(5),
            ),
            evaluation_periods=3,
            threshold=80,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="Redis CPU utilization is high",
            alarm_name="RedisHighCPU",
        )

        redis_cpu_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alerts_topic)
        )

        # Create a Log Group for application logs
        application_logs = logs.LogGroup(
            self,
            "ApplicationLogs",
            log_group_name="/experimentation/application",
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create a metric filter for error logs
        error_metric = application_logs.add_metric_filter(
            "ErrorMetric",
            filter_pattern=logs.FilterPattern.all_terms("ERROR"),
            metric_name="ErrorCount",
            metric_namespace="ExperimentationPlatform",
            default_value=0,
        )

        # Create an alarm for error logs
        error_logs_alarm = cloudwatch.Alarm(
            self,
            "ErrorLogsAlarm",
            metric=error_metric.metric(statistic="Sum", period=Duration.minutes(5)),
            evaluation_periods=1,
            threshold=10,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            alarm_description="High number of error logs detected",
            alarm_name="ApplicationErrorLogs",
        )

        error_logs_alarm.add_alarm_action(
            cloudwatch_actions.SnsAction(self.alerts_topic)
        )

        # Create a dashboard for application-specific metrics
        app_dashboard = cloudwatch.Dashboard(
            self,
            "ApplicationDashboard",
            dashboard_name="experimentation-application-metrics",
        )

        # Add application-specific widgets (these would be custom metrics published by your application)
        app_widget = cloudwatch.GraphWidget(
            title="Experiment Metrics",
            left=[
                cloudwatch.Metric(
                    namespace="ExperimentationPlatform",
                    metric_name="ActiveExperiments",
                    statistic="Maximum",
                    period=Duration.minutes(5),
                ),
                cloudwatch.Metric(
                    namespace="ExperimentationPlatform",
                    metric_name="ExperimentCreationRate",
                    statistic="Sum",
                    period=Duration.hours(1),
                ),
            ],
            right=[
                cloudwatch.Metric(
                    namespace="ExperimentationPlatform",
                    metric_name="FeatureFlagEvaluations",
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="ExperimentationPlatform",
                    metric_name="ExperimentAssignments",
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
            ],
        )

        event_widget = cloudwatch.GraphWidget(
            title="Event Processing",
            left=[
                cloudwatch.Metric(
                    namespace="ExperimentationPlatform",
                    metric_name="EventsProcessed",
                    statistic="Sum",
                    period=Duration.minutes(1),
                ),
                cloudwatch.Metric(
                    namespace="ExperimentationPlatform",
                    metric_name="EventProcessingLatency",
                    statistic="Average",
                    period=Duration.minutes(1),
                ),
            ],
            right=[
                cloudwatch.Metric(
                    namespace="ExperimentationPlatform",
                    metric_name="EventProcessingErrors",
                    statistic="Sum",
                    period=Duration.minutes(5),
                )
            ],
        )

        # Add widgets to application dashboard
        app_dashboard.add_widgets(app_widget, event_widget)
