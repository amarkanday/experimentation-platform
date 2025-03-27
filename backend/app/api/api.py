"""
API router configuration.

This module configures the API router by including all endpoint modules
and applying appropriate prefixes and tags.
"""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    auth,
    experiments,
    tracking,
    feature_flags,
    admin,
)

# Create API router for v1
api_router_v1 = APIRouter()

# Include endpoint routers with appropriate prefixes and tags
api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])

api_router_v1.include_router(
    experiments.router, prefix="/experiments", tags=["Experiments"]
)

api_router_v1.include_router(tracking.router, prefix="/tracking", tags=["Tracking"])

api_router_v1.include_router(
    feature_flags.router, prefix="/feature-flags", tags=["Feature Flags"]
)

api_router_v1.include_router(admin.router, prefix="/admin", tags=["Administration"])

# Main API router that includes versioned routers
api_router = APIRouter()
api_router.include_router(api_router_v1, prefix="/v1")
