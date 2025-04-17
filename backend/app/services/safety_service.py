"""
Safety monitoring service for feature flags.

This service handles safety monitoring, configuration, and rollback functionality
for feature flags.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from sqlalchemy import and_, func, desc
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.safety import (
    SafetySettings,
    FeatureFlagSafetyConfig,
    SafetyRollbackRecord,
    RollbackTriggerType
)
from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from backend.app.models.metrics import RawMetric, ErrorLog
from backend.app.schemas.safety import (
    SafetySettingsCreate,
    SafetySettingsUpdate,
    FeatureFlagSafetyConfigCreate,
    FeatureFlagSafetyConfigUpdate,
    SafetyRollbackRecordCreate,
    SafetyCheckResponse,
    RollbackResponse,
    SafetySettingsResponse,
    FeatureFlagSafetyConfigResponse,
    MetricStatus
)
from backend.app.core.logging import get_logger
from backend.app.services.feature_flag_service import FeatureFlagService
from backend.app.services.metrics_service import MetricsService

logger = get_logger(__name__)


class SafetyService:
    """Service for safety monitoring and rollback functionality."""

    def __init__(self, db: Session):
        """Initialize the safety service with a database session."""
        self.db = db
        self.feature_flag_service = FeatureFlagService(db)
        # MetricsService is designed to be used with static methods only
        # self.metrics_service = MetricsService(db)

    @staticmethod
    def get_safety_settings(db: Session) -> Optional[SafetySettings]:
        """
        Get global safety settings.

        Args:
            db: Database session

        Returns:
            SafetySettings object if found, None otherwise
        """
        return db.query(SafetySettings).first()

    @staticmethod
    def create_safety_settings(
        db: Session, data: SafetySettingsCreate
    ) -> SafetySettings:
        """
        Create global safety settings.

        Args:
            db: Database session
            data: Safety settings data

        Returns:
            Created SafetySettings object
        """
        # Check if settings already exist
        existing = db.query(SafetySettings).first()
        if existing:
            raise ValueError("Safety settings already exist, use update instead")

        # Create new settings
        db_obj = SafetySettings(**data.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update_safety_settings(
        db: Session, data: SafetySettingsUpdate
    ) -> Optional[SafetySettings]:
        """
        Update global safety settings.

        Args:
            db: Database session
            data: Safety settings update data

        Returns:
            Updated SafetySettings object if found, None otherwise
        """
        # Get existing settings
        db_obj = db.query(SafetySettings).first()
        if not db_obj:
            return None

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_feature_flag_safety_config(
        db: Session, feature_flag_id: UUID
    ) -> Optional[FeatureFlagSafetyConfig]:
        """
        Get safety configuration for a feature flag.

        Args:
            db: Database session
            feature_flag_id: ID of the feature flag

        Returns:
            FeatureFlagSafetyConfig object if found, None otherwise
        """
        return db.query(FeatureFlagSafetyConfig).filter(
            FeatureFlagSafetyConfig.feature_flag_id == feature_flag_id
        ).first()

    @staticmethod
    def create_feature_flag_safety_config(
        db: Session, data: FeatureFlagSafetyConfigCreate
    ) -> FeatureFlagSafetyConfig:
        """
        Create safety configuration for a feature flag.

        Args:
            db: Database session
            data: Safety configuration data

        Returns:
            Created FeatureFlagSafetyConfig object
        """
        # Check if config already exists
        existing = db.query(FeatureFlagSafetyConfig).filter(
            FeatureFlagSafetyConfig.feature_flag_id == data.feature_flag_id
        ).first()
        if existing:
            raise ValueError(
                f"Safety config already exists for feature flag {data.feature_flag_id}"
            )

        # Check if feature flag exists
        feature_flag = db.query(FeatureFlag).filter(
            FeatureFlag.id == data.feature_flag_id
        ).first()
        if not feature_flag:
            raise ValueError(f"Feature flag {data.feature_flag_id} does not exist")

        # Create new config
        db_obj = FeatureFlagSafetyConfig(**data.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update_feature_flag_safety_config(
        db: Session, feature_flag_id: UUID, data: FeatureFlagSafetyConfigUpdate
    ) -> Optional[FeatureFlagSafetyConfig]:
        """
        Update safety configuration for a feature flag.

        Args:
            db: Database session
            feature_flag_id: ID of the feature flag
            data: Safety configuration update data

        Returns:
            Updated FeatureFlagSafetyConfig object if found, None otherwise
        """
        # Get existing config
        db_obj = db.query(FeatureFlagSafetyConfig).filter(
            FeatureFlagSafetyConfig.feature_flag_id == feature_flag_id
        ).first()
        if not db_obj:
            return None

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_or_create_safety_config(
        db: Session, feature_flag_id: UUID
    ) -> FeatureFlagSafetyConfig:
        """
        Get or create safety configuration for a feature flag.

        Args:
            db: Database session
            feature_flag_id: ID of the feature flag

        Returns:
            FeatureFlagSafetyConfig object
        """
        # Try to get existing config
        config = db.query(FeatureFlagSafetyConfig).filter(
            FeatureFlagSafetyConfig.feature_flag_id == feature_flag_id
        ).first()

        # If config exists, return it
        if config:
            return config

        # Check if feature flag exists
        feature_flag = db.query(FeatureFlag).filter(
            FeatureFlag.id == feature_flag_id
        ).first()
        if not feature_flag:
            raise ValueError(f"Feature flag {feature_flag_id} does not exist")

        # Create new config with default values
        config = FeatureFlagSafetyConfig(feature_flag_id=feature_flag_id)
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def create_rollback_record(
        db: Session, data: SafetyRollbackRecordCreate
    ) -> SafetyRollbackRecord:
        """
        Create a rollback record.

        Args:
            db: Database session
            data: Rollback record data

        Returns:
            Created SafetyRollbackRecord object
        """
        # Create new record
        db_obj = SafetyRollbackRecord(**data.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_error_metrics(
        self, db: Session, feature_flag_id: UUID, timeframe_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Get error metrics for a feature flag.

        Args:
            db: Database session
            feature_flag_id: ID of the feature flag
            timeframe_minutes: Timeframe for metrics collection in minutes

        Returns:
            Dictionary with error metrics
        """
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=timeframe_minutes)

        # Get feature flag
        feature_flag = db.query(FeatureFlag).filter(FeatureFlag.id == feature_flag_id).first()
        if not feature_flag:
            raise ValueError(f"Feature flag {feature_flag_id} does not exist")

        # Get error logs for the feature flag within the time window
        error_logs = db.query(ErrorLog).filter(
            ErrorLog.feature_flag_id == feature_flag_id,
            ErrorLog.created_at.between(start_time, end_time)
        ).all()

        # Get total evaluations for the feature flag within the time window
        total_evaluations = db.query(func.count(RawMetric.id)).filter(
            RawMetric.feature_flag_id == feature_flag_id,
            RawMetric.created_at.between(start_time, end_time)
        ).scalar() or 0

        # Count errors by type
        error_count = len(error_logs)
        error_types = {}
        for log in error_logs:
            error_type = log.error_type
            if error_type in error_types:
                error_types[error_type] += 1
            else:
                error_types[error_type] = 1

        # Calculate error rate
        error_rate = 0 if total_evaluations == 0 else error_count / total_evaluations

        # Return metrics
        return {
            "error_count": error_count,
            "total_evaluations": total_evaluations,
            "error_rate": error_rate,
            "error_types": error_types,
            "timeframe_minutes": timeframe_minutes,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

    def get_latency_metrics(
        self, db: Session, feature_flag_id: UUID, timeframe_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Get latency metrics for a feature flag.

        Args:
            db: Database session
            feature_flag_id: ID of the feature flag
            timeframe_minutes: Timeframe for metrics collection in minutes

        Returns:
            Dictionary with latency metrics
        """
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=timeframe_minutes)

        # Get feature flag
        feature_flag = db.query(FeatureFlag).filter(FeatureFlag.id == feature_flag_id).first()
        if not feature_flag:
            raise ValueError(f"Feature flag {feature_flag_id} does not exist")

        # Get latency metrics for the feature flag within the time window
        # This implementation assumes RawMetric has a 'latency' field
        # You may need to adapt this based on your actual data model
        metrics = db.query(RawMetric).filter(
            RawMetric.feature_flag_id == feature_flag_id,
            RawMetric.created_at.between(start_time, end_time)
        ).all()

        # Calculate latency statistics
        total_metrics = len(metrics)
        if total_metrics == 0:
            return {
                "avg_latency": 0,
                "max_latency": 0,
                "min_latency": 0,
                "p95_latency": 0,
                "total_requests": 0,
                "timeframe_minutes": timeframe_minutes,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }

        # Extract latency values
        latencies = [getattr(metric, 'latency', 0) for metric in metrics]
        latencies = [l for l in latencies if l is not None]

        if not latencies:
            return {
                "avg_latency": 0,
                "max_latency": 0,
                "min_latency": 0,
                "p95_latency": 0,
                "total_requests": total_metrics,
                "timeframe_minutes": timeframe_minutes,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }

        # Calculate statistics
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)

        # Calculate p95 latency
        sorted_latencies = sorted(latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        p95_latency = sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else max_latency

        # Return metrics
        return {
            "avg_latency": avg_latency,
            "max_latency": max_latency,
            "min_latency": min_latency,
            "p95_latency": p95_latency,
            "total_requests": total_metrics,
            "timeframe_minutes": timeframe_minutes,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

    async def get_safety_settings(self) -> SafetySettingsResponse:
        """Get the global safety settings."""
        settings = self.db.query(SafetySettings).first()

        if not settings:
            # Create default settings if none exist
            settings = SafetySettings(
                enabled=True,
                auto_rollback_enabled=False,
                default_metrics=[]
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)

        return SafetySettingsResponse.from_orm(settings)

    async def create_or_update_safety_settings(
        self, settings: SafetySettingsCreate
    ) -> SafetySettingsResponse:
        """Create or update the global safety settings."""
        existing_settings = self.db.query(SafetySettings).first()

        if existing_settings:
            # Update existing settings
            for key, value in settings.dict(exclude_unset=True).items():
                setattr(existing_settings, key, value)
        else:
            # Create new settings
            existing_settings = SafetySettings(**settings.dict())
            self.db.add(existing_settings)

        self.db.commit()
        self.db.refresh(existing_settings)
        return SafetySettingsResponse.from_orm(existing_settings)

    async def get_feature_flag_safety_config(
        self, feature_flag_id: UUID
    ) -> FeatureFlagSafetyConfigResponse:
        """Get safety configuration for a feature flag."""
        # First check if the feature flag exists
        feature_flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == feature_flag_id).first()
        if not feature_flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag with ID {feature_flag_id} not found"
            )

        config = self.db.query(FeatureFlagSafetyConfig).filter(
            FeatureFlagSafetyConfig.feature_flag_id == feature_flag_id
        ).first()

        if not config:
            # Return default configuration based on global settings
            settings = await self.async_get_safety_settings()
            return FeatureFlagSafetyConfigResponse(
                id=UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder ID
                feature_flag_id=feature_flag_id,
                enabled=settings.enabled,
                auto_rollback_enabled=settings.auto_rollback_enabled,
                metrics=settings.default_metrics,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

        return FeatureFlagSafetyConfigResponse.from_orm(config)

    async def create_or_update_feature_flag_safety_config(
        self, feature_flag_id: UUID, config: FeatureFlagSafetyConfigCreate
    ) -> FeatureFlagSafetyConfigResponse:
        """Create or update safety configuration for a feature flag."""
        # First check if the feature flag exists
        feature_flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == feature_flag_id).first()
        if not feature_flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag with ID {feature_flag_id} not found"
            )

        existing_config = self.db.query(FeatureFlagSafetyConfig).filter(
            FeatureFlagSafetyConfig.feature_flag_id == feature_flag_id
        ).first()

        if existing_config:
            # Update existing configuration
            for key, value in config.dict(exclude_unset=True).items():
                setattr(existing_config, key, value)
        else:
            # Create new configuration
            config_data = config.dict()
            existing_config = FeatureFlagSafetyConfig(
                feature_flag_id=feature_flag_id,
                **config_data
            )
            self.db.add(existing_config)

        self.db.commit()
        self.db.refresh(existing_config)
        return FeatureFlagSafetyConfigResponse.from_orm(existing_config)

    async def check_feature_flag_safety(
        self, feature_flag_id: UUID
    ) -> SafetyCheckResponse:
        """Check safety status of a feature flag."""
        # First check if the feature flag exists
        feature_flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == feature_flag_id).first()
        if not feature_flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag with ID {feature_flag_id} not found"
            )

        # Get safety configuration for the feature flag
        config = await self.async_get_feature_flag_safety_config(feature_flag_id)

        if not config.enabled:
            # Safety monitoring is not enabled for this feature flag
            return SafetyCheckResponse(
                feature_flag_id=feature_flag_id,
                is_healthy=True,  # Assume healthy if monitoring is disabled
                metrics=[],
                last_checked=datetime.utcnow(),
                details={"message": "Safety monitoring is disabled for this feature flag"}
            )

        # Retrieve current metric values for the feature flag
        # In a real implementation, this would query a metrics database or service
        metric_statuses = []
        is_healthy = True

        for metric in config.metrics:
            # In a real implementation, we would fetch the actual metric value
            # Here we're just simulating with a placeholder
            current_value = self._get_metric_value(feature_flag_id, metric.name)

            # Determine if the metric is healthy based on its threshold
            metric_is_healthy = current_value <= metric.threshold
            if not metric_is_healthy:
                is_healthy = False

            metric_statuses.append(
                MetricStatus(
                    name=metric.name,
                    description=metric.description,
                    current_value=current_value,
                    threshold=metric.threshold,
                    unit=metric.unit,
                    is_healthy=metric_is_healthy,
                    details={"feature_flag_id": str(feature_flag_id)}
                )
            )

        return SafetyCheckResponse(
            feature_flag_id=feature_flag_id,
            is_healthy=is_healthy,
            metrics=metric_statuses,
            last_checked=datetime.utcnow(),
            details={"feature_flag_key": feature_flag.key}
        )

    def _get_metric_value(self, feature_flag_id: UUID, metric_name: str) -> float:
        """Get the current value of a metric for a feature flag.

        This is a placeholder implementation. In a real system, this would query
        a metrics database or service to get the actual metric value.
        """
        # For demonstration purposes, return a simulated value
        # In a real implementation, this would use the metrics_service to get actual metrics
        import random
        return random.uniform(0.1, 5.0)  # Return a random value between 0.1 and 5.0

    async def rollback_feature_flag(
        self,
        feature_flag_id: UUID,
        percentage: Optional[int] = 0,
        reason: Optional[str] = "Manual rollback"
    ) -> RollbackResponse:
        """Roll back a feature flag to a safe state."""
        # First check if the feature flag exists
        feature_flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == feature_flag_id).first()
        if not feature_flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag with ID {feature_flag_id} not found"
            )

        # Get the current rollout percentage
        previous_percentage = feature_flag.rollout_percentage

        # Update the feature flag rollout percentage
        feature_flag.rollout_percentage = percentage
        self.db.commit()

        # In a real implementation, we would record the rollback in a safety_rollbacks table

        return RollbackResponse(
            feature_flag_id=feature_flag_id,
            success=True,
            message=f"Feature flag '{feature_flag.key}' rolled back from {previous_percentage}% to {percentage}%",
            trigger_type="manual",
            previous_percentage=previous_percentage,
            new_percentage=percentage,
            details={"reason": reason}
        )

    def should_rollback(
        self, db: Session, feature_flag_id: UUID
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Determine if a feature flag should be rolled back based on metrics.

        Args:
            db: Database session
            feature_flag_id: ID of the feature flag

        Returns:
            Tuple with (should_rollback, reason, metrics)
        """
        # Skip if feature flag does not exist or is not active
        feature_flag = db.query(FeatureFlag).filter(
            FeatureFlag.id == feature_flag_id,
            FeatureFlag.status == FeatureFlagStatus.ACTIVE
        ).first()
        if not feature_flag:
            return False, None, None

        # Skip if rollout percentage is 0
        if feature_flag.rollout_percentage == 0:
            return False, None, None

        # Get safety config
        safety_config = self.get_or_create_safety_config(db, feature_flag_id)

        # Skip if monitoring or auto-rollback is disabled
        if not safety_config.monitoring_enabled:
            return False, None, None

        if not safety_config.auto_rollback_enabled:
            return False, None, None

        # Check safety
        try:
            safety_check = self.check_feature_flag_safety(feature_flag_id)

            # If status is critical, recommend rollback
            if safety_check.is_healthy == False:
                # Determine the most severe issue
                reason = "Multiple issues detected"
                trigger_type = RollbackTriggerType.CUSTOM_METRIC
                trigger_value = None
                threshold_value = None

                for metric in safety_check.metrics:
                    if metric.is_healthy == False:
                        reason = f"Metric '{metric.name}' exceeded threshold"
                        trigger_type = RollbackTriggerType.METRIC
                        trigger_value = metric.current_value
                        threshold_value = metric.threshold
                        break

                # Return rollback recommendation
                return True, reason, {
                    "trigger_type": trigger_type,
                    "trigger_value": trigger_value,
                    "threshold_value": threshold_value,
                    "safety_check": safety_check.model_dump()
                }

            # Otherwise, don't rollback
            return False, None, None

        except Exception as e:
            logger.error(f"Error checking safety for feature flag {feature_flag_id}: {str(e)}")
            return False, None, None

    def execute_rollback(
        self, db: Session, feature_flag_id: UUID, reason: str = "Manual rollback",
        trigger_type: RollbackTriggerType = RollbackTriggerType.MANUAL,
        metrics_data: Optional[Dict[str, Any]] = None,
        trigger_value: Optional[float] = None,
        threshold_value: Optional[float] = None
    ) -> RollbackResponse:
        """
        Roll back a feature flag to safe state.

        Args:
            db: Database session
            feature_flag_id: ID of the feature flag
            reason: Reason for rollback
            trigger_type: Type of trigger that caused the rollback
            metrics_data: Metrics data at the time of rollback
            trigger_value: Value that triggered the rollback
            threshold_value: Threshold that was exceeded

        Returns:
            RollbackResponse with details of the rollback operation
        """
        # Start transaction
        try:
            # Get feature flag
            feature_flag = db.query(FeatureFlag).filter(
                FeatureFlag.id == feature_flag_id
            ).with_for_update().first()

            if not feature_flag:
                raise ValueError(f"Feature flag {feature_flag_id} does not exist")

            # Store previous percentage
            previous_percentage = feature_flag.rollout_percentage

            # Update feature flag to 0% rollout but keep it ACTIVE
            feature_flag.rollout_percentage = 0
            feature_flag.updated_at = datetime.utcnow()
            db.add(feature_flag)

            # Get safety config
            safety_config = self.get_or_create_safety_config(db, feature_flag_id)

            # Create rollback record
            rollback_record = SafetyRollbackRecord(
                safety_config_id=safety_config.id,
                trigger_type=trigger_type,
                trigger_value=trigger_value,
                threshold_value=threshold_value,
                rollout_percentage_before=previous_percentage,
                description=reason,
                metrics_data=metrics_data
            )
            db.add(rollback_record)

            # Commit transaction
            db.commit()
            db.refresh(rollback_record)

            # Log rollback
            logger.info(
                f"Rolled back feature flag {feature_flag_id} from {previous_percentage}% to 0%"
                f" due to {reason} (trigger: {trigger_type.value})"
            )

            # Return response
            return RollbackResponse(
                success=True,
                feature_flag_id=feature_flag_id,
                rollback_record_id=rollback_record.id,
                previous_percentage=previous_percentage,
                current_percentage=0,
                message=reason,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            # Rollback transaction on error
            db.rollback()
            logger.error(f"Error rolling back feature flag {feature_flag_id}: {str(e)}")

            # Return failure response
            return RollbackResponse(
                success=False,
                feature_flag_id=feature_flag_id,
                rollback_record_id=None,
                previous_percentage=-1,  # Use -1 to indicate unknown
                current_percentage=-1,   # Use -1 to indicate unknown
                message=f"Rollback failed: {str(e)}",
                timestamp=datetime.utcnow()
            )

    async def async_get_safety_settings(self) -> SafetySettingsResponse:
        """Get the global safety settings."""
        settings = self.db.query(SafetySettings).first()

        if not settings:
            # Create default settings if none exist
            settings = SafetySettings(
                enabled=True,
                auto_rollback_enabled=False,
                default_metrics=[]
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)

        return SafetySettingsResponse.from_orm(settings)

    async def async_get_feature_flag_safety_config(
        self, feature_flag_id: UUID
    ) -> FeatureFlagSafetyConfigResponse:
        """Get safety configuration for a feature flag."""
        # First check if the feature flag exists
        feature_flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == feature_flag_id).first()
        if not feature_flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag with ID {feature_flag_id} not found"
            )

        config = self.db.query(FeatureFlagSafetyConfig).filter(
            FeatureFlagSafetyConfig.feature_flag_id == feature_flag_id
        ).first()

        if not config:
            # Return default configuration based on global settings
            settings = await self.async_get_safety_settings()
            return FeatureFlagSafetyConfigResponse(
                id=UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder ID
                feature_flag_id=feature_flag_id,
                enabled=settings.enabled,
                auto_rollback_enabled=settings.auto_rollback_enabled,
                metrics=settings.default_metrics,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

        return FeatureFlagSafetyConfigResponse.from_orm(config)

    async def async_rollback_feature_flag(
        self,
        feature_flag_id: UUID,
        percentage: Optional[int] = 0,
        reason: Optional[str] = "Manual rollback"
    ) -> RollbackResponse:
        """Roll back a feature flag to a safe state."""
        # First check if the feature flag exists
        feature_flag = self.db.query(FeatureFlag).filter(FeatureFlag.id == feature_flag_id).first()
        if not feature_flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feature flag with ID {feature_flag_id} not found"
            )

        # Get the current rollout percentage
        previous_percentage = feature_flag.rollout_percentage

        # Update the feature flag rollout percentage
        feature_flag.rollout_percentage = percentage
        self.db.commit()

        # In a real implementation, we would record the rollback in a safety_rollbacks table

        return RollbackResponse(
            feature_flag_id=feature_flag_id,
            success=True,
            message=f"Feature flag '{feature_flag.key}' rolled back from {previous_percentage}% to {percentage}%",
            trigger_type="manual",
            previous_percentage=previous_percentage,
            new_percentage=percentage,
            details={"reason": reason}
        )
