"""
API router configuration.

This module configures the API router by including all endpoint modules
and applying appropriate prefixes and tags.
"""

from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    auth,
    users,
    experiments,
    tracking,
    feature_flags,
    admin,
    assignments,
    events,
    results,
)

# Import the sample size calculator router
from backend.app.api.v1.sample_size_calculator import router as sample_size_router


# Create API router for v1
api_router_v1 = APIRouter()

# Include endpoint routers with appropriate prefixes and tags
api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(users.router, prefix="/users", tags=["Users"])
api_router_v1.include_router(
    experiments.router, prefix="/experiments", tags=["Experiments"]
)
api_router_v1.include_router(tracking.router, prefix="/tracking", tags=["Tracking"])
api_router_v1.include_router(
    feature_flags.router, prefix="/feature-flags", tags=["Feature Flags"]
)
api_router_v1.include_router(admin.router, prefix="/admin", tags=["Administration"])
api_router_v1.include_router(
    assignments.router, prefix="/assignments", tags=["Assignments"]
)
api_router_v1.include_router(events.router, prefix="/events", tags=["Events"])
api_router_v1.include_router(results.router, prefix="/results", tags=["Results"])

# Add new utility endpoints
api_router_v1.include_router(sample_size_router, prefix="/utils", tags=["Utilities"])

# Main API router that includes versioned routers
api_router = APIRouter()
api_router.include_router(api_router_v1, prefix="/v1")

# Documentation configuration
tags_metadata = [
    {
        "name": "Authentication",
        "description": "Operations for user authentication, registration and token management",
    },
    {
        "name": "Users",
        "description": "Operations for managing user accounts and profiles",
    },
    {
        "name": "Experiments",
        "description": "Operations for creating, managing and analyzing A/B tests and experiments",
    },
    {
        "name": "Tracking",
        "description": "Operations for tracking user interactions and experiment events",
    },
    {
        "name": "Feature Flags",
        "description": "Operations for managing feature flags and gradual rollouts",
    },
    {
        "name": "Assignments",
        "description": "Operations for managing user assignments to experiment variants",
    },
    {
        "name": "Events",
        "description": "Operations for querying and managing tracking events",
    },
    {
        "name": "Results",
        "description": "Operations for viewing results and analysis of experiments",
    },
    {
        "name": "Administration",
        "description": "Operations for system administration and management",
    },
    {
        "name": "Utilities",
        "description": "Utility operations for experiment design and planning",
    },
]
