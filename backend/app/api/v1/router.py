"""
Main router for API v1 endpoints.

This module aggregates all v1 endpoint routers and re-exports them as a single router.
"""

from fastapi import APIRouter
from .endpoints import (
    auth,
    users,
    experiments,
    variants,
    metrics,
    feature_flags,
    assignments,
    events,
)

# Create the main router for v1 API
api_router = APIRouter()

# Include all endpoint routers with appropriate prefixes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(
    experiments.router, prefix="/experiments", tags=["Experiments"]
)
api_router.include_router(variants.router, prefix="/variants", tags=["Variants"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
api_router.include_router(
    feature_flags.router, prefix="/feature-flags", tags=["Feature Flags"]
)
api_router.include_router(
    assignments.router, prefix="/assignments", tags=["Assignments"]
)
api_router.include_router(events.router, prefix="/events", tags=["Events"])
