import pytest
from unittest.mock import Mock, patch
import boto3
from botocore.exceptions import ClientError
from backend.app.utils.aws_client import AWSClient

class TestAWSClient:
    @pytest.fixture
    def aws_client(self):
        return AWSClient()

    @patch('boto3.client')
    def test_init_cloudwatch_logs_success(self, mock_boto3_client, aws_client):
        # Test successful initialization
        mock_logs_client = Mock()
        mock_boto3_client.return_value = mock_logs_client

        result = aws_client.init_cloudwatch_logs()

        assert result is True
        assert aws_client.logs_client == mock_logs_client
        mock_boto3_client.assert_called_once_with('logs', region_name='us-west-2')

    @patch('boto3.client')
    def test_init_cloudwatch_logs_failure(self, mock_boto3_client, aws_client):
        # Test initialization failure
        mock_boto3_client.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'DescribeLogGroups'
        )

        result = aws_client.init_cloudwatch_logs()

        assert result is False
        assert aws_client.logs_client is None

    @patch('boto3.client')
    def test_init_cloudwatch_metrics_success(self, mock_boto3_client, aws_client):
        # Test successful initialization
        mock_metrics_client = Mock()
        mock_boto3_client.return_value = mock_metrics_client

        result = aws_client.init_cloudwatch_metrics()

        assert result is True
        assert aws_client.metrics_client == mock_metrics_client
        mock_boto3_client.assert_called_once_with('cloudwatch', region_name='us-west-2')

    @patch('boto3.client')
    def test_init_cloudwatch_metrics_failure(self, mock_boto3_client, aws_client):
        # Test initialization failure
        mock_boto3_client.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'PutMetricData'
        )

        result = aws_client.init_cloudwatch_metrics()

        assert result is False
        assert aws_client.metrics_client is None

    @patch('backend.app.utils.aws_client.AWSClient.init_cloudwatch_metrics')
    def test_send_metric_success(self, mock_init_metrics, aws_client):
        # Test successful metric sending
        mock_metrics_client = Mock()
        aws_client.metrics_client = mock_metrics_client

        result = aws_client.send_metric(
            namespace='TestNamespace',
            metric_name='TestMetric',
            value=42.0,
            unit='Count'
        )

        assert result is True
        mock_metrics_client.put_metric_data.assert_called_once()

    def test_send_metric_no_client(self, aws_client):
        # Test metric sending without initialized client
        aws_client.metrics_client = None

        result = aws_client.send_metric(
            namespace='TestNamespace',
            metric_name='TestMetric',
            value=42.0,
            unit='Count'
        )

        assert result is False

    @patch('backend.app.utils.aws_client.AWSClient.init_cloudwatch_metrics')
    def test_send_metric_error(self, mock_init_metrics, aws_client):
        # Test metric sending with error
        mock_metrics_client = Mock()
        mock_metrics_client.put_metric_data.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            'PutMetricData'
        )
        aws_client.metrics_client = mock_metrics_client

        result = aws_client.send_metric(
            namespace='TestNamespace',
            metric_name='TestMetric',
            value=42.0,
            unit='Count'
        )

        assert result is False

    def test_send_metric_invalid_unit(self, aws_client):
        # Test metric sending with invalid unit
        mock_metrics_client = Mock()
        aws_client.metrics_client = mock_metrics_client

        result = aws_client.send_metric(
            namespace='TestNamespace',
            metric_name='TestMetric',
            value=42.0,
            unit='InvalidUnit'
        )

        assert result is False
        mock_metrics_client.put_metric_data.assert_not_called()
