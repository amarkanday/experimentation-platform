# backend/app/middleware/security_middleware.py
"""
Security middleware for adding security headers to responses.

This middleware adds various security headers to HTTP responses to enhance
application security and prevent common web vulnerabilities.
"""
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""

    def __init__(self, app: ASGIApp):
        """Initialize the middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to the response."""
        # Process the request and get the response
        response = await call_next(request)

        # Set Content Security Policy (CSP)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )

        # Set HSTS header in production
        if settings.ENVIRONMENT == "prod":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Set X-Frame-Options
        response.headers["X-Frame-Options"] = "DENY"

        # Set X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Set X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Set Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Set Permissions-Policy
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        return response
