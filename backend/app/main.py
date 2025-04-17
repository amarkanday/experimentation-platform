"""
Main FastAPI application module.

This module initializes the FastAPI application with all necessary middleware,
routers, and configuration.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Import routers and settings
from backend.app.api.api import api_router
from backend.app.core.config import settings
from backend.app.middleware.security_middleware import SecurityHeadersMiddleware
from backend.app.middleware.logging_middleware import LoggingMiddleware, RequestLoggingMiddleware
from backend.app.middleware.error_middleware import ErrorMiddleware
from backend.app.middleware.metrics_middleware import MetricsMiddleware
from backend.app.core.scheduler import experiment_scheduler
from backend.app.core.rollout_scheduler import rollout_scheduler
from backend.app.core.metrics_scheduler import metrics_scheduler
from backend.app.core.safety_scheduler import safety_scheduler

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add performance metrics middleware
app.add_middleware(MetricsMiddleware)

# Add error tracking middleware
app.add_middleware(ErrorMiddleware)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Add startup and shutdown events for the scheduler
@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    logger.info("Starting experiment scheduler")
    await experiment_scheduler.start()

    logger.info("Starting rollout scheduler")
    await rollout_scheduler.start()

    logger.info("Starting metrics scheduler")
    await metrics_scheduler.start()

    logger.info("Starting safety monitoring scheduler")
    await safety_scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background tasks on application shutdown."""
    logger.info("Stopping experiment scheduler")
    await experiment_scheduler.stop()

    logger.info("Stopping rollout scheduler")
    await rollout_scheduler.stop()

    logger.info("Stopping metrics scheduler")
    await metrics_scheduler.stop()

    logger.info("Stopping safety monitoring scheduler")
    await safety_scheduler.stop()

# Add OpenAPI documentation routes
@app.get("/api/v1/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    return get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.PROJECT_DESCRIPTION,
        routes=app.routes,
    )

@app.get("/api/v1/docs", include_in_schema=False)
async def get_swagger_docs():
    return get_swagger_ui_html(
        openapi_url="/api/v1/openapi.json",
        title=f"{settings.PROJECT_NAME} - Swagger UI",
    )

@app.get("/api/v1/redoc", include_in_schema=False)
async def get_redoc_docs():
    return get_redoc_html(
        openapi_url="/api/v1/openapi.json",
        title=f"{settings.PROJECT_NAME} - ReDoc",
    )

# Add health check endpoint
@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy"}

# This allows other modules to import the application instance
# without creating circular imports
__all__ = ["app"]
