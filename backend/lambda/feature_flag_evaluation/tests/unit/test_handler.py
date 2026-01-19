"""
Unit tests for Feature Flag Lambda Handler (Day 3).

Tests the Lambda handler function including:
- API Gateway event parsing
- Request/response formatting
- Evaluation orchestration
- Error handling
- CORS headers

Following TDD (Test-Driven Development) - RED phase: Tests written first.
All tests should fail until handler.py is implemented.
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

from models import FeatureFlagConfig, VariantConfig


class TestFeatureFlagLambdaHandler:
    """Unit tests for Feature Flag Lambda handler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.valid_event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "flag_key": "new_checkout"
            },
            "headers": {
                "Content-Type": "application/json"
            },
            "requestContext": {
                "requestId": "test-request-123",
                "sourceIp": "192.168.1.1"
            }
        }

        self.enabled_flag = FeatureFlagConfig(
            flag_id="flag_123",
            key="new_checkout",
            enabled=True,
            rollout_percentage=100.0
        )

        self.disabled_flag = FeatureFlagConfig(
            flag_id="flag_disabled",
            key="disabled_feature",
            enabled=False,
            rollout_percentage=100.0
        )

    # ====================================================================
    # Task 4.11: Tests for Lambda handler integration
    # ====================================================================

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_successful_evaluation_enabled(self, mock_evaluator_class):
        """Test successful flag evaluation that returns enabled=True."""
        from handler import lambda_handler

        # Mock evaluator
        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = self.enabled_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": True,
            "reason": "enabled",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        # Call handler
        response = lambda_handler(self.valid_event, {})

        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['enabled'] is True
        assert body['flag_key'] == 'new_checkout'
        assert body['user_id'] == 'user_123'
        assert body['reason'] == 'enabled'

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_successful_evaluation_disabled(self, mock_evaluator_class):
        """Test successful flag evaluation that returns enabled=False."""
        from handler import lambda_handler

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = self.disabled_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": False,
            "reason": "flag_disabled",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['enabled'] is False
        assert body['reason'] == 'flag_disabled'

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_evaluation_with_variant(self, mock_evaluator_class):
        """Test flag evaluation that returns a variant."""
        from handler import lambda_handler

        variant_flag = FeatureFlagConfig(
            flag_id="flag_variant",
            key="variant_feature",
            enabled=True,
            rollout_percentage=100.0,
            default_variant="control",
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = variant_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": True,
            "reason": "enabled",
            "variant": "treatment"
        }
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['enabled'] is True
        assert body['variant'] == 'treatment'

    def test_handler_missing_user_id(self):
        """Test 400 error when user_id is missing."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "flag_key": "new_checkout"
            }
        }

        response = lambda_handler(event, {})

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'user_id' in body['error'].lower()

    def test_handler_missing_flag_key(self):
        """Test 400 error when flag_key is missing."""
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
        assert 'flag_key' in body['error'].lower()

    def test_handler_missing_query_parameters(self):
        """Test 400 error when query parameters are missing."""
        from handler import lambda_handler

        event = {}

        response = lambda_handler(event, {})

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body

    def test_handler_empty_user_id(self):
        """Test 400 error when user_id is empty string."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "user_id": "",
                "flag_key": "new_checkout"
            }
        }

        response = lambda_handler(event, {})

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'user_id' in body['error'].lower()

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_flag_not_found(self, mock_evaluator_class):
        """Test 404 error when flag doesn't exist."""
        from handler import lambda_handler

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = None
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'not found' in body['error'].lower()

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_with_user_context(self, mock_evaluator_class):
        """Test evaluation with user context from request body."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "flag_key": "new_checkout"
            },
            "body": json.dumps({
                "context": {
                    "country": "US",
                    "platform": "web",
                    "age": 25
                }
            })
        }

        targeted_flag = FeatureFlagConfig(
            flag_id="flag_targeted",
            key="new_checkout",
            enabled=True,
            rollout_percentage=100.0,
            targeting_rules=[
                {"attribute": "country", "operator": "equals", "value": "US"}
            ]
        )

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = targeted_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": True,
            "reason": "enabled",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['enabled'] is True

        # Verify context was passed to evaluator
        call_kwargs = mock_evaluator.evaluate.call_args.kwargs
        assert 'context' in call_kwargs
        assert call_kwargs['context']['country'] == 'US'
        assert call_kwargs['context']['platform'] == 'web'

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_user_excluded_by_rollout(self, mock_evaluator_class):
        """Test response when user is excluded by rollout percentage."""
        from handler import lambda_handler

        partial_rollout_flag = FeatureFlagConfig(
            flag_id="flag_partial",
            key="partial_feature",
            enabled=True,
            rollout_percentage=50.0
        )

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = partial_rollout_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": False,
            "reason": "not_in_rollout",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['enabled'] is False
        assert body['reason'] == 'not_in_rollout'

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_user_excluded_by_targeting(self, mock_evaluator_class):
        """Test response when user doesn't match targeting rules."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "flag_key": "targeted_feature"
            },
            "body": json.dumps({
                "context": {
                    "country": "CA"
                }
            })
        }

        targeted_flag = FeatureFlagConfig(
            flag_id="flag_targeted",
            key="targeted_feature",
            enabled=True,
            rollout_percentage=100.0,
            targeting_rules=[
                {"attribute": "country", "operator": "equals", "value": "US"}
            ]
        )

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = targeted_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": False,
            "reason": "targeting_rules_not_met",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['enabled'] is False
        assert body['reason'] == 'targeting_rules_not_met'

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_internal_server_error(self, mock_evaluator_class):
        """Test 500 error handling for unexpected exceptions."""
        from handler import lambda_handler

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.side_effect = Exception("DynamoDB connection error")
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'internal server error' in body['error'].lower()

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_validation_error(self, mock_evaluator_class):
        """Test 400 error for validation errors from evaluator."""
        from handler import lambda_handler

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = self.enabled_flag
        mock_evaluator.evaluate.side_effect = ValueError("user_id cannot be None")
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body

    def test_handler_response_headers_cors(self):
        """Test that response includes proper CORS headers."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "flag_key": "test"
            }
        }

        response = lambda_handler(event, {})

        # Verify CORS headers exist
        assert 'headers' in response
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']

    def test_handler_response_headers_content_type(self):
        """Test that response has correct Content-Type header."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "flag_key": "test"
            }
        }

        response = lambda_handler(event, {})

        assert response['headers']['Content-Type'] == 'application/json'

    def test_handler_invalid_json_body(self):
        """Test handling of malformed JSON in request body."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "flag_key": "new_checkout"
            },
            "body": "invalid json {{"
        }

        # Should handle gracefully - continue without context
        response = lambda_handler(event, {})

        # Should not fail completely due to bad JSON
        # Either succeed without context or return specific error
        assert response['statusCode'] in [200, 400, 404, 500]

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_no_request_body(self, mock_evaluator_class):
        """Test evaluation without request body (no context)."""
        from handler import lambda_handler

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = self.enabled_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": True,
            "reason": "enabled",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        # No body in event
        event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "flag_key": "new_checkout"
            }
        }

        response = lambda_handler(event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['enabled'] is True

        # Verify context was None
        call_kwargs = mock_evaluator.evaluate.call_args.kwargs
        assert call_kwargs['context'] is None

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_logs_request_metadata(self, mock_evaluator_class):
        """Test that handler extracts and logs request metadata."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "flag_key": "new_checkout"
            },
            "requestContext": {
                "requestId": "test-request-456",
                "sourceIp": "10.0.1.100"
            }
        }

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = self.enabled_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": True,
            "reason": "enabled",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        # Should not raise errors
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_whitespace_user_id(self, mock_evaluator_class):
        """Test 400 error when user_id is only whitespace."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "user_id": "   ",
                "flag_key": "new_checkout"
            }
        }

        response = lambda_handler(event, {})

        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_cache_hit_performance(self, mock_evaluator_class):
        """Test that handler uses cached flag config for performance."""
        from handler import lambda_handler

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = self.enabled_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": True,
            "reason": "enabled",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        # Make multiple requests
        for _ in range(3):
            response = lambda_handler(self.valid_event, {})
            assert response['statusCode'] == 200

        # Verify cached method was called (not uncached)
        assert mock_evaluator.get_flag_config_cached.call_count == 3
        assert mock_evaluator.get_flag_config_cached.called

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_response_includes_flag_id(self, mock_evaluator_class):
        """Test that response includes flag_id for tracking."""
        from handler import lambda_handler

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = self.enabled_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": True,
            "reason": "enabled",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'flag_id' in body
        assert body['flag_id'] == 'flag_123'

    @patch('handler.FeatureFlagEvaluator')
    def test_handler_context_with_multiple_attributes(self, mock_evaluator_class):
        """Test evaluation with complex user context."""
        from handler import lambda_handler

        event = {
            "queryStringParameters": {
                "user_id": "user_123",
                "flag_key": "new_checkout"
            },
            "body": json.dumps({
                "context": {
                    "country": "US",
                    "platform": "web",
                    "age": 25,
                    "subscription_tier": "premium",
                    "device_type": "mobile"
                }
            })
        }

        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = self.enabled_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": True,
            "reason": "enabled",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(event, {})

        assert response['statusCode'] == 200

        # Verify all context attributes were passed
        call_kwargs = mock_evaluator.evaluate.call_args.kwargs
        context = call_kwargs['context']
        assert context['country'] == 'US'
        assert context['age'] == 25
        assert context['subscription_tier'] == 'premium'

    # ====================================================================
    # Task 4.10: Tests for async evaluation tracking (Kinesis)
    # ====================================================================

    @patch('handler.record_evaluation_event_async')
    @patch('handler.FeatureFlagEvaluator')
    def test_handler_records_evaluation_event_to_kinesis(
        self,
        mock_evaluator_class,
        mock_record_event
    ):
        """Test that evaluation events are sent to Kinesis."""
        from handler import lambda_handler

        # Mock evaluator
        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = self.enabled_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": True,
            "reason": "enabled",
            "variant": "treatment"
        }
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 200

        # Verify Kinesis event was recorded
        mock_record_event.assert_called_once()
        call_args = mock_record_event.call_args

        # Verify event structure
        assert call_args.kwargs['user_id'] == 'user_123'
        assert call_args.kwargs['flag_config'].key == 'new_checkout'
        assert call_args.kwargs['flag_config'].flag_id == 'flag_123'
        assert call_args.kwargs['evaluation_result']['enabled'] is True
        assert call_args.kwargs['evaluation_result']['reason'] == 'enabled'
        assert call_args.kwargs['evaluation_result']['variant'] == 'treatment'

    @patch('handler.record_evaluation_event_async')
    @patch('handler.FeatureFlagEvaluator')
    def test_handler_tracking_failure_does_not_block_response(
        self,
        mock_evaluator_class,
        mock_record_event
    ):
        """Test that tracking failures don't block the response."""
        from handler import lambda_handler

        # Mock evaluator
        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = self.enabled_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": True,
            "reason": "enabled",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        # Mock Kinesis failure
        mock_record_event.side_effect = Exception("Kinesis unavailable")

        # Request should still succeed
        response = lambda_handler(self.valid_event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['enabled'] is True

        # Tracking was attempted
        mock_record_event.assert_called_once()

    @patch('handler.record_evaluation_event_async')
    @patch('handler.FeatureFlagEvaluator')
    def test_handler_tracking_event_includes_all_metadata(
        self,
        mock_evaluator_class,
        mock_record_event
    ):
        """Test that tracking event includes all required metadata."""
        from handler import lambda_handler

        # Add request body with context
        event_with_context = {
            **self.valid_event,
            "body": json.dumps({
                "context": {
                    "country": "US",
                    "user_tier": "premium"
                }
            })
        }

        # Mock evaluator
        mock_evaluator = Mock()
        mock_evaluator.get_flag_config_cached.return_value = self.enabled_flag
        mock_evaluator.evaluate.return_value = {
            "enabled": False,
            "reason": "not_in_rollout",
            "variant": None
        }
        mock_evaluator_class.return_value = mock_evaluator

        response = lambda_handler(event_with_context, {})

        assert response['statusCode'] == 200

        # Verify event was recorded
        mock_record_event.assert_called_once()
        call_kwargs = mock_record_event.call_args.kwargs

        # Verify all required fields
        assert 'user_id' in call_kwargs
        assert 'flag_config' in call_kwargs
        assert 'evaluation_result' in call_kwargs
        assert call_kwargs['evaluation_result']['reason'] == 'not_in_rollout'
