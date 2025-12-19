"""
Lambda handler for experiment variant assignments.

Handles API Gateway requests for assigning users to experiment variants.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from assignment_service import AssignmentService
from utils import get_logger

logger = get_logger(__name__)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for experiment variant assignments.

    Accepts API Gateway events with query parameters:
    - user_id: Unique user identifier (required)
    - experiment_key: Experiment key (required)

    Optional request body with JSON:
    - context: User context for targeting rules

    Returns:
        API Gateway response with assignment details or error

    Response format (success):
    {
        "user_id": "user_123",
        "experiment_key": "checkout_redesign",
        "variant": "treatment",
        "assignment_id": "assign_abc123",
        "excluded": false
    }

    Response format (excluded):
    {
        "user_id": "user_123",
        "experiment_key": "checkout_redesign",
        "variant": null,
        "excluded": true
    }
    """
    try:
        # Extract request metadata
        request_id = event.get('requestContext', {}).get('requestId', 'unknown')
        source_ip = event.get('requestContext', {}).get('sourceIp', 'unknown')

        logger.info(
            f"Assignment request received",
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
                "Missing query parameters. Required: user_id, experiment_key"
            )

        user_id = query_params.get('user_id')
        experiment_key = query_params.get('experiment_key')

        # Validate required parameters
        if not user_id:
            logger.warning("Missing user_id parameter")
            return create_error_response(400, "Missing required parameter: user_id")

        if not experiment_key:
            logger.warning("Missing experiment_key parameter")
            return create_error_response(400, "Missing required parameter: experiment_key")

        # Validate user_id is not empty
        if not user_id.strip():
            logger.warning("Empty user_id parameter")
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

        # Initialize assignment service
        service = AssignmentService()

        # Get experiment configuration
        experiment_config = service.get_experiment_config_cached(experiment_key)
        if not experiment_config:
            logger.warning(
                f"Experiment not found",
                extra={
                    'experiment_key': experiment_key,
                    'user_id': user_id
                }
            )
            return create_error_response(
                404,
                f"Experiment not found: {experiment_key}"
            )

        # Get or create assignment
        assignment = service.get_or_create_assignment(
            user_id=user_id,
            experiment_config=experiment_config,
            context=user_context
        )

        # Handle excluded users
        if assignment is None:
            logger.info(
                f"User excluded from experiment",
                extra={
                    'user_id': user_id,
                    'experiment_key': experiment_key
                }
            )
            return create_success_response({
                'user_id': user_id,
                'experiment_key': experiment_key,
                'variant': None,
                'excluded': True
            })

        # Return successful assignment
        logger.info(
            f"Assignment returned",
            extra={
                'user_id': user_id,
                'experiment_key': experiment_key,
                'variant': assignment.variant,
                'assignment_id': assignment.assignment_id
            }
        )

        return create_success_response({
            'user_id': assignment.user_id,
            'experiment_key': assignment.experiment_key,
            'experiment_id': assignment.experiment_id,
            'variant': assignment.variant,
            'assignment_id': assignment.assignment_id,
            'excluded': False
        })

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
            "Internal server error occurred while processing assignment request"
        )


def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create successful API Gateway response.

    Args:
        data: Response data dictionary

    Returns:
        API Gateway response dict
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps(data)
    }


def create_error_response(status_code: int, error_message: str) -> Dict[str, Any]:
    """
    Create error API Gateway response.

    Args:
        status_code: HTTP status code
        error_message: Error message

    Returns:
        API Gateway response dict
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps({
            'error': error_message
        })
    }
