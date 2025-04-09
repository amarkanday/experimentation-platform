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
import random
import string


class AnalyticsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Generate random ID for resource names
        random_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        env_name = self.node.try_get_context("env") or "dev"

        # Create a Kinesis Data Stream with randomized name
        stream_name = f"exp-events-{random_id}"
        self.events_stream = kinesis.Stream(
            self,
            "EventsStream",
            stream_name=stream_name,
            shard_count=1,  # Increase for production
            retention_period=Duration.hours(24),
        )

        # Create an S3 bucket with randomized name
        bucket_name = f"exp-data-{random_id}-{self.region}"
        self.data_lake_bucket = s3.Bucket(
            self,
            "DataLakeBucket",
            bucket_name=bucket_name,
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True,
        )

        # Create a policy document with Kinesis permissions
        kinesis_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "kinesis:DescribeStream",
                        "kinesis:GetShardIterator",
                        "kinesis:GetRecords",
                        "kinesis:ListShards",
                    ],
                    resources=[self.events_stream.stream_arn],
                )
            ]
        )

        # Create Firehose role with inline policy
        firehose_role = iam.Role(
            self,
            "FirehoseRole",
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
            inline_policies={"KinesisPolicy": kinesis_policy},
        )

        # Create inline policy for S3 access
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

        # Create inline policy for CloudWatch Logs access
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
        delivery_stream_name = f"exp-delivery-{random_id}"

        # Create the delivery stream
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
        delivery_stream.node.add_dependency(self.events_stream)

        # Create a domain name with randomized suffix (ensuring it's under 28 chars)
        domain_name = f"exp-{random_id[:8]}"

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
                    principals=[iam.AccountRootPrincipal()],
                    resources=["*"],
                )
            ],
            encryption_at_rest=opensearch.EncryptionAtRestOptions(enabled=True),
            node_to_node_encryption=True,
        )

        # Rest of implementation unchanged...
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
                    return {
                        'statusCode': 200,
                        'body': 'Event processed'
                    }
                """
            ),
            handler="index.handler",
            environment={
                "OPENSEARCH_DOMAIN": opensearch_domain.domain_endpoint,
                "ENVIRONMENT": env_name,
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

        # Create a Glue Database with randomized name
        db_name = f"exp_{random_id[:8]}_db"

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
                name=db_name, description="Database for experimentation platform data"
            ),
        )

        # Create a Glue Crawler with randomized name
        crawler_name = f"exp-crawler-{random_id[:8]}"

        glue_crawler = glue.CfnCrawler(
            self,
            "EventsCrawler",
            name=crawler_name,
            role=glue_role.role_arn,
            database_name=db_name,
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
