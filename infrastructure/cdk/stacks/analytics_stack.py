from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_kinesis as kinesis,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_s3 as s3,
    aws_kinesisfirehose as firehose,
    aws_opensearchservice as opensearch,
    aws_lambda_event_sources as lambda_event_sources,
    aws_glue as glue,
)
from constructs import Construct


class AnalyticsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Generate a unique identifier to avoid resource name conflicts
        # This will add a suffix to resource names
        env_name = self.node.try_get_context("env") or "dev"
        unique_suffix = f"-{env_name}-{self.account}-{self.region}"

        # Create or import a Kinesis Data Stream for event collection
        try:
            # Try to create a new stream with a unique name
            self.events_stream = kinesis.Stream(
                self,
                "EventsStream",
                stream_name=f"experimentation-events{unique_suffix}",
                shard_count=1,  # Increase for production
                retention_period=Duration.hours(24),
            )
        except Exception as e:
            # If it fails, import the existing stream
            print(f"Using existing Kinesis stream: {e}")
            self.events_stream = kinesis.Stream.from_stream_arn(
                self,
                "ExistingEventsStream",
                stream_arn=f"arn:aws:kinesis:{self.region}:{self.account}:stream/experimentation-events",
            )

        # Create or import an S3 bucket for the data lake
        try:
            # Try to create a new bucket with a unique name
            bucket_name = f"experimentation-data-lake{unique_suffix}"
            self.data_lake_bucket = s3.Bucket(
                self,
                "DataLakeBucket",
                bucket_name=bucket_name,
                removal_policy=RemovalPolicy.RETAIN,
                versioned=True,
            )
        except Exception as e:
            # If it fails, import the existing bucket
            print(f"Using existing S3 bucket: {e}")
            existing_bucket_name = (
                f"experimentation-data-lake-{self.account}-{self.region}"
            )
            self.data_lake_bucket = s3.Bucket.from_bucket_name(
                self, "ExistingDataLakeBucket", bucket_name=existing_bucket_name
            )

        # Create a Firehose delivery stream to S3
        firehose_role = iam.Role(
            self,
            "FirehoseRole",
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
        )

        # Add explicit permissions for Kinesis
        firehose_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "kinesis:DescribeStream",
                    "kinesis:GetShardIterator",
                    "kinesis:GetRecords",
                    "kinesis:ListShards",
                ],
                resources=[self.events_stream.stream_arn],
            )
        )

        # Add S3 permissions
        firehose_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:AbortMultipartUpload",
                    "s3:GetBucketLocation",
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:ListBucketMultipartUploads",
                    "s3:PutObject",
                ],
                resources=[
                    self.data_lake_bucket.bucket_arn,
                    f"{self.data_lake_bucket.bucket_arn}/*",
                ],
            )
        )

        # Add CloudWatch permissions for logging
        firehose_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:PutLogEvents",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                ],
                resources=["arn:aws:logs:*:*:*"],
            )
        )

        # Create a unique delivery stream name
        delivery_stream_name = f"experimentation-events-to-s3{unique_suffix}"

        delivery_stream = firehose.CfnDeliveryStream(
            self,
            "EventsDeliveryStream",
            delivery_stream_name=delivery_stream_name,
            delivery_stream_type="KinesisStreamAsSource",
            kinesis_stream_source_configuration=firehose.CfnDeliveryStream.KinesisStreamSourceConfigurationProperty(
                kinesis_stream_arn=self.events_stream.stream_arn,
                role_arn=firehose_role.role_arn,
            ),
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=self.data_lake_bucket.bucket_arn,
                buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
                    interval_in_seconds=60, size_in_m_bs=5
                ),
                compression_format="GZIP",
                prefix="raw/events/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
                error_output_prefix="errors/!{firehose:error-output-type}/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
                role_arn=firehose_role.role_arn,
            ),
        )

        # Create a domain name with a unique suffix
        # domain_name = f"experimentation{unique_suffix}".lower().replace("-", "")
        # Update the domain name generation to ensure it's within the 3-28 char limit
        domain_name = f"exp-{env_name}-{self.region.split('-')[2]}"
        if len(domain_name) > 28:
            # If still too long, use a simpler name with a hash
            import hashlib

            hash_suffix = hashlib.md5(
                f"{self.account}-{self.region}".encode()
            ).hexdigest()[:6]
            domain_name = f"exp-{env_name}-{hash_suffix}"

        # Create an OpenSearch domain for analytics (with simplified configuration)
        opensearch_domain = opensearch.Domain(
            self,
            "ExperimentationDomain",
            domain_name=domain_name,
            version=opensearch.EngineVersion.OPENSEARCH_1_3,
            capacity=opensearch.CapacityConfig(
                data_nodes=1, data_node_instance_type="t3.small.search"
            ),
            ebs=opensearch.EbsOptions(
                enabled=True, volume_size=10, volume_type=ec2.EbsDeviceVolumeType.GP2
            ),
            access_policies=[
                iam.PolicyStatement(
                    actions=["es:*"],
                    effect=iam.Effect.ALLOW,
                    principals=[iam.AnyPrincipal()],
                    resources=["*"],
                )
            ],
            encryption_at_rest=opensearch.EncryptionAtRestOptions(enabled=True),
            node_to_node_encryption=True,
        )

        # Create a Lambda function to process events and send to OpenSearch
        lambda_role = iam.Role(
            self,
            "AnalyticsLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # Grant permissions to the Lambda function
        self.events_stream.grant_read(lambda_role)
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["es:ESHttpPost", "es:ESHttpPut"],
                resources=[opensearch_domain.domain_arn + "/*"],
            )
        )

        # Analytics Lambda function with placeholder code
        analytics_lambda = lambda_.Function(
            self,
            "AnalyticsLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_inline(
                """
                def handler(event, context):
                    print("Received event:", event)
                    return {
                        'statusCode': 200,
                        'body': 'Event processed'
                    }
                """
            ),
            handler="index.handler",
            environment={
                "OPENSEARCH_DOMAIN": opensearch_domain.domain_endpoint,
                "ENVIRONMENT": "dev",
            },
            timeout=Duration.seconds(30),
            memory_size=256,
            role=lambda_role,
        )

        # Add Kinesis as an event source for the Lambda function
        analytics_lambda.add_event_source(
            lambda_event_sources.KinesisEventSource(
                self.events_stream,
                starting_position=lambda_.StartingPosition.LATEST,
                batch_size=100,
                max_batching_window=Duration.seconds(10),
            )
        )

        # Create a Glue Database and Crawler for analyzing data in S3
        glue_role = iam.Role(
            self,
            "GlueRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSGlueServiceRole"
                )
            ],
        )

        self.data_lake_bucket.grant_read(glue_role)

        # Create a Glue Database
        glue_database = glue.CfnDatabase(
            self,
            "ExperimentationDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="experimentation_db",
                description="Database for experimentation platform data",
            ),
        )

        # Create a Glue Crawler
        glue_crawler = glue.CfnCrawler(
            self,
            "EventsCrawler",
            name="experimentation-events-crawler",
            role=glue_role.role_arn,
            database_name="experimentation_db",
            schedule=glue.CfnCrawler.ScheduleProperty(
                schedule_expression="cron(0 * * * ? *)"  # Run hourly
            ),
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets=[
                    glue.CfnCrawler.S3TargetProperty(
                        path=f"s3://{self.data_lake_bucket.bucket_name}/raw/events/"
                    )
                ]
            ),
            schema_change_policy=glue.CfnCrawler.SchemaChangePolicyProperty(
                update_behavior="UPDATE_IN_DATABASE", delete_behavior="LOG"
            ),
        )
