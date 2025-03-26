"""
Main FastAPI application entry point with enhanced documentation.

This module initializes the FastAPI application with appropriate settings,
middleware, documentation endpoints, and routers.
"""

import logging
from typing import Dict, Any, List

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from backend.app.api.api import api_router
from backend.app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Create application
def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application with documentation
    """
    # Initialize FastAPI with customized documentation settings
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        debug=settings.DEBUG,
        # Set OpenAPI URL (used by both Swagger UI and ReDoc)
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        # Configure documentation URLs - disable in production if needed
        docs_url=(
            f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT != "prod" else None
        ),
        redoc_url=(
            f"{settings.API_V1_STR}/redoc" if settings.ENVIRONMENT != "prod" else None
        ),
        # Set terms of service and contact info
        terms_of_service="https://example.com/terms/",
        contact={
            "name": "API Support",
            "url": "https://example.com/support",
            "email": "api@example.com",
        },
        # Set license info
        license_info={
            "name": "Internal Use Only",
            "url": "https://example.com/license",
        },
    )

    # Custom OpenAPI schema generator (optional)
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            servers=[
                {
                    "url": settings.SERVER_URL,
                    "description": f"{settings.ENVIRONMENT} environment",
                },
            ],
        )

        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "OAuth2PasswordBearer": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": f"{settings.API_V1_STR}/auth/token",
                        "scopes": {},
                    }
                },
            },
            "APIKeyHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
            },
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    # Apply custom OpenAPI schema
    app.openapi = custom_openapi

    # Configure CORS middleware
    origins: List[str] = []
    if settings.BACKEND_CORS_ORIGINS:
        origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
        expose_headers=["Content-Length", "Content-Disposition"],
        max_age=600,  # Cache preflight requests for 10 minutes
    )

    # Add GZip compression for API responses
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Include static files if needed (for custom documentation)
    # app.mount("/static", StaticFiles(directory="static"), name="static")

    # Include centralized API router with all versions
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    """Run the application using Uvicorn when executed directly."""
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
