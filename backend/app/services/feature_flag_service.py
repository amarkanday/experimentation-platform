# Feature flag management service
# backend/app/services/feature_flag_service.py
import logging
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple
from uuid import UUID

from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session, joinedload

from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from backend.app.schemas.feature_flag import FeatureFlagCreate, FeatureFlagUpdate
from backend.app.services.metrics_service import MetricsService
from backend.app.schemas.metrics import ErrorLogCreate


logger = logging.getLogger(__name__)


class FeatureFlagService:
    """
    Service for managing feature flags in the platform.

    This service handles:
    - Creating and updating feature flags
    - Evaluating feature flags for users
    - Managing targeting rules and rollout percentages
    """

    def __init__(self, db: Session):
        """Initialize with a database session."""
        self.db = db

    def get_feature_flag(self, flag_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """
        Get a feature flag by ID.

        Args:
            flag_id: ID of the feature flag

        Returns:
            Dictionary containing the feature flag data or None if not found
        """
        flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()

        if not flag:
            return None

        return self._feature_flag_to_dict(flag)

    def get_feature_flags(
        self, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all feature flags with optional status filter.

        Args:
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            List of feature flag dictionaries
        """
        query = self.db.query(FeatureFlag)

        if status:
            query = query.filter(FeatureFlag.status == status)

        flags = query.offset(skip).limit(limit).all()
        return [self._feature_flag_to_dict(flag) for flag in flags]

    def count_feature_flags(self, status: Optional[str] = None) -> int:
        """
        Count feature flags with optional status filter.

        Args:
            status: Optional status filter

        Returns:
            Count of matching feature flags
        """
        query = self.db.query(func.count(FeatureFlag.id))

        if status:
            query = query.filter(FeatureFlag.status == status)

        return query.scalar() or 0

    def create_feature_flag(self, flag_data: FeatureFlagCreate) -> FeatureFlag:
        """Create a new feature flag."""
        try:
            # Convert Pydantic model to dict and create DB model
            flag_dict = flag_data.model_dump()

            # Handle is_active to status conversion
            if "is_active" in flag_dict:
                is_active = flag_dict.pop("is_active")
                flag_dict["status"] = FeatureFlagStatus.ACTIVE if is_active else FeatureFlagStatus.INACTIVE

            # Remove any other fields that don't exist in the model
            for key in list(flag_dict.keys()):
                if key not in [c.name for c in FeatureFlag.__table__.columns]:
                    flag_dict.pop(key)

            flag = FeatureFlag(**flag_dict)

            # Add and commit to DB
            self.db.add(flag)
            self.db.commit()
            self.db.refresh(flag)

            return flag
        except Exception as e:
            logger.error(f"Error creating feature flag: {str(e)}")
            self.db.rollback()
            raise

    def update_feature_flag(
        self, flag_id: Union[str, UUID, FeatureFlag], flag_data: FeatureFlagUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update an existing feature flag."""
        try:
            # Handle if a FeatureFlag object was passed instead of an ID
            if isinstance(flag_id, FeatureFlag):
                flag = flag_id
            else:
                # Get existing flag
                flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == flag_id).first()

            if not flag:
                return None

            # Update flag with new data
            update_data = flag_data.model_dump(exclude_unset=True)

            # Handle is_active to status conversion
            if "is_active" in update_data:
                is_active = update_data.pop("is_active")
                update_data["status"] = FeatureFlagStatus.ACTIVE if is_active else FeatureFlagStatus.INACTIVE

            # Remove fields that don't exist in the model
            for key in list(update_data.keys()):
                if key not in [c.name for c in FeatureFlag.__table__.columns]:
                    update_data.pop(key)

            for field, value in update_data.items():
                setattr(flag, field, value)

            # Commit changes
            self.db.commit()
            self.db.refresh(flag)

            return self._feature_flag_to_dict(flag)
        except Exception as e:
            logger.error(f"Error updating feature flag: {str(e)}")
            self.db.rollback()
            raise

    def delete_feature_flag(self, flag: FeatureFlag) -> None:
        """
        Delete a feature flag.

        Args:
            flag: Feature flag model object
        """
        flag_id = str(flag.id)
        flag_name = flag.name

        self.db.delete(flag)
        self.db.commit()

        logger.info(f"Deleted feature flag {flag_id}: {flag_name}")

    def activate_feature_flag(self, flag: FeatureFlag) -> Dict[str, Any]:
        """
        Activate a feature flag.

        Args:
            flag: Feature flag model object

        Returns:
            Dictionary containing the updated feature flag data
        """
        flag.status = FeatureFlagStatus.ACTIVE.value
        flag.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(flag)

        logger.info(f"Activated feature flag {flag.id}: {flag.name}")
        return self._feature_flag_to_dict(flag)

    def deactivate_feature_flag(self, flag: FeatureFlag) -> Dict[str, Any]:
        """
        Deactivate a feature flag.

        Args:
            flag: Feature flag model object

        Returns:
            Dictionary containing the updated feature flag data
        """
        flag.status = FeatureFlagStatus.INACTIVE.value
        flag.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(flag)

        logger.info(f"Deactivated feature flag {flag.id}: {flag.name}")
        return self._feature_flag_to_dict(flag)

    def get_user_flags(
        self, user_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get all active feature flags with their evaluation for a specific user.

        Args:
            user_id: ID of the user
            context: Optional context data for rule evaluation

        Returns:
            Dictionary mapping flag keys to their values for this user
        """
        # Get all active flags
        flags = (
            self.db.query(FeatureFlag)
            .filter(FeatureFlag.status == FeatureFlagStatus.ACTIVE.value)
            .all()
        )

        # Evaluate each flag for the user
        result = {}
        for flag in flags:
            result[flag.key] = self.evaluate_flag(flag, user_id, context)

        return result

    def evaluate_flag(
        self, flag: FeatureFlag, user_id: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Evaluate a feature flag for a specific user.

        Args:
            flag: Feature flag model object
            user_id: ID of the user
            context: Optional context data for rule evaluation

        Returns:
            Boolean indicating if the flag is enabled for this user
        """
        # Track evaluation time for latency metrics
        start_time = time.time()

        # Initialize tracking variables
        targeting_rule_id = None
        result = False
        error = None

        try:
            # If flag is not active, return False
            if flag.status != FeatureFlagStatus.ACTIVE.value:
                result = False
                return result

            # If flag has no rules, use the default value
            if not flag.targeting_rules or len(flag.targeting_rules) == 0:
                result = self._evaluate_percentage_rollout(flag, user_id)
                return result

            # Evaluate each rule
            context = context or {}

            # Extract rules from targeting_rules field (which is a JSONB field)
            rules = flag.targeting_rules

            if isinstance(rules, list):
                for i, rule in enumerate(rules):
                    rule_id = rule.get("id", f"rule_{i}")
                    if self._evaluate_rule(rule, user_id, context):
                        # If rule matches, use its rollout percentage
                        targeting_rule_id = rule_id
                        result = self._evaluate_percentage_rollout(
                            flag, user_id, rule.get("percentage", 100)
                        )
                        return result

            # If no rules match, use the default value
            result = self._evaluate_percentage_rollout(flag, user_id)
            return result

        except Exception as e:
            # Log and record the error
            error = str(e)
            logger.error(f"Error evaluating flag {flag.key} for user {user_id}: {error}")

            # Default behavior on error is to return False
            result = False
            return result

        finally:
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000  # Convert to milliseconds

            try:
                # Record metrics (in a separate try-except to avoid affecting the main flow)
                MetricsService.record_flag_evaluation(
                    db=self.db,
                    feature_flag_id=flag.id,
                    user_id=user_id,
                    value=result,
                    targeting_rule_id=targeting_rule_id,
                    latency_ms=latency_ms,
                    metadata={
                        "context": context,
                    }
                )

                # If there was an error, log it separately
                if error:
                    error_data = ErrorLogCreate(
                        error_type="flag_evaluation_error",
                        feature_flag_id=flag.id,
                        user_id=user_id,
                        message=error,
                        request_data={"context": context}
                    )
                    MetricsService.log_error(db=self.db, data=error_data)
            except Exception as metrics_error:
                # Don't let metrics collection errors affect flag evaluation
                logger.error(f"Failed to record metrics: {str(metrics_error)}")

    def _evaluate_rule(
        self, rule: Dict[str, Any], user_id: str, context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a targeting rule for a user.

        Args:
            rule: Rule dictionary from feature flag
            user_id: ID of the user
            context: Context data for rule evaluation

        Returns:
            Boolean indicating if the rule matches
        """
        # Get rule type and conditions
        rule_type = rule.get("type", "")
        conditions = rule.get("conditions", [])

        # Handle different rule types
        if rule_type == "user_id":
            # Direct user ID match
            target_ids = rule.get("user_ids", [])
            return user_id in target_ids

        elif rule_type == "context":
            # Context attribute match (all conditions must match)
            if not conditions:
                return False

            for condition in conditions:
                attribute = condition.get("attribute", "")
                operator = condition.get("operator", "")
                value = condition.get("value")

                # Skip if attribute not in context
                if attribute not in context:
                    return False

                # Get context value
                context_value = context[attribute]

                # Evaluate based on operator
                if operator == "eq" and context_value != value:
                    return False
                elif operator == "ne" and context_value == value:
                    return False
                elif operator == "gt" and not (
                    isinstance(context_value, (int, float)) and context_value > value
                ):
                    return False
                elif operator == "lt" and not (
                    isinstance(context_value, (int, float)) and context_value < value
                ):
                    return False
                elif operator == "contains" and not (
                    isinstance(context_value, str)
                    and isinstance(value, str)
                    and value in context_value
                ):
                    return False
                elif operator == "in" and not (
                    isinstance(value, (list, tuple)) and context_value in value
                ):
                    return False

            # All conditions passed
            return True

        # Unknown rule type
        return False

    def _evaluate_percentage_rollout(
        self, flag: FeatureFlag, user_id: str, percentage: Optional[int] = None
    ) -> bool:
        """
        Evaluate percentage-based rollout for a user.

        Args:
            flag: Feature flag model object
            user_id: ID of the user
            percentage: Rollout percentage (0-100), defaults to flag's percentage

        Returns:
            Boolean indicating if the user is in the rollout
        """
        # Use flag's percentage if not specified
        if percentage is None:
            percentage = flag.rollout_percentage or 0

        # If percentage is 0 or 100, short-circuit
        if percentage <= 0:
            return False
        if percentage >= 100:
            return True

        # Create a hash using user ID and flag key for deterministic assignment
        hash_input = f"{user_id}:{flag.key}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)

        # Get bucket (0-99)
        bucket = hash_value % 100

        # User is in the rollout if their bucket is less than the percentage
        return bucket < percentage

    def _feature_flag_to_dict(self, flag: FeatureFlag) -> Dict[str, Any]:
        """
        Convert a feature flag model to a dictionary for API responses.

        Args:
            flag: Feature flag model object

        Returns:
            Dictionary representation of the feature flag
        """
        return {
            "id": str(flag.id),
            "name": flag.name,
            "key": flag.key,
            "description": flag.description,
            "status": flag.status,
            "rollout_percentage": flag.rollout_percentage,
            "rules": flag.targeting_rules,
            "owner_id": str(flag.owner_id),
            "created_at": (
                flag.created_at.isoformat()
                if hasattr(flag.created_at, "isoformat")
                else flag.created_at
            ),
            "updated_at": (
                flag.updated_at.isoformat()
                if hasattr(flag.updated_at, "isoformat")
                else flag.updated_at
            ),
        }
