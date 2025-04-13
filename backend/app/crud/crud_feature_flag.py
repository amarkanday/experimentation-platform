"""
CRUD for feature flag management.

This module provides database operations for FeatureFlag models.
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from backend.app.crud.base import CRUDBase
from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from backend.app.schemas.feature_flag import FeatureFlagCreate, FeatureFlagUpdate


class CRUDFeatureFlag(CRUDBase[FeatureFlag, FeatureFlagCreate, FeatureFlagUpdate]):
    """Feature flag CRUD operations."""

    def get_by_key(self, db: Session, *, key: str) -> Optional[FeatureFlag]:
        """
        Get a feature flag by key.

        Args:
            db: Database session
            key: Key of the feature flag to get

        Returns:
            The feature flag if found, None otherwise
        """
        return db.query(FeatureFlag).filter(FeatureFlag.key == key).first()

    def create(self, db: Session, *, obj_in: FeatureFlagCreate) -> FeatureFlag:
        """
        Create a new feature flag.

        Args:
            db: Database session
            obj_in: Data to create the feature flag with

        Returns:
            The created feature flag
        """
        # Convert Pydantic model to dict
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else jsonable_encoder(obj_in)

        # Handle is_active to status conversion
        if "is_active" in obj_in_data:
            is_active = obj_in_data.pop("is_active")
            obj_in_data["status"] = FeatureFlagStatus.ACTIVE.value if is_active else FeatureFlagStatus.INACTIVE.value

        # Remove any fields that don't exist in the model
        model_fields = [c.name for c in FeatureFlag.__table__.columns]
        obj_in_data = {k: v for k, v in obj_in_data.items() if k in model_fields}

        # Create feature flag
        db_obj = FeatureFlag(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: FeatureFlag, obj_in: Union[FeatureFlagUpdate, Dict[str, Any]]
    ) -> FeatureFlag:
        """
        Update a feature flag.

        Args:
            db: Database session
            db_obj: The feature flag to update
            obj_in: New data to update the feature flag with

        Returns:
            The updated feature flag
        """
        # Convert to dict if it's a Pydantic model
        if hasattr(obj_in, "model_dump"):
            update_data = obj_in.model_dump(exclude_unset=True)
        elif hasattr(obj_in, "dict"):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            update_data = obj_in

        # Handle is_active to status conversion
        if "is_active" in update_data:
            is_active = update_data.pop("is_active")
            update_data["status"] = FeatureFlagStatus.ACTIVE.value if is_active else FeatureFlagStatus.INACTIVE.value

        # Remove fields that don't exist in the model
        model_fields = [c.name for c in FeatureFlag.__table__.columns]
        update_data = {k: v for k, v in update_data.items() if k in model_fields}

        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def get_active_flags(self, db: Session) -> List[FeatureFlag]:
        """
        Get all active feature flags.

        Args:
            db: Database session

        Returns:
            List of active feature flags
        """
        return db.query(FeatureFlag).filter(FeatureFlag.status == FeatureFlagStatus.ACTIVE.value).all()

    def activate(self, db: Session, *, db_obj: FeatureFlag) -> FeatureFlag:
        """
        Activate a feature flag.

        Args:
            db: Database session
            db_obj: The feature flag to activate

        Returns:
            The activated feature flag
        """
        db_obj.status = FeatureFlagStatus.ACTIVE.value
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def deactivate(self, db: Session, *, db_obj: FeatureFlag) -> FeatureFlag:
        """
        Deactivate a feature flag.

        Args:
            db: Database session
            db_obj: The feature flag to deactivate

        Returns:
            The deactivated feature flag
        """
        db_obj.status = FeatureFlagStatus.INACTIVE.value
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


crud_feature_flag = CRUDFeatureFlag(FeatureFlag)
