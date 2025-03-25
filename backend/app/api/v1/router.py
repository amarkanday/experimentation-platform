from backend.app.api.v1.endpoints import (
    assignments,
    events,
    experiments,
    feature_flags,
    users,
)
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(
    experiments.router, prefix="/experiments", tags=["experiments"]
)
api_router.include_router(
    feature_flags.router, prefix="/feature-flags", tags=["feature-flags"]
)
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(
    assignments.router, prefix="/assignments", tags=["assignments"]
)
api_router.include_router(users.router, prefix="/users", tags=["users"])
