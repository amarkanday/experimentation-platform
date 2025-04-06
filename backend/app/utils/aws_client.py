import os
import logging
import boto3
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class AWSClient:
    """
    Utility class for initializing and managing AWS clients.
    Provides standardized initialization with proper error handling.
    """

    def __init__(self):
        self.logs_client = None
        self.metrics_client = None

    def init_cloudwatch_logs(self) -> bool:
        """
        Initialize and store a boto3 CloudWatch Logs client.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get region from environment variable or use default
            region = os.environ.get('AWS_REGION', 'us-west-2')

            # Get profile from environment variable
            profile = os.environ.get('AWS_PROFILE')

            # Create session with profile if specified
            if profile:
                session = boto3.Session(profile_name=profile, region_name=region)
                self.logs_client = session.client('logs')
            else:
                # Use default credentials from environment or instance profile
                self.logs_client = boto3.client('logs', region_name=region)

            logger.debug(f"Successfully initialized CloudWatch Logs client in region {region}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize CloudWatch Logs client: {str(e)}")
            self.logs_client = None
            return False

    def init_cloudwatch_metrics(self) -> bool:
        """
        Initialize and store a boto3 CloudWatch Metrics client.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get region from environment variable or use default
            region = os.environ.get('AWS_REGION', 'us-west-2')

            # Get profile from environment variable
            profile = os.environ.get('AWS_PROFILE')

            # Create session with profile if specified
            if profile:
                session = boto3.Session(profile_name=profile, region_name=region)
                self.metrics_client = session.client('cloudwatch')
            else:
                # Use default credentials from environment or instance profile
                self.metrics_client = boto3.client('cloudwatch', region_name=region)

            logger.debug(f"Successfully initialized CloudWatch Metrics client in region {region}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize CloudWatch Metrics client: {str(e)}")
            self.metrics_client = None
            return False

    def send_metric(
        self,
        namespace: str,
        metric_name: str,
        value: float,
        unit: str = 'None',
        dimensions: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send a metric to CloudWatch Metrics.

        Args:
            namespace: CloudWatch namespace
            metric_name: Name of the metric
            value: Value to send
            unit: Unit of measurement
            dimensions: Optional dimensions for the metric

        Returns:
            bool: True if successful, False otherwise
        """
        if self.metrics_client is None:
            logger.error("Cannot put metric data: CloudWatch client is None")
            return False

        # Validate unit
        valid_units = [
            'Seconds', 'Microseconds', 'Milliseconds', 'Bytes', 'Kilobytes',
            'Megabytes', 'Gigabytes', 'Terabytes', 'Bits', 'Kilobits',
            'Megabits', 'Gigabits', 'Terabits', 'Percent', 'Count',
            'Bytes/Second', 'Kilobytes/Second', 'Megabytes/Second',
            'Gigabytes/Second', 'Terabytes/Second', 'Bits/Second',
            'Kilobits/Second', 'Megabits/Second', 'Gigabits/Second',
            'Terabits/Second', 'Count/Second', 'None'
        ]
        if unit not in valid_units:
            logger.error(f"Invalid unit: {unit}")
            return False

        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }

            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': key, 'Value': value}
                    for key, value in dimensions.items()
                ]

            response = self.metrics_client.put_metric_data(
                Namespace=namespace,
                MetricData=[metric_data]
            )

            logger.debug(f"Successfully put metric data: {namespace}/{metric_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to put metric data: {str(e)}")
            return False
