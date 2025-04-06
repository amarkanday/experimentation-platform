import os
import json
import time
import logging
import traceback
from typing import Dict, Any, Callable, Awaitable, Optional
from datetime import datetime

try:
    import fastapi
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
except ImportError:
    # For linting purposes, define placeholder types if imports fail
    BaseHTTPMiddleware = object
    class Request: pass
    class Response: pass

from backend.app.utils.aws_client import AWSClient

logger = logging.getLogger(__name__)

class ErrorMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking and reporting errors to CloudWatch.
    """

    def __init__(
        self,
        app,
        aws_client: Optional[AWSClient] = None,
        metric_namespace: str = "ExperimentationPlatform",
        track_errors: bool = True
    ):
        super().__init__(app)
        self.aws_client = aws_client
        self.namespace = metric_namespace
        self.track_errors = track_errors
        self.is_test_env = os.environ.get("TESTING", "false").lower() == "true"

        # Initialize CloudWatch metrics client if needed
        if self.track_errors and self.aws_client:
            self.aws_client.init_cloudwatch_metrics()
            logger.info("Error tracking enabled with CloudWatch integration")
        elif self.track_errors:
            logger.info("Error tracking enabled without CloudWatch")
        else:
            logger.info("Error tracking disabled")

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process the request and track any errors.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: The response from the API
        """
        if not self.track_errors:
            return await call_next(request)

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Track error metrics
            if self.aws_client:
                self._send_error_metrics(str(request.url.path), request.method, e)

            # Log error details
            self._log_error(request, e)

            # Re-raise the exception
            raise

    def _send_error_metrics(self, path: str, method: str, error: Exception) -> None:
        """Send error metrics to CloudWatch."""
        if not self.aws_client:
            return

        try:
            # Send error count metric
            self.aws_client.send_metric(
                namespace=self.namespace,
                metric_name="ErrorCount",
                value=1,
                unit="Count",
                dimensions={
                    "Endpoint": path,
                    "Method": method,
                    "ErrorType": type(error).__name__
                }
            )
        except Exception as e:
            logger.error(f"Failed to send error metrics to CloudWatch: {str(e)}")

    def _log_error(self, request: Request, error: Exception) -> None:
        """Log detailed error information."""
        error_details = {
            "path": str(request.url.path),
            "method": request.method,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add request context if available
        try:
            error_details.update({
                "client_host": request.client.host,
                "headers": dict(request.headers),
                "query_params": dict(request.query_params)
            })
        except Exception:
            pass

        logger.error(f"Request error: {error_details}", exc_info=True)
