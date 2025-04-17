"""
Scheduler for feature flag safety monitoring.

This module provides scheduling functionality for automatically
monitoring feature flags for safety issues and triggering rollbacks.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.app.db.session import SessionLocal
from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from backend.app.services.safety_service import SafetyService
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class SafetyScheduler:
    """Handles scheduled tasks for feature flag safety monitoring."""

    def __init__(self, interval_minutes: int = 5):
        """
        Initialize the safety scheduler.

        Args:
            interval_minutes: How often to check feature flags for safety issues (in minutes)
        """
        self.interval_minutes = interval_minutes
        self.is_running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Safety scheduler is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info(f"Safety scheduler started with {self.interval_minutes} minute interval")

    async def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return

        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        logger.info("Safety scheduler stopped")

    async def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.is_running:
            try:
                # Process feature flags that need safety checks
                await self.check_feature_flags_safety()

                # Wait for the next interval
                await asyncio.sleep(self.interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in safety scheduler: {str(e)}")
                # Wait a bit before trying again
                await asyncio.sleep(60)

    async def check_feature_flags_safety(self):
        """
        Check all active feature flags for safety issues.

        This checks:
        1. All active feature flags with rollout percentage > 0
        2. For each flag, check if safety monitoring is enabled
        3. If enabled, check safety metrics
        4. If auto-rollback is enabled and safety check fails, trigger rollback
        """
        logger.info("Checking feature flags safety")

        # Use a new database session for this task
        db = SessionLocal()
        try:
            # Get all active feature flags with rollout percentage > 0
            active_flags = db.query(FeatureFlag).filter(
                and_(
                    FeatureFlag.status == FeatureFlagStatus.ACTIVE,
                    FeatureFlag.rollout_percentage > 0
                )
            ).all()

            if not active_flags:
                logger.info("No active feature flags with rollout percentage > 0 found")
                return

            safety_service = SafetyService(db)

            # Check each feature flag for safety issues
            for feature_flag in active_flags:
                try:
                    # Get safety configuration for the feature flag
                    config = await safety_service.async_get_feature_flag_safety_config(feature_flag.id)

                    # Skip if safety monitoring is not enabled for this flag
                    if not config.enabled:
                        continue

                    # Check safety status
                    safety_check = await safety_service.check_feature_flag_safety(feature_flag.id)

                    # Log the safety check result
                    if safety_check.is_healthy:
                        logger.info(f"Feature flag {feature_flag.key} ({feature_flag.id}) is healthy")
                    else:
                        logger.warning(f"Feature flag {feature_flag.key} ({feature_flag.id}) has safety issues: {safety_check.details}")

                    # If auto-rollback is enabled and safety check fails, trigger rollback
                    settings = await safety_service.async_get_safety_settings()

                    if settings.enable_automatic_rollbacks and not safety_check.is_healthy:
                        logger.warning(f"Triggering automatic rollback for feature flag {feature_flag.key} ({feature_flag.id})")

                        # Find what metric triggered the rollback
                        trigger_reason = "Automatic rollback due to safety issues"
                        for metric in safety_check.metrics:
                            if not metric.is_healthy:
                                trigger_reason = f"Automatic rollback due to {metric.name} exceeding threshold ({metric.current_value} > {metric.threshold})"
                                break

                        # Execute rollback
                        rollback_result = await safety_service.async_rollback_feature_flag(
                            feature_flag_id=feature_flag.id,
                            percentage=0,
                            reason=trigger_reason
                        )

                        if rollback_result.success:
                            logger.info(f"Successfully rolled back feature flag {feature_flag.key}: {rollback_result.message}")
                        else:
                            logger.error(f"Failed to roll back feature flag {feature_flag.key}: {rollback_result.message}")

                except Exception as e:
                    logger.error(f"Error checking safety for feature flag {feature_flag.id}: {str(e)}")

        except Exception as e:
            logger.error(f"Error checking feature flags safety: {str(e)}")
        finally:
            db.close()


# Create a global instance of the safety scheduler
safety_scheduler = SafetyScheduler()
