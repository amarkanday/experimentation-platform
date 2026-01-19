"""
Integration tests for Feature Flag Lambda (Day 4).

Tests the complete end-to-end flow from API Gateway event to response,
including evaluation logic and caching behavior.

Following TDD (Test-Driven Development) - Integration phase.
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from models import FeatureFlagConfig, VariantConfig


class TestFeatureFlagEndToEnd:
    """End-to-end integration tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enabled_flag = FeatureFlagConfig(
            flag_id="flag_e2e_123",
            key="e2e_feature",
            enabled=True,
            rollout_percentage=100.0
        )

        self.partial_rollout_flag = FeatureFlagConfig(
            flag_id="flag_partial",
            key="partial_feature",
            enabled=True,
            rollout_percentage=50.0
        )

        self.targeted_flag = FeatureFlagConfig(
            flag_id="flag_targeted",
            key="targeted_feature",
            enabled=True,
            rollout_percentage=100.0,
            targeting_rules=[
                {"attribute": "country", "operator": "equals", "value": "US"}
            ]
        )

        self.variant_flag = FeatureFlagConfig(
            flag_id="flag_variants",
            key="variant_feature",
            enabled=True,
            rollout_percentage=100.0,
            default_variant="control",
            variants=[
                VariantConfig(key="control", allocation=0.5),
                VariantConfig(key="treatment", allocation=0.5)
            ]
        )

    @patch('evaluator.get_dynamodb_resource')
    def test_end_to_end_enabled_flag(self, mock_get_resource):
        """Test complete flow for enabled flag evaluation."""
        from handler import lambda_handler

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'flag_e2e_123',
                'key': 'e2e_feature',
                'enabled': True,
                'rollout_percentage': 100.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        # Create API Gateway event
        event = {
            "queryStringParameters": {
                "user_id": "user_e2e_123",
                "flag_key": "e2e_feature"
            },
            "requestContext": {
                "requestId": "e2e-test-123"
            }
        }

        # Call handler
        response = lambda_handler(event, {})

        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['enabled'] is True
        assert body['flag_key'] == 'e2e_feature'
        assert body['user_id'] == 'user_e2e_123'
        assert body['flag_id'] == 'flag_e2e_123'

    @patch('evaluator.get_dynamodb_resource')
    def test_end_to_end_with_targeting_rules(self, mock_get_resource):
        """Test complete flow with targeting rules evaluation."""
        from handler import lambda_handler

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'flag_targeted',
                'key': 'targeted_feature',
                'enabled': True,
                'rollout_percentage': 100.0,
                'targeting_rules': [
                    {"attribute": "country", "operator": "equals", "value": "US"}
                ]
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        # Event with US user (should match)
        event_us = {
            "queryStringParameters": {
                "user_id": "user_us",
                "flag_key": "targeted_feature"
            },
            "body": json.dumps({
                "context": {"country": "US"}
            })
        }

        response_us = lambda_handler(event_us, {})
        assert response_us['statusCode'] == 200
        body_us = json.loads(response_us['body'])
        assert body_us['enabled'] is True

        # Event with CA user (should not match)
        event_ca = {
            "queryStringParameters": {
                "user_id": "user_ca",
                "flag_key": "targeted_feature"
            },
            "body": json.dumps({
                "context": {"country": "CA"}
            })
        }

        response_ca = lambda_handler(event_ca, {})
        assert response_ca['statusCode'] == 200
        body_ca = json.loads(response_ca['body'])
        assert body_ca['enabled'] is False
        assert body_ca['reason'] == 'targeting_rules_not_met'

    @patch('evaluator.get_dynamodb_resource')
    def test_end_to_end_with_variants(self, mock_get_resource):
        """Test complete flow with variant assignment."""
        from handler import lambda_handler

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'flag_variants',
                'key': 'variant_feature',
                'enabled': True,
                'rollout_percentage': 100.0,
                'default_variant': 'control',
                'variants': [
                    {'key': 'control', 'allocation': 0.5},
                    {'key': 'treatment', 'allocation': 0.5}
                ]
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        event = {
            "queryStringParameters": {
                "user_id": "user_variant_123",
                "flag_key": "variant_feature"
            }
        }

        response = lambda_handler(event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['enabled'] is True
        assert body['variant'] in ['control', 'treatment']

        # Same user should get same variant
        response2 = lambda_handler(event, {})
        body2 = json.loads(response2['body'])
        assert body2['variant'] == body['variant']

    @patch('evaluator.get_dynamodb_resource')
    def test_end_to_end_partial_rollout_distribution(self, mock_get_resource):
        """Test that partial rollout creates correct distribution."""
        from handler import lambda_handler

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'flag_partial',
                'key': 'partial_feature',
                'enabled': True,
                'rollout_percentage': 50.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        # Test 100 different users
        enabled_count = 0
        for i in range(100):
            event = {
                "queryStringParameters": {
                    "user_id": f"user_{i}",
                    "flag_key": "partial_feature"
                }
            }

            response = lambda_handler(event, {})
            body = json.loads(response['body'])

            if body['enabled']:
                enabled_count += 1

        # Should be approximately 50% (±10% tolerance for small sample)
        assert 40 <= enabled_count <= 60, \
            f"Expected ~50 enabled, got {enabled_count}"

    @patch('evaluator.get_dynamodb_resource')
    def test_end_to_end_caching_behavior(self, mock_get_resource):
        """Test that caching reduces DynamoDB calls."""
        from handler import lambda_handler

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'flag_cached',
                'key': 'cached_feature',
                'enabled': True,
                'rollout_percentage': 100.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        event = {
            "queryStringParameters": {
                "user_id": "user_cache_test",
                "flag_key": "cached_feature"
            }
        }

        # First request - should hit DynamoDB
        response1 = lambda_handler(event, {})
        assert response1['statusCode'] == 200
        assert mock_table.get_item.call_count == 1

        # Second request - should use cache
        response2 = lambda_handler(event, {})
        assert response2['statusCode'] == 200
        # Should still be 1 (cached)
        assert mock_table.get_item.call_count == 1

        # Third request - should use cache
        response3 = lambda_handler(event, {})
        assert response3['statusCode'] == 200
        assert mock_table.get_item.call_count == 1

    @patch('evaluator.get_dynamodb_resource')
    def test_end_to_end_consistency_across_calls(self, mock_get_resource):
        """Test that same user gets consistent results across multiple calls."""
        from handler import lambda_handler

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'flag_consistent',
                'key': 'consistent_feature',
                'enabled': True,
                'rollout_percentage': 50.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        event = {
            "queryStringParameters": {
                "user_id": "user_consistent",
                "flag_key": "consistent_feature"
            }
        }

        # Make 10 calls
        results = []
        for _ in range(10):
            response = lambda_handler(event, {})
            body = json.loads(response['body'])
            results.append(body['enabled'])

        # All results should be identical
        assert len(set(results)) == 1, \
            "Same user should get consistent results"

    @patch('evaluator.get_dynamodb_resource')
    def test_end_to_end_complex_targeting_rules(self, mock_get_resource):
        """Test evaluation with multiple complex targeting rules."""
        from handler import lambda_handler

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'flag_complex',
                'key': 'complex_feature',
                'enabled': True,
                'rollout_percentage': 100.0,
                'targeting_rules': [
                    {"attribute": "country", "operator": "equals", "value": "US"},
                    {"attribute": "age", "operator": "greater_than", "value": 18},
                    {"attribute": "platform", "operator": "in", "value": ["web", "mobile"]}
                ]
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        # User matching all rules
        event_match = {
            "queryStringParameters": {
                "user_id": "user_match",
                "flag_key": "complex_feature"
            },
            "body": json.dumps({
                "context": {
                    "country": "US",
                    "age": 25,
                    "platform": "web"
                }
            })
        }

        response_match = lambda_handler(event_match, {})
        body_match = json.loads(response_match['body'])
        assert body_match['enabled'] is True

        # User not matching age rule
        event_no_match = {
            "queryStringParameters": {
                "user_id": "user_no_match",
                "flag_key": "complex_feature"
            },
            "body": json.dumps({
                "context": {
                    "country": "US",
                    "age": 16,  # Too young
                    "platform": "web"
                }
            })
        }

        response_no_match = lambda_handler(event_no_match, {})
        body_no_match = json.loads(response_no_match['body'])
        assert body_no_match['enabled'] is False

    @patch('evaluator.get_dynamodb_resource')
    def test_end_to_end_disabled_flag(self, mock_get_resource):
        """Test that disabled flag returns False regardless of other settings."""
        from handler import lambda_handler

        # Mock DynamoDB response - disabled flag
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'flag_disabled',
                'key': 'disabled_feature',
                'enabled': False,
                'rollout_percentage': 100.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        event = {
            "queryStringParameters": {
                "user_id": "user_any",
                "flag_key": "disabled_feature"
            }
        }

        response = lambda_handler(event, {})

        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['enabled'] is False
        assert body['reason'] == 'flag_disabled'

    @patch('evaluator.get_dynamodb_resource')
    def test_end_to_end_zero_percent_rollout(self, mock_get_resource):
        """Test that 0% rollout excludes all users."""
        from handler import lambda_handler

        # Mock DynamoDB response
        mock_table = Mock()
        mock_table.get_item.return_value = {
            'Item': {
                'flag_id': 'flag_zero',
                'key': 'zero_rollout',
                'enabled': True,
                'rollout_percentage': 0.0
            }
        }
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_get_resource.return_value = mock_resource

        # Test multiple users
        for i in range(10):
            event = {
                "queryStringParameters": {
                    "user_id": f"user_{i}",
                    "flag_key": "zero_rollout"
                }
            }

            response = lambda_handler(event, {})
            body = json.loads(response['body'])
            assert body['enabled'] is False
            assert body['reason'] == 'not_in_rollout'
