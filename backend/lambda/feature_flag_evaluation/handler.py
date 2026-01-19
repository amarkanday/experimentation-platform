"""
Lambda handler for feature flag evaluation.

Handles API Gateway requests for evaluating feature flags for users.

Following TDD (Test-Driven Development) - GREEN phase: Implementation to pass tests.
"""

import sys
import json
import os
import boto3
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Add shared module and current directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent))

from evaluator import FeatureFlagEvaluator
from models import FeatureFlagConfig
from utils import get_logger

logger = get_logger(__name__)

# Initialize evaluator once for Lambda warm-start optimization
# This persists across invocations in the same Lambda container
evaluator = None

# Flag to track if AWS clients have been initialized
_clients_initialized = False


def initialize_aws_clients() -> None:
    """
    Initialize and validate AWS clients and environment variables.

    Called once during Lambda cold start to validate configuration
    before processing requests.

    Raises:
        ValueError: If required environment variables are missing
    """
    global _clients_initialized

    if _clients_initialized:
        return

    # Validate required environment variables
    required_vars = ['FLAGS_TABLE']
    optional_vars = ['KINESIS_STREAM_NAME']

    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        error_msg = f"Missing required environment variables: {', '.join(missing)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Check optional but recommended variables
    for var in optional_vars:
        if not os.environ.get(var):
            logger.warning(
                f"Optional environment variable not set: {var}. "
                f"Some features may be disabled."
            )

    logger.info(
        "AWS clients initialized successfully",
        extra={
            'flags_table': os.environ.get('FLAGS_TABLE'),
            'kinesis_stream': os.environ.get('KINESIS_STREAM_NAME', 'not_set')
        }
    )

    _clients_initialized = True


def reset_evaluator() -> None:
    """
    Reset evaluator instance (primarily for testing).
    """
    global evaluator
    evaluator = None


def get_evaluator() -> FeatureFlagEvaluator:
    """
    Get or create evaluator instance (singleton pattern for Lambda warm-start).

    Returns:
        FeatureFlagEvaluator instance
    """
    global evaluator
    if evaluator is None:
        evaluator = FeatureFlagEvaluator()
    return evaluator


def record_evaluation_event_async(
    user_id: str,
    flag_config: FeatureFlagConfig,
    evaluation_result: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Record evaluation event to Kinesis asynchronously.

    This is a fire-and-forget operation - it should not block the response.
    Failures are logged but do not raise exceptions.

    Args:
        user_id: User ID who triggered the evaluation
        flag_config: Feature flag configuration that was evaluated
        evaluation_result: Result of the evaluation (enabled, reason, variant)
        context: Optional user context used for evaluation

    Note:
        Requires KINESIS_STREAM_NAME environment variable to be set.
    """
    try:
        stream_name = os.environ.get('KINESIS_STREAM_NAME')
        if not stream_name:
            logger.warning("KINESIS_STREAM_NAME not set, skipping evaluation tracking")
            return

        kinesis = boto3.client('kinesis')

        # Build event data
        event_data = {
            'event_type': 'feature_flag_evaluation',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_id': user_id,
            'flag_id': flag_config.flag_id,
            'flag_key': flag_config.key,
            'enabled': evaluation_result['enabled'],
            'reason': evaluation_result['reason'],
            'variant': evaluation_result.get('variant'),
            'context': context
        }

        # Send to Kinesis
        kinesis.put_record(
            StreamName=stream_name,
            Data=json.dumps(event_data),
            PartitionKey=user_id
        )

        logger.debug(
            f"Evaluation event recorded to Kinesis",
            extra={
                'flag_key': flag_config.key,
                'user_id': user_id,
                'enabled': evaluation_result['enabled']
            }
        )

    except Exception as e:
        # Log error but don't raise - tracking failures should not block responses
        logger.warning(
            f"Failed to record evaluation event to Kinesis: {str(e)}",
            extra={
                'flag_key': flag_config.key if flag_config else 'unknown',
                'user_id': user_id,
                'error_type': type(e).__name__
            }
        )


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for feature flag evaluation.

    Accepts API Gateway events with query parameters:
    - user_id: Unique user identifier (required)
    - flag_key: Feature flag key (required)

    Optional request body with JSON:
    - context: User context for targeting rules

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response with evaluation result or error

    Response format (success):
    {
        "user_id": "user_123",
        "flag_key": "new_checkout",
        "flag_id": "flag_123",
        "enabled": true,
        "reason": "enabled",
        "variant": "treatment"  # Optional, if variants configured
    }
    """
    # Initialize AWS clients and validate environment on cold start
    initialize_aws_clients()

    try:
        # Extract request metadata
        request_id = event.get('requestContext', {}).get('requestId', 'unknown')
        source_ip = event.get('requestContext', {}).get('sourceIp', 'unknown')

        logger.info(
            f"Feature flag evaluation request received",
            extra={
                'request_id': request_id,
                'source_ip': source_ip
            }
        )

        # Parse query parameters
        query_params = event.get('queryStringParameters')
        if not query_params:
            logger.warning("Missing query parameters")
            return create_error_response(
                400,
                "Missing query parameters. Required: user_id, flag_key"
            )

        user_id = query_params.get('user_id')
        flag_key = query_params.get('flag_key')

        # Validate required parameters
        if not user_id:
            logger.warning("Missing user_id parameter")
            return create_error_response(400, "Missing required parameter: user_id")

        if not flag_key:
            logger.warning("Missing flag_key parameter")
            return create_error_response(400, "Missing required parameter: flag_key")

        # Validate user_id is not empty or whitespace
        if not user_id.strip():
            logger.warning("Empty or whitespace user_id parameter")
            return create_error_response(400, "user_id cannot be empty")

        # Parse request body for user context
        user_context = None
        if event.get('body'):
            try:
                body = json.loads(event['body'])
                user_context = body.get('context')
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in request body")
                # Continue without context rather than failing

        # Get evaluator instance (singleton for warm-start caching)
        evaluator_instance = get_evaluator()

        # Get feature flag configuration (with caching)
        flag_config = evaluator_instance.get_flag_config_cached(flag_key)
        if not flag_config:
            logger.warning(
                f"Feature flag not found",
                extra={
                    'flag_key': flag_key,
                    'user_id': user_id
                }
            )
            return create_error_response(
                404,
                f"Feature flag not found: {flag_key}"
            )

        # Evaluate flag for user
        evaluation_result = evaluator_instance.evaluate(
            user_id=user_id,
            flag_config=flag_config,
            context=user_context
        )

        # Record evaluation event to Kinesis (fire-and-forget)
        # Wrap in try-except to ensure tracking failures don't block response
        try:
            record_evaluation_event_async(
                user_id=user_id,
                flag_config=flag_config,
                evaluation_result=evaluation_result,
                context=user_context
            )
        except Exception as e:
            # Log but don't raise - tracking is non-critical
            logger.warning(
                f"Failed to record evaluation tracking: {str(e)}",
                extra={'user_id': user_id, 'flag_key': flag_key}
            )

        # Log evaluation result
        logger.info(
            f"Feature flag evaluated",
            extra={
                'user_id': user_id,
                'flag_key': flag_key,
                'flag_id': flag_config.flag_id,
                'enabled': evaluation_result['enabled'],
                'reason': evaluation_result['reason']
            }
        )

        # Build response
        response_data = {
            'user_id': user_id,
            'flag_key': flag_key,
            'flag_id': flag_config.flag_id,
            'enabled': evaluation_result['enabled'],
            'reason': evaluation_result['reason']
        }

        # Include variant if present
        if evaluation_result.get('variant'):
            response_data['variant'] = evaluation_result['variant']

        return create_success_response(response_data)

    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Validation error: {str(e)}")
        return create_error_response(400, str(e))

    except Exception as e:
        # Handle unexpected errors
        logger.error(
            f"Internal server error: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'request_id': event.get('requestContext', {}).get('requestId', 'unknown')
            },
            exc_info=True
        )
        return create_error_response(
            500,
            "Internal server error occurred while processing feature flag evaluation request"
        )


def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create successful API Gateway response.

    Args:
        data: Response data dictionary

    Returns:
        API Gateway response dict with 200 status
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'
        },
        'body': json.dumps(data)
    }


def create_error_response(status_code: int, error_message: str) -> Dict[str, Any]:
    """
    Create error API Gateway response.

    Args:
        status_code: HTTP status code (400, 404, 500, etc.)
        error_message: Error message

    Returns:
        API Gateway response dict with error status
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'
        },
        'body': json.dumps({
            'error': error_message
        })
    }
