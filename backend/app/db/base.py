# backend/app/db/base.py
"""
Base module for SQLAlchemy models.

Import all models here for Alembic migrations to detect them.
"""

# Import all models here
from backend.app.models.base import Base, BaseModel
from backend.app.models.user import User, Role, Permission
from backend.app.models.experiment import Experiment, Variant, Metric
from backend.app.models.assignment import Assignment
from backend.app.models.event import Event
from backend.app.models.feature_flag import FeatureFlag, FeatureFlagOverride
