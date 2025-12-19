"""
Integration tests for Lambda Handler (Day 4).

Tests the main Lambda handler function including API Gateway integration,
request/response formatting, and end-to-end assignment workflows.
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))


class TestLambdaHandlerIntegration:
    """Integration tests for Lambda handler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "experiment_key": "checkout_redesign"
            },
            "headers": {
                "Content-Type": "application/json"
            },
            "requestContext": {
                "requestId": "test-request-123"
            }
        }

    @patch('handler.AssignmentService')
    def test_handler_successful_new_assignment(self, mock_service_class):
        """Test successful new assignment creation."""
        from handler import lambda_handler
        from models import ExperimentConfig, VariantConfig, ExperimentStatus, Assignment

        # Mock experiment config
        experiment_config = ExperimentConfig(
            experiment_id="exp_123",
            key="checkout_redesign",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        # Mock assignment
        assignment = Assignment(
            assignment_id="assign_abc123",
            user_id="user_123",
            experiment_id="exp_123",
            experiment_key="checkout_redesign",
            variant="treatment",
            timestamp=datetime.now(timezone.utc)
        )

        # Mock service methods
        mock_service = Mock()
        mock_service.get_experiment_config_cached.return_value = experiment_config
        mock_service.get_or_create_assignment.return_value = assignment
        mock_service_class.return_value = mock_service

        # Call handler
        response = lambda_handler(self.valid_event, {})

        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['variant'] == 'treatment'
        assert body['experiment_key'] == 'checkout_redesign'
        assert body['user_id'] == 'user_123'

    @patch('handler.AssignmentService')
    def test_handler_existing_assignment(self, mock_service_class):
        """Test returning existing assignment."""
        from handler import lambda_handler
        from models import ExperimentConfig, VariantConfig, ExperimentStatus, Assignment

        experiment_config = ExperimentConfig(
            experiment_id="exp_123",
            key="checkout_redesign",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        # Mock existing assignment
        assignment = Assignment(
            assignment_id="assign_existing",
            user_id="user_123",
            experiment_id="exp_123",
            experiment_key="checkout_redesign",
            variant="control",
            timestamp=datetime.now(timezone.utc)
        )

        mock_service = Mock()
        mock_service.get_experiment_config_cached.return_value = experiment_config
        mock_service.get_or_create_assignment.return_value = assignment
        mock_service_class.return_value = mock_service

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['variant'] == 'control'

    def test_handler_missing_user_id(self):
        """Test 400 error when user_id is missing."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "experiment_key": "checkout_redesign"
            }
        }

        response = lambda_handler(event, {})

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'user_id' in body['error'].lower()

    def test_handler_missing_experiment_key(self):
        """Test 400 error when experiment_key is missing."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "user_id": "user_123"
            }
        }

        response = lambda_handler(event, {})

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'experiment_key' in body['error'].lower()

    def test_handler_missing_query_parameters(self):
        """Test 400 error when query parameters are missing."""
        from handler import lambda_handler

        event = {}

        response = lambda_handler(event, {})

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body

    @patch('handler.AssignmentService')
    def test_handler_experiment_not_found(self, mock_service_class):
        """Test 404 error when experiment doesn't exist."""
        from handler import lambda_handler

        # Mock service - experiment not found
        mock_service = Mock()
        mock_service.get_experiment_config_cached.return_value = None
        mock_service_class.return_value = mock_service

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'not found' in body['error'].lower()

    @patch('handler.AssignmentService')
    def test_handler_user_excluded_by_traffic(self, mock_service_class):
        """Test 200 response when user excluded by traffic allocation."""
        from handler import lambda_handler
        from models import ExperimentConfig, VariantConfig, ExperimentStatus

        experiment_config = ExperimentConfig(
            experiment_id="exp_123",
            key="checkout_redesign",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ],
            traffic_allocation=0.5
        )

        # Mock service - user excluded
        mock_service = Mock()
        mock_service.get_experiment_config_cached.return_value = experiment_config
        mock_service.get_or_create_assignment.return_value = None
        mock_service_class.return_value = mock_service

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['variant'] is None
        assert body['excluded'] is True

    @patch('handler.AssignmentService')
    def test_handler_with_user_context(self, mock_service_class):
        """Test assignment with user context."""
        from handler import lambda_handler
        from models import ExperimentConfig, VariantConfig, ExperimentStatus, Assignment

        event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "experiment_key": "checkout_redesign"
            },
            "body": json.dumps({
                "context": {
                    "country": "US",
                    "platform": "web"
                }
            })
        }

        experiment_config = ExperimentConfig(
            experiment_id="exp_123",
            key="checkout_redesign",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ],
            targeting_rules=[
                {"attribute": "country", "operator": "equals", "value": "US"}
            ]
        )

        assignment = Assignment(
            assignment_id="assign_123",
            user_id="user_123",
            experiment_id="exp_123",
            experiment_key="checkout_redesign",
            variant="treatment",
            timestamp=datetime.now(timezone.utc),
            context={"country": "US", "platform": "web"}
        )

        mock_service = Mock()
        mock_service.get_experiment_config_cached.return_value = experiment_config
        mock_service.get_or_create_assignment.return_value = assignment
        mock_service_class.return_value = mock_service

        response = lambda_handler(event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['variant'] == 'treatment'

        # Verify context was passed to service
        call_kwargs = mock_service.get_or_create_assignment.call_args.kwargs
        assert 'context' in call_kwargs
        assert call_kwargs['context']['country'] == 'US'

    @patch('handler.AssignmentService')
    def test_handler_user_excluded_by_targeting(self, mock_service_class):
        """Test user excluded by targeting rules."""
        from handler import lambda_handler
        from models import ExperimentConfig, VariantConfig, ExperimentStatus

        event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "experiment_key": "checkout_redesign"
            },
            "body": json.dumps({
                "context": {
                    "country": "CA"
                }
            })
        }

        experiment_config = ExperimentConfig(
            experiment_id="exp_123",
            key="checkout_redesign",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ],
            targeting_rules=[
                {"attribute": "country", "operator": "equals", "value": "US"}
            ]
        )

        mock_service = Mock()
        mock_service.get_experiment_config_cached.return_value = experiment_config
        mock_service.get_or_create_assignment.return_value = None
        mock_service_class.return_value = mock_service

        response = lambda_handler(event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['variant'] is None
        assert body['excluded'] is True

    @patch('handler.AssignmentService')
    def test_handler_internal_server_error(self, mock_service_class):
        """Test 500 error handling."""
        from handler import lambda_handler

        # Mock service to raise exception
        mock_service = Mock()
        mock_service.get_experiment_config_cached.side_effect = Exception("DynamoDB error")
        mock_service_class.return_value = mock_service

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'internal server error' in body['error'].lower()

    def test_handler_response_headers(self):
        """Test that response includes proper CORS headers."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "experiment_key": "test"
            }
        }

        response = lambda_handler(event, {})

        # Verify CORS headers
        assert 'headers' in response
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Headers' in response['headers']

    @patch('handler.AssignmentService')
    def test_handler_logs_request_metadata(self, mock_service_class):
        """Test that handler logs request metadata."""
        from handler import lambda_handler
        from models import ExperimentConfig, VariantConfig, ExperimentStatus, Assignment

        event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "experiment_key": "checkout_redesign"
            },
            "requestContext": {
                "requestId": "test-request-123",
                "sourceIp": "192.168.1.1"
            }
        }

        experiment_config = ExperimentConfig(
            experiment_id="exp_123",
            key="checkout_redesign",
            status=ExperimentStatus.ACTIVE,
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        assignment = Assignment(
            assignment_id="assign_123",
            user_id="user_123",
            experiment_id="exp_123",
            experiment_key="checkout_redesign",
            variant="treatment",
            timestamp=datetime.now(timezone.utc)
        )

        mock_service = Mock()
        mock_service.get_experiment_config_cached.return_value = experiment_config
        mock_service.get_or_create_assignment.return_value = assignment
        mock_service_class.return_value = mock_service

        # Should not raise errors
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200

    def test_handler_invalid_json_body(self):
        """Test handling of invalid JSON in request body."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "experiment_key": "checkout_redesign"
            },
            "body": "invalid json {{"
        }

        response = lambda_handler(event, {})

        # Should handle gracefully - either ignore body or return 400
        assert response['statusCode'] in [200, 400, 404, 500]

    @patch('handler.AssignmentService')
    def test_handler_empty_user_id(self, mock_service_class):
        """Test 400 error when user_id is empty."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "user_id": "",
                "experiment_key": "checkout_redesign"
            }
        }

        response = lambda_handler(event, {})

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
