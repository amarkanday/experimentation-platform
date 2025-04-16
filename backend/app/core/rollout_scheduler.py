"""
Scheduler for feature flag rollout schedules.

This module provides scheduling functionality for automatically
progressing feature flag rollout schedules based on defined triggers.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from backend.app.db.session import SessionLocal
from backend.app.models.feature_flag import FeatureFlag
from backend.app.models.rollout_schedule import (
    RolloutSchedule,
    RolloutStage,
    RolloutScheduleStatus,
    RolloutStageStatus,
    TriggerType
)
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class RolloutScheduler:
    """Handles scheduled tasks for feature flag rollouts."""

    def __init__(self, interval_minutes: int = 15):
        """
        Initialize the rollout scheduler.

        Args:
            interval_minutes: How often to check for schedules that need to be updated (in minutes)
        """
        self.interval_minutes = interval_minutes
        self.is_running = False
        self.task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Rollout scheduler is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info(f"Rollout scheduler started with {self.interval_minutes} minute interval")

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
        logger.info("Rollout scheduler stopped")

    async def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.is_running:
            try:
                # Process rollout schedules that need updates
                await self.process_rollout_schedules()

                # Wait for the next interval
                await asyncio.sleep(self.interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rollout scheduler: {str(e)}")
                # Wait a bit before trying again
                await asyncio.sleep(60)

    async def process_rollout_schedules(self):
        """
        Process rollout schedules that need updates based on their triggers.

        This checks for:
        1. Schedules in ACTIVE status that have pending stages
        2. For each schedule, finds stages that should be activated
        3. Updates feature flag rollout percentages accordingly
        """
        logger.info("Processing rollout schedules")

        # Use a new database session for this task
        db = SessionLocal()
        try:
            current_time = datetime.now(timezone.utc)

            # Get active rollout schedules
            active_schedules = db.query(RolloutSchedule).filter(
                and_(
                    RolloutSchedule.status == RolloutScheduleStatus.ACTIVE,
                    or_(
                        RolloutSchedule.end_date.is_(None),
                        RolloutSchedule.end_date > current_time
                    )
                )
            ).all()

            if not active_schedules:
                logger.info("No active rollout schedules found")
                return

            logger.info(f"Found {len(active_schedules)} active rollout schedules")

            schedules_updated = 0
            stages_processed = 0

            # Process each active schedule
            for schedule in active_schedules:
                try:
                    # Find the current active stage and any pending stages
                    current_active_stage = db.query(RolloutStage).filter(
                        and_(
                            RolloutStage.rollout_schedule_id == schedule.id,
                            RolloutStage.status == RolloutStageStatus.IN_PROGRESS
                        )
                    ).first()

                    next_pending_stages = db.query(RolloutStage).filter(
                        and_(
                            RolloutStage.rollout_schedule_id == schedule.id,
                            RolloutStage.status == RolloutStageStatus.PENDING
                        )
                    ).order_by(RolloutStage.stage_order).all()

                    # If there's no active stage, activate the first pending stage if it's eligible
                    if not current_active_stage and next_pending_stages:
                        next_stage = next_pending_stages[0]
                        if self._is_stage_eligible_for_activation(next_stage, current_time):
                            # Activate the stage
                            was_updated = await self._activate_stage(db, schedule, next_stage, current_time)
                            if was_updated:
                                stages_processed += 1
                                schedules_updated += 1

                    # If there is an active stage, check if it's complete and can progress to the next stage
                    elif current_active_stage:
                        # Check if the stage should be marked complete
                        next_stage_index = 0
                        for i, stage in enumerate(next_pending_stages):
                            if stage.stage_order > current_active_stage.stage_order:
                                next_stage_index = i
                                break

                        if self._is_stage_eligible_for_completion(current_active_stage, current_time):
                            # Complete the current stage
                            current_active_stage.status = RolloutStageStatus.COMPLETED
                            current_active_stage.completed_date = current_time
                            current_active_stage.updated_at = current_time
                            db.add(current_active_stage)

                            # If there are more stages, activate the next one if eligible
                            if next_pending_stages and next_stage_index < len(next_pending_stages):
                                next_stage = next_pending_stages[next_stage_index]

                                # Check minimum duration between stages
                                min_duration_hours = schedule.min_stage_duration or 0
                                if min_duration_hours > 0:
                                    min_duration = timedelta(hours=min_duration_hours)
                                    if current_time - current_active_stage.updated_at < min_duration:
                                        logger.info(
                                            f"Minimum duration not met for next stage in schedule {schedule.id}. "
                                            f"Will wait until {current_active_stage.updated_at + min_duration}"
                                        )
                                        continue

                                # Activate the next stage
                                was_updated = await self._activate_stage(db, schedule, next_stage, current_time)
                                if was_updated:
                                    stages_processed += 1
                            else:
                                # This was the last stage, mark the schedule as completed
                                schedule.status = RolloutScheduleStatus.COMPLETED
                                schedule.updated_at = current_time
                                db.add(schedule)
                                logger.info(f"Rollout schedule {schedule.id} completed")

                            db.commit()
                            schedules_updated += 1

                except Exception as e:
                    logger.error(f"Error processing rollout schedule {schedule.id}: {str(e)}")
                    # Continue with next schedule

            if schedules_updated > 0:
                logger.info(f"Updated {schedules_updated} rollout schedules with {stages_processed} stage transitions")
            else:
                logger.info("No rollout schedules required updates")

        except Exception as e:
            logger.error(f"Error processing rollout schedules: {str(e)}")
        finally:
            db.close()

    def _is_stage_eligible_for_activation(self, stage: RolloutStage, current_time: datetime) -> bool:
        """
        Check if a stage is eligible for activation based on its trigger.

        Args:
            stage: The stage to check
            current_time: The current time

        Returns:
            True if the stage should be activated, False otherwise
        """
        if stage.status != RolloutStageStatus.PENDING:
            return False

        if stage.trigger_type == TriggerType.TIME_BASED:
            # For time-based triggers, check if the scheduled time has passed
            if not stage.start_date:
                # If no specific start date, stage can be activated immediately
                return True

            return stage.start_date <= current_time

        elif stage.trigger_type == TriggerType.METRIC_BASED:
            # For metric-based triggers, this would check if metrics meet criteria
            # This requires integration with a metrics system and is more complex
            # For now, return False as this is not implemented
            logger.info(f"Metric-based activation for stage {stage.id} not yet implemented")
            return False

        elif stage.trigger_type == TriggerType.MANUAL:
            # Manual stages are only activated manually, never by the scheduler
            return False

        return False

    def _is_stage_eligible_for_completion(self, stage: RolloutStage, current_time: datetime) -> bool:
        """
        Check if a stage is eligible for completion based on its criteria.

        Args:
            stage: The stage to check
            current_time: The current time

        Returns:
            True if the stage should be completed, False otherwise
        """
        if stage.status != RolloutStageStatus.IN_PROGRESS:
            return False

        if stage.trigger_type == TriggerType.TIME_BASED:
            # For time-based triggers, check if a minimum time has passed
            # This could be based on a duration in the trigger configuration
            trigger_config = stage.trigger_configuration or {}
            duration_hours = trigger_config.get("duration", 24)  # Default to 24 hours

            # If the stage has been active for at least the specified duration, it's complete
            if stage.updated_at:
                min_time = stage.updated_at + timedelta(hours=duration_hours)
                return current_time >= min_time

            return False

        elif stage.trigger_type == TriggerType.METRIC_BASED:
            # Similar to activation, this would check metrics
            logger.info(f"Metric-based completion for stage {stage.id} not yet implemented")
            return False

        elif stage.trigger_type == TriggerType.MANUAL:
            # Manual stages are only completed manually
            return False

        return False

    async def _activate_stage(self, db: Session, schedule: RolloutSchedule, stage: RolloutStage, current_time: datetime) -> bool:
        """
        Activate a rollout stage and update the feature flag.

        Args:
            db: Database session
            schedule: The rollout schedule
            stage: The stage to activate
            current_time: The current time

        Returns:
            True if the stage was activated, False otherwise
        """
        try:
            # Mark the stage as in progress
            stage.status = RolloutStageStatus.IN_PROGRESS
            stage.updated_at = current_time
            db.add(stage)

            # Update the feature flag's rollout percentage
            feature_flag = db.query(FeatureFlag).filter(
                FeatureFlag.id == schedule.feature_flag_id
            ).with_for_update().first()

            if not feature_flag:
                logger.error(f"Feature flag {schedule.feature_flag_id} not found for rollout schedule {schedule.id}")
                return False

            feature_flag.rollout_percentage = stage.target_percentage
            feature_flag.updated_at = current_time
            db.add(feature_flag)

            # Commit the changes
            db.commit()

            logger.info(
                f"Activated stage {stage.id} ({stage.name}) in schedule {schedule.id} - "
                f"Updated feature flag {feature_flag.key} to {stage.target_percentage}% rollout"
            )
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error activating stage {stage.id}: {str(e)}")
            return False

# Create a singleton instance of the scheduler
rollout_scheduler = RolloutScheduler()
