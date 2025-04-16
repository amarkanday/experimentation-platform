"""
Service for managing feature flag rollout schedules.

This module provides functionality for creating, updating, and managing
rollout schedules for feature flags.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from backend.app.models.feature_flag import FeatureFlag, FeatureFlagStatus
from backend.app.models.rollout_schedule import (
    RolloutSchedule,
    RolloutStage,
    RolloutScheduleStatus,
    RolloutStageStatus,
    TriggerType
)
from backend.app.schemas.rollout_schedule import (
    RolloutScheduleCreate,
    RolloutScheduleUpdate,
    RolloutStageCreate,
    RolloutStageUpdate
)
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class RolloutService:
    """
    Service for managing feature flag rollout schedules.

    This service handles:
    - Creating and updating rollout schedules
    - Managing rollout stages
    - Processing stage transitions
    - Validating schedule configurations
    """

    @staticmethod
    def create_rollout_schedule(
        db: Session,
        data: RolloutScheduleCreate,
        owner_id: UUID
    ) -> RolloutSchedule:
        """
        Create a new rollout schedule with the provided stages.

        Args:
            db: Database session
            data: Schedule data including stages
            owner_id: ID of the user creating the schedule

        Returns:
            The created schedule
        """
        # First check if the feature flag exists
        feature_flag = db.query(FeatureFlag).filter(
            FeatureFlag.id == data.feature_flag_id
        ).first()

        if not feature_flag:
            raise ValueError(f"Feature flag with ID {data.feature_flag_id} not found")

        # Create the schedule
        schedule = RolloutSchedule(
            name=data.name,
            description=data.description,
            feature_flag_id=data.feature_flag_id,
            owner_id=owner_id,
            start_date=data.start_date,
            end_date=data.end_date,
            metadata=data.metadata,
            max_percentage=data.max_percentage,
            min_stage_duration=data.min_stage_duration,
            status=RolloutScheduleStatus.DRAFT,
        )

        db.add(schedule)
        db.flush()  # Flush to get the ID for the schedule

        # Create the stages
        for stage_data in data.stages:
            stage = RolloutStage(
                rollout_schedule_id=schedule.id,
                name=stage_data.name,
                description=stage_data.description,
                stage_order=stage_data.stage_order,
                target_percentage=stage_data.target_percentage,
                trigger_type=TriggerType(stage_data.trigger_type.value),
                trigger_configuration=stage_data.trigger_configuration,
                start_date=stage_data.start_date,
                status=RolloutStageStatus.PENDING,
            )
            db.add(stage)

        # Commit the transaction
        db.commit()
        db.refresh(schedule)

        return schedule

    @staticmethod
    def get_rollout_schedule(db: Session, schedule_id: UUID) -> Optional[RolloutSchedule]:
        """
        Get a rollout schedule by ID.

        Args:
            db: Database session
            schedule_id: ID of the schedule to retrieve

        Returns:
            The schedule if found, None otherwise
        """
        return db.query(RolloutSchedule).filter(RolloutSchedule.id == schedule_id).first()

    @staticmethod
    def get_rollout_schedules(
        db: Session,
        feature_flag_id: Optional[UUID] = None,
        owner_id: Optional[UUID] = None,
        status: Optional[RolloutScheduleStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[RolloutSchedule], int]:
        """
        Get rollout schedules with optional filtering.

        Args:
            db: Database session
            feature_flag_id: Optional filter by feature flag ID
            owner_id: Optional filter by owner ID
            status: Optional filter by status
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            A tuple of (schedules, total_count)
        """
        query = db.query(RolloutSchedule)

        if feature_flag_id:
            query = query.filter(RolloutSchedule.feature_flag_id == feature_flag_id)

        if owner_id:
            query = query.filter(RolloutSchedule.owner_id == owner_id)

        if status:
            query = query.filter(RolloutSchedule.status == status)

        # Count total for pagination
        total = query.count()

        # Apply pagination
        schedules = query.order_by(RolloutSchedule.created_at.desc()).offset(skip).limit(limit).all()

        return schedules, total

    @staticmethod
    def update_rollout_schedule(
        db: Session,
        schedule_id: UUID,
        data: RolloutScheduleUpdate
    ) -> Optional[RolloutSchedule]:
        """
        Update an existing rollout schedule.

        Args:
            db: Database session
            schedule_id: ID of the schedule to update
            data: Updated schedule data

        Returns:
            The updated schedule if found, None otherwise
        """
        schedule = db.query(RolloutSchedule).filter(RolloutSchedule.id == schedule_id).first()

        if not schedule:
            return None

        # Validate status transition
        if data.status and data.status != schedule.status:
            if not RolloutService._validate_status_transition(schedule.status, data.status):
                raise ValueError(
                    f"Invalid status transition from {schedule.status.value} to {data.status.value}"
                )

            # If activating, ensure there's at least one stage
            if data.status == RolloutScheduleStatus.ACTIVE:
                stages_count = db.query(RolloutStage).filter(
                    RolloutStage.rollout_schedule_id == schedule_id
                ).count()

                if stages_count == 0:
                    raise ValueError("Cannot activate a schedule with no stages")

        # Update basic fields
        update_data = data.model_dump(exclude_unset=True)

        # Handle stages update if provided
        stages_data = update_data.pop('stages', None)

        for key, value in update_data.items():
            setattr(schedule, key, value)

        # Update stages if provided
        if stages_data:
            # First, update existing stages
            existing_stages = db.query(RolloutStage).filter(
                RolloutStage.rollout_schedule_id == schedule_id
            ).all()

            # Create a lookup map for existing stages
            existing_stage_map = {stage.id: stage for stage in existing_stages}

            for stage_data in stages_data:
                stage_id = getattr(stage_data, 'id', None)

                if stage_id and stage_id in existing_stage_map:
                    # Update existing stage
                    stage = existing_stage_map[stage_id]
                    stage_update_data = stage_data.model_dump(exclude_unset=True)

                    for key, value in stage_update_data.items():
                        setattr(stage, key, value)

                    db.add(stage)

        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        return schedule

    @staticmethod
    def add_rollout_stage(
        db: Session,
        schedule_id: UUID,
        data: RolloutStageCreate
    ) -> Optional[RolloutStage]:
        """
        Add a new stage to an existing rollout schedule.

        Args:
            db: Database session
            schedule_id: ID of the schedule to add a stage to
            data: Stage data

        Returns:
            The created stage if successful, None otherwise
        """
        schedule = db.query(RolloutSchedule).filter(RolloutSchedule.id == schedule_id).first()

        if not schedule:
            return None

        # Get max order of existing stages
        max_order = db.query(func.max(RolloutStage.stage_order)).filter(
            RolloutStage.rollout_schedule_id == schedule_id
        ).scalar() or 0

        # If no order is specified, put it at the end
        if data.stage_order is None:
            data.stage_order = max_order + 1

        # If order is in the middle, we need to shift other stages
        if data.stage_order <= max_order:
            stages_to_shift = db.query(RolloutStage).filter(
                and_(
                    RolloutStage.rollout_schedule_id == schedule_id,
                    RolloutStage.stage_order >= data.stage_order
                )
            ).all()

            for stage in stages_to_shift:
                stage.stage_order += 1
                db.add(stage)

        # Create the new stage
        stage = RolloutStage(
            rollout_schedule_id=schedule_id,
            name=data.name,
            description=data.description,
            stage_order=data.stage_order,
            target_percentage=data.target_percentage,
            trigger_type=TriggerType(data.trigger_type.value),
            trigger_configuration=data.trigger_configuration,
            start_date=data.start_date,
            status=RolloutStageStatus.PENDING,
        )

        db.add(stage)
        db.commit()
        db.refresh(stage)

        return stage

    @staticmethod
    def update_rollout_stage(
        db: Session,
        stage_id: UUID,
        data: RolloutStageUpdate
    ) -> Optional[RolloutStage]:
        """
        Update an existing rollout stage.

        Args:
            db: Database session
            stage_id: ID of the stage to update
            data: Updated stage data

        Returns:
            The updated stage if found, None otherwise
        """
        stage = db.query(RolloutStage).filter(RolloutStage.id == stage_id).first()

        if not stage:
            return None

        # If changing order, handle order shifts
        if data.stage_order is not None and data.stage_order != stage.stage_order:
            # Get the schedule to validate
            schedule = db.query(RolloutSchedule).filter(
                RolloutSchedule.id == stage.rollout_schedule_id
            ).first()

            if not schedule:
                raise ValueError("Schedule not found")

            # Don't allow changing order for stages that are not in PENDING status
            if stage.status != RolloutStageStatus.PENDING:
                raise ValueError("Cannot change order of stages that are not in PENDING status")

            # Handle shifting other stages
            if data.stage_order > stage.stage_order:
                # Moving down - shift up stages in between
                stages_to_shift = db.query(RolloutStage).filter(
                    and_(
                        RolloutStage.rollout_schedule_id == stage.rollout_schedule_id,
                        RolloutStage.stage_order > stage.stage_order,
                        RolloutStage.stage_order <= data.stage_order,
                        RolloutStage.id != stage.id
                    )
                ).all()

                for s in stages_to_shift:
                    s.stage_order -= 1
                    db.add(s)
            else:
                # Moving up - shift down stages in between
                stages_to_shift = db.query(RolloutStage).filter(
                    and_(
                        RolloutStage.rollout_schedule_id == stage.rollout_schedule_id,
                        RolloutStage.stage_order < stage.stage_order,
                        RolloutStage.stage_order >= data.stage_order,
                        RolloutStage.id != stage.id
                    )
                ).all()

                for s in stages_to_shift:
                    s.stage_order += 1
                    db.add(s)

        # Update fields
        update_data = data.model_dump(exclude_unset=True)

        if 'trigger_type' in update_data:
            update_data['trigger_type'] = TriggerType(update_data['trigger_type'].value)

        for key, value in update_data.items():
            setattr(stage, key, value)

        db.add(stage)
        db.commit()
        db.refresh(stage)

        return stage

    @staticmethod
    def delete_rollout_stage(db: Session, stage_id: UUID) -> bool:
        """
        Delete a rollout stage.

        Args:
            db: Database session
            stage_id: ID of the stage to delete

        Returns:
            True if the stage was deleted, False otherwise
        """
        stage = db.query(RolloutStage).filter(RolloutStage.id == stage_id).first()

        if not stage:
            return False

        # Don't allow deleting stages that are not in PENDING status
        if stage.status != RolloutStageStatus.PENDING:
            raise ValueError("Cannot delete stages that are not in PENDING status")

        # Get the schedule to validate
        schedule = db.query(RolloutSchedule).filter(
            RolloutSchedule.id == stage.rollout_schedule_id
        ).first()

        if not schedule:
            return False

        # Don't allow deleting stages from active schedules
        if schedule.status == RolloutScheduleStatus.ACTIVE:
            raise ValueError("Cannot delete stages from active schedules")

        # Update order of subsequent stages
        stages_to_shift = db.query(RolloutStage).filter(
            and_(
                RolloutStage.rollout_schedule_id == stage.rollout_schedule_id,
                RolloutStage.stage_order > stage.stage_order
            )
        ).all()

        for s in stages_to_shift:
            s.stage_order -= 1
            db.add(s)

        # Delete the stage
        db.delete(stage)
        db.commit()

        return True

    @staticmethod
    def activate_rollout_schedule(db: Session, schedule_id: UUID) -> Optional[RolloutSchedule]:
        """
        Activate a rollout schedule.

        Args:
            db: Database session
            schedule_id: ID of the schedule to activate

        Returns:
            The activated schedule if successful, None otherwise
        """
        schedule = db.query(RolloutSchedule).filter(RolloutSchedule.id == schedule_id).first()

        if not schedule:
            return None

        # Validate status transition
        if schedule.status != RolloutScheduleStatus.DRAFT and schedule.status != RolloutScheduleStatus.PAUSED:
            raise ValueError(f"Cannot activate schedule in {schedule.status.value} status")

        # Check that there's at least one stage
        stages_count = db.query(RolloutStage).filter(
            RolloutStage.rollout_schedule_id == schedule_id
        ).count()

        if stages_count == 0:
            raise ValueError("Cannot activate a schedule with no stages")

        # Update status
        schedule.status = RolloutScheduleStatus.ACTIVE
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        return schedule

    @staticmethod
    def pause_rollout_schedule(db: Session, schedule_id: UUID) -> Optional[RolloutSchedule]:
        """
        Pause an active rollout schedule.

        Args:
            db: Database session
            schedule_id: ID of the schedule to pause

        Returns:
            The paused schedule if successful, None otherwise
        """
        schedule = db.query(RolloutSchedule).filter(RolloutSchedule.id == schedule_id).first()

        if not schedule:
            return None

        # Validate status transition
        if schedule.status != RolloutScheduleStatus.ACTIVE:
            raise ValueError(f"Cannot pause schedule in {schedule.status.value} status")

        # Update status
        schedule.status = RolloutScheduleStatus.PAUSED
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        return schedule

    @staticmethod
    def cancel_rollout_schedule(db: Session, schedule_id: UUID) -> Optional[RolloutSchedule]:
        """
        Cancel a rollout schedule.

        Args:
            db: Database session
            schedule_id: ID of the schedule to cancel

        Returns:
            The cancelled schedule if successful, None otherwise
        """
        schedule = db.query(RolloutSchedule).filter(RolloutSchedule.id == schedule_id).first()

        if not schedule:
            return None

        # Cannot cancel completed schedules
        if schedule.status == RolloutScheduleStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed schedule")

        # Update status
        schedule.status = RolloutScheduleStatus.CANCELLED
        db.add(schedule)
        db.commit()
        db.refresh(schedule)

        return schedule

    @staticmethod
    def delete_rollout_schedule(db: Session, schedule_id: UUID) -> bool:
        """
        Delete a rollout schedule.

        Args:
            db: Database session
            schedule_id: ID of the schedule to delete

        Returns:
            True if the schedule was deleted, False otherwise
        """
        schedule = db.query(RolloutSchedule).filter(RolloutSchedule.id == schedule_id).first()

        if not schedule:
            return False

        # Cannot delete active schedules
        if schedule.status == RolloutScheduleStatus.ACTIVE:
            raise ValueError("Cannot delete an active schedule. Pause or cancel it first.")

        # Delete the schedule (cascades to stages)
        db.delete(schedule)
        db.commit()

        return True

    @staticmethod
    def manually_advance_stage(db: Session, stage_id: UUID) -> Optional[RolloutStage]:
        """
        Manually advance a stage that has manual triggers.

        Args:
            db: Database session
            stage_id: ID of the stage to advance

        Returns:
            The updated stage if successful, None otherwise
        """
        stage = db.query(RolloutStage).filter(RolloutStage.id == stage_id).first()

        if not stage:
            return None

        # Must be a manual trigger type
        if stage.trigger_type != TriggerType.MANUAL:
            raise ValueError("Can only manually advance stages with manual trigger type")

        # Must be in PENDING or IN_PROGRESS status
        valid_statuses = [RolloutStageStatus.PENDING, RolloutStageStatus.IN_PROGRESS]
        if stage.status not in valid_statuses:
            raise ValueError(f"Cannot advance stage in {stage.status.value} status")

        # Get the schedule
        schedule = db.query(RolloutSchedule).filter(
            RolloutSchedule.id == stage.rollout_schedule_id
        ).first()

        if not schedule:
            raise ValueError("Schedule not found")

        # Schedule must be active
        if schedule.status != RolloutScheduleStatus.ACTIVE:
            raise ValueError(f"Cannot advance stage for schedule in {schedule.status.value} status")

        current_time = datetime.now(timezone.utc)

        if stage.status == RolloutStageStatus.PENDING:
            # Activate the stage
            stage.status = RolloutStageStatus.IN_PROGRESS
            stage.updated_at = current_time

            # Update feature flag percentage
            feature_flag = db.query(FeatureFlag).filter(
                FeatureFlag.id == schedule.feature_flag_id
            ).with_for_update().first()

            if feature_flag:
                feature_flag.rollout_percentage = stage.target_percentage
                feature_flag.updated_at = current_time
                db.add(feature_flag)

        elif stage.status == RolloutStageStatus.IN_PROGRESS:
            # Complete the stage
            stage.status = RolloutStageStatus.COMPLETED
            stage.completed_date = current_time
            stage.updated_at = current_time

            # Check for next stage
            next_stage = db.query(RolloutStage).filter(
                and_(
                    RolloutStage.rollout_schedule_id == schedule.id,
                    RolloutStage.stage_order > stage.stage_order,
                    RolloutStage.status == RolloutStageStatus.PENDING
                )
            ).order_by(RolloutStage.stage_order).first()

            if next_stage:
                # Activate next stage
                next_stage.status = RolloutStageStatus.IN_PROGRESS
                next_stage.updated_at = current_time
                db.add(next_stage)

                # Update feature flag percentage
                feature_flag = db.query(FeatureFlag).filter(
                    FeatureFlag.id == schedule.feature_flag_id
                ).with_for_update().first()

                if feature_flag:
                    feature_flag.rollout_percentage = next_stage.target_percentage
                    feature_flag.updated_at = current_time
                    db.add(feature_flag)
            else:
                # No more stages, mark schedule as completed
                schedule.status = RolloutScheduleStatus.COMPLETED
                schedule.updated_at = current_time
                db.add(schedule)

        db.add(stage)
        db.commit()
        db.refresh(stage)

        return stage

    @staticmethod
    def _validate_status_transition(current_status: RolloutScheduleStatus, new_status: RolloutScheduleStatus) -> bool:
        """
        Validate if a status transition is allowed.

        Args:
            current_status: Current status of the schedule
            new_status: New status to transition to

        Returns:
            True if the transition is valid, False otherwise
        """
        # Define allowed transitions
        allowed_transitions = {
            RolloutScheduleStatus.DRAFT: [
                RolloutScheduleStatus.ACTIVE,
                RolloutScheduleStatus.CANCELLED
            ],
            RolloutScheduleStatus.ACTIVE: [
                RolloutScheduleStatus.PAUSED,
                RolloutScheduleStatus.COMPLETED,
                RolloutScheduleStatus.CANCELLED
            ],
            RolloutScheduleStatus.PAUSED: [
                RolloutScheduleStatus.ACTIVE,
                RolloutScheduleStatus.CANCELLED
            ],
            RolloutScheduleStatus.COMPLETED: [],  # No transitions from completed
            RolloutScheduleStatus.CANCELLED: [],  # No transitions from cancelled
        }

        return new_status in allowed_transitions.get(current_status, [])
