"""
Main application module.

This module initializes the FastAPI application with all middleware,
routes, and event handlers.
"""

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from backend.app.api.api import api_router
from backend.app.core.config import settings
from backend.app.middleware.security_middleware import SecurityHeadersMiddleware
from backend.app.middleware.logging_middleware import LoggingMiddleware


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.PROJECT_VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add security headers middleware
    application.add_middleware(SecurityHeadersMiddleware)

    # Add logging middleware
    application.add_middleware(LoggingMiddleware)

    # Add application routes
    application.include_router(api_router, prefix=settings.API_V1_STR)

    # Add OpenAPI documentation routes
    @application.get("/api/v1/openapi.json", include_in_schema=False)
    async def get_openapi_schema():
        return get_openapi(
            title=settings.PROJECT_NAME,
            version=settings.PROJECT_VERSION,
            description=settings.PROJECT_DESCRIPTION,
            routes=application.routes,
        )

    @application.get("/api/v1/docs", include_in_schema=False)
    async def get_swagger_docs():
        return get_swagger_ui_html(
            openapi_url="/api/v1/openapi.json",
            title=f"{settings.PROJECT_NAME} - Swagger UI",
        )

    @application.get("/api/v1/redoc", include_in_schema=False)
    async def get_redoc_docs():
        return get_redoc_html(
            openapi_url="/api/v1/openapi.json",
            title=f"{settings.PROJECT_NAME} - ReDoc",
        )

    # Add health check endpoint
    @application.get("/health", include_in_schema=False)
    async def health_check():
        return {"status": "healthy"}

    return application


# Create the application instance
app = create_application()

# This allows other modules to import the application instance
# without creating circular imports
__all__ = ["app"]
