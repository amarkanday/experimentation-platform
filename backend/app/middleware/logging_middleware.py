# backend/app/middleware/logging_middleware.py
"""
Middleware for logging HTTP requests and responses.

This middleware logs incoming requests and outgoing responses using structured JSON logging.
"""

import os
import time
import uuid
from typing import Callable, Awaitable, Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.app.core.logging import get_logger, LogContext
from backend.app.utils.masking import mask_request_data, mask_sensitive_data
from backend.app.utils.metrics import MetricsCollector

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request/response details."""

    def __init__(self, app: ASGIApp):
        """Initialize the middleware."""
        super().__init__(app)
        self.collect_request_body = os.getenv("COLLECT_REQUEST_BODY", "true").lower() in ("true", "1", "yes")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log details."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Get user ID from request if available
        user_id = None
        if hasattr(request.state, "user"):
            user_id = str(request.state.user.id)

        # Get session ID from cookies if available
        session_id = request.cookies.get("session_id")

        # Initialize metrics collector
        metrics_collector = MetricsCollector()
        metrics_collector.start()

        # Create log context
        with LogContext(logger, request_id, user_id, session_id) as ctx:
            # Collect request data
            request_data = {
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "client_host": request.client.host if request.client else None,
            }

            # Collect request body for POST/PUT/PATCH if enabled
            if self.collect_request_body and request.method in ("POST", "PUT", "PATCH"):
                try:
                    body = await request.json()
                    request_data["body"] = body
                except (ValueError, Exception):
                    # Unable to parse JSON body, might be form data or other format
                    pass

            # Mask sensitive data
            masked_request_data = mask_request_data(request_data)

            # Log incoming request
            ctx.info("Request started", extra=masked_request_data)

            # Process the request
            try:
                response = await call_next(request)

                # Stop metrics collection
                metrics_collector.stop()
                performance_metrics = metrics_collector.get_metrics()

                # Collect and mask response data
                response_data = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                }

                masked_response_data = mask_sensitive_data(response_data)

                # Combine with performance metrics
                log_data = {
                    "response": masked_response_data,
                    "metrics": {
                        "process_time_ms": performance_metrics.get("duration_ms", 0),
                        "memory_usage_mb": performance_metrics.get("memory_change_mb", 0),
                        "total_memory_mb": performance_metrics.get("total_memory_mb", 0),
                        "cpu_percent": performance_metrics.get("cpu_percent", 0),
                    }
                }

                # Log successful response
                ctx.info("Request completed", extra=log_data)

                # Add custom headers
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Process-Time"] = str(performance_metrics.get("duration_ms", 0) / 1000)

                return response

            except Exception as e:
                # Stop metrics collection
                metrics_collector.stop()
                performance_metrics = metrics_collector.get_metrics()

                # Log exception with metrics
                error_data = {
                    "error": str(e),
                    "metrics": {
                        "process_time_ms": performance_metrics.get("duration_ms", 0),
                        "memory_usage_mb": performance_metrics.get("memory_change_mb", 0),
                        "total_memory_mb": performance_metrics.get("total_memory_mb", 0),
                        "cpu_percent": performance_metrics.get("cpu_percent", 0),
                    }
                }

                ctx.error("Request failed", exc_info=True, extra=error_data)
                raise


# Keep the original for backward compatibility
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request/response details (legacy version)."""

    def __init__(self, app: ASGIApp):
        """Initialize the middleware."""
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request and log details."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state for tracking
        request.state.request_id = request_id

        # Initialize metrics collector
        metrics_collector = MetricsCollector()
        metrics_collector.start()

        # Capture start time
        start_time = time.time()

        # Log incoming request (masked)
        masked_path = request.url.path
        masked_headers = mask_sensitive_data(dict(request.headers))

        logger.info(
            f"Request {request_id} started: {request.method} {masked_path}"
        )

        # Process the request
        try:
            response = await call_next(request)

            # Stop metrics collection
            metrics_collector.stop()
            performance_metrics = metrics_collector.get_metrics()

            # Log successful response
            logger.info(
                f"Request {request_id} completed: {response.status_code} "
                f"({performance_metrics.get('duration_ms', 0)/1000:.3f}s) "
                f"Memory: {performance_metrics.get('total_memory_mb', 0):.2f}MB "
                f"CPU: {performance_metrics.get('cpu_percent', 0):.2f}%"
            )

            # Add custom headers
            response.headers["X-Process-Time"] = str(performance_metrics.get("duration_ms", 0) / 1000)
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Stop metrics collection
            metrics_collector.stop()
            performance_metrics = metrics_collector.get_metrics()

            # Log exception
            logger.exception(
                f"Request {request_id} failed after {performance_metrics.get('duration_ms', 0)/1000:.3f}s: {str(e)} "
                f"Memory: {performance_metrics.get('total_memory_mb', 0):.2f}MB "
                f"CPU: {performance_metrics.get('cpu_percent', 0):.2f}%"
            )
            raise
