# backend/app/middleware/logging_middleware.py
"""
Middleware for logging HTTP requests and responses.

This middleware logs incoming requests and outgoing responses using structured JSON logging.
"""

import time
import uuid
from typing import Callable, Awaitable, Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.app.core.logging import get_logger, LogContext

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request/response details."""

    def __init__(self, app: ASGIApp):
        """Initialize the middleware."""
        super().__init__(app)

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

        # Create log context
        with LogContext(logger, request_id, user_id, session_id) as ctx:
            # Capture start time
            start_time = time.time()

            # Log incoming request
            ctx.info(
                "Request started",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "headers": dict(request.headers),
                    "client_host": request.client.host if request.client else None,
                }
            )

            # Process the request
            try:
                response = await call_next(request)

                # Calculate processing time
                process_time = time.time() - start_time

                # Log successful response
                ctx.info(
                    "Request completed",
                    extra={
                        "status_code": response.status_code,
                        "process_time_ms": process_time * 1000,
                        "response_headers": dict(response.headers),
                    }
                )

                # Add custom headers
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Process-Time"] = str(process_time)

                return response

            except Exception as e:
                # Log exception
                process_time = time.time() - start_time
                ctx.error(
                    "Request failed",
                    exc_info=True,
                    extra={
                        "error": str(e),
                        "process_time_ms": process_time * 1000,
                    }
                )
                raise


# Keep the original for backward compatibility
class RequestLoggingMiddleware:
    """Middleware for logging request/response details (legacy version)."""

    async def __call__(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request and log details."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state for tracking
        request.state.request_id = request_id

        # Capture start time
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Request {request_id} started: {request.method} {request.url.path}"
        )

        # Process the request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log successful response
            logger.info(
                f"Request {request_id} completed: {response.status_code} "
                f"({process_time:.3f}s)"
            )

            # Add custom headers if needed
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log exception
            process_time = time.time() - start_time
            logger.exception(
                f"Request {request_id} failed after {process_time:.3f}s: {str(e)}"
            )
            raise
