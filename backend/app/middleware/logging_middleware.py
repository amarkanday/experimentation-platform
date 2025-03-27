# backend/app/middleware/logging_middleware.py
"""
Middleware for logging HTTP requests and responses.

This middleware logs incoming requests and outgoing responses for debugging
and monitoring purposes.
"""

import time
import logging
import uuid
from typing import Callable, Awaitable

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Middleware for logging request/response details."""

    async def __call__(
        self, request: Request, call_next: RequestResponseEndpoint
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
