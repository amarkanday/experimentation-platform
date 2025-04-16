"""
Unit tests for rollout scheduler.

This module tests the functionality of the RolloutScheduler class,
which manages automatic progression of feature flag rollout schedules.
"""

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call

from backend.app.core.rollout_scheduler import RolloutScheduler
from backend.app.models.rollout_schedule import (
    RolloutSchedule,
    RolloutStage,
    RolloutScheduleStatus,
    RolloutStageStatus,
    TriggerType
)
from backend.app.models.feature_flag import FeatureFlag


class TestRolloutScheduler:
    """Tests for the rollout scheduler functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def scheduler(self):
        """Create a scheduler instance for testing."""
        return RolloutScheduler(interval_minutes=1)

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_scheduler_initialization(self, mock_session, scheduler):
        """Test scheduler initialization with default parameters."""
        assert scheduler.interval_minutes == 1
        assert scheduler.is_running is False
        assert scheduler.task is None

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_scheduler_start_stop(self, mock_session, scheduler):
        """Test starting and stopping the scheduler."""
        # Test starting
        await scheduler.start()
        assert scheduler.is_running is True
        assert scheduler.task is not None

        # Test stopping
        await scheduler.stop()
        assert scheduler.is_running is False
        assert scheduler.task is None

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_scheduler_no_active_schedules(self, mock_session_class):
        """Test scheduler when there are no active schedules."""
        # Setup mock database session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock query to return no active schedules
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        # Create scheduler and process
        scheduler = RolloutScheduler(interval_minutes=1)
        await scheduler.process_rollout_schedules()

        # Verify
        mock_session.query.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_scheduler_activate_initial_stage(self, mock_session_class):
        """Test scheduler activating the first stage of a schedule."""
        # Setup mock database
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Create mock schedule and stage
        mock_schedule = MagicMock(spec=RolloutSchedule)
        mock_schedule.id = "schedule-1"
        mock_schedule.feature_flag_id = "flag-1"
        mock_schedule.status = RolloutScheduleStatus.ACTIVE
        mock_schedule.min_stage_duration = None
        mock_schedule.end_date = None

        mock_stage = MagicMock(spec=RolloutStage)
        mock_stage.id = "stage-1"
        mock_stage.rollout_schedule_id = "schedule-1"
        mock_stage.status = RolloutStageStatus.PENDING
        mock_stage.stage_order = 1
        mock_stage.trigger_type = TriggerType.TIME_BASED
        mock_stage.start_date = None  # Eligible for immediate activation
        mock_stage.target_percentage = 25

        # Setup mock queries
        mock_schedules_query = MagicMock()
        mock_session.query.return_value = mock_schedules_query
        mock_schedules_query.filter.return_value = mock_schedules_query
        mock_schedules_query.all.return_value = [mock_schedule]

        mock_active_stage_query = MagicMock()
        mock_pending_stage_query = MagicMock()

        # Set up query chain for active and pending stages
        def mock_query_side_effect(arg):
            if arg == RolloutSchedule:
                return mock_schedules_query
            elif arg == RolloutStage:
                # This query is called twice - first for active stages, then for pending stages
                if not hasattr(mock_query_side_effect, 'called'):
                    mock_query_side_effect.called = True
                    return mock_active_stage_query
                else:
                    return mock_pending_stage_query
            elif arg == FeatureFlag:
                mock_flag_query = MagicMock()
                mock_flag_query.filter.return_value = mock_flag_query
                mock_flag_query.with_for_update.return_value = mock_flag_query
                mock_flag_query.first.return_value = MagicMock(spec=FeatureFlag)
                return mock_flag_query

        mock_session.query.side_effect = mock_query_side_effect

        # No active stages
        mock_active_stage_query.filter.return_value = mock_active_stage_query
        mock_active_stage_query.first.return_value = None

        # One pending stage
        mock_pending_stage_query.filter.return_value = mock_pending_stage_query
        mock_pending_stage_query.order_by.return_value = mock_pending_stage_query
        mock_pending_stage_query.all.return_value = [mock_stage]

        # Create scheduler and patch _activate_stage
        scheduler = RolloutScheduler(interval_minutes=1)
        # Make _activate_stage return True to indicate the stage was updated
        scheduler._activate_stage = AsyncMock(return_value=True)

        # Process schedules
        await scheduler.process_rollout_schedules()

        # Verify _activate_stage was called correctly
        scheduler._activate_stage.assert_called_once()
        args = scheduler._activate_stage.call_args[0]
        assert args[0] == mock_session  # db
        assert args[1] == mock_schedule  # schedule
        assert args[2] == mock_stage  # stage
        # args[3] is current_time

        # Verify session closed
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_scheduler_complete_stage_and_activate_next(self, mock_session_class):
        """Test completing a stage and activating the next one."""
        # Setup mock database
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Create mock schedule and stages
        mock_schedule = MagicMock(spec=RolloutSchedule)
        mock_schedule.id = "schedule-1"
        mock_schedule.feature_flag_id = "flag-1"
        mock_schedule.status = RolloutScheduleStatus.ACTIVE
        mock_schedule.min_stage_duration = None
        mock_schedule.end_date = None

        # Current active stage
        mock_active_stage = MagicMock(spec=RolloutStage)
        mock_active_stage.id = "stage-1"
        mock_active_stage.rollout_schedule_id = "schedule-1"
        mock_active_stage.status = RolloutStageStatus.IN_PROGRESS
        mock_active_stage.stage_order = 1
        mock_active_stage.trigger_type = TriggerType.TIME_BASED
        mock_active_stage.updated_at = datetime.now(timezone.utc) - timedelta(hours=25)
        mock_active_stage.target_percentage = 25

        # Next pending stage
        mock_pending_stage = MagicMock(spec=RolloutStage)
        mock_pending_stage.id = "stage-2"
        mock_pending_stage.rollout_schedule_id = "schedule-1"
        mock_pending_stage.status = RolloutStageStatus.PENDING
        mock_pending_stage.stage_order = 2
        mock_pending_stage.trigger_type = TriggerType.TIME_BASED
        mock_pending_stage.start_date = None
        mock_pending_stage.target_percentage = 50

        # Setup mock queries
        mock_schedules_query = MagicMock()
        mock_session.query.return_value = mock_schedules_query
        mock_schedules_query.filter.return_value = mock_schedules_query
        mock_schedules_query.all.return_value = [mock_schedule]

        mock_active_stage_query = MagicMock()
        mock_pending_stage_query = MagicMock()

        # Set up query chain for active and pending stages
        def mock_query_side_effect(arg):
            if arg == RolloutSchedule:
                return mock_schedules_query
            elif arg == RolloutStage:
                # This query is called twice - first for active stages, then for pending stages
                if not hasattr(mock_query_side_effect, 'called'):
                    mock_query_side_effect.called = True
                    return mock_active_stage_query
                else:
                    return mock_pending_stage_query
            elif arg == FeatureFlag:
                mock_flag_query = MagicMock()
                mock_flag_query.filter.return_value = mock_flag_query
                mock_flag_query.with_for_update.return_value = mock_flag_query
                mock_flag_query.first.return_value = MagicMock(spec=FeatureFlag)
                return mock_flag_query

        mock_session.query.side_effect = mock_query_side_effect

        # One active stage
        mock_active_stage_query.filter.return_value = mock_active_stage_query
        mock_active_stage_query.first.return_value = mock_active_stage

        # One pending stage
        mock_pending_stage_query.filter.return_value = mock_pending_stage_query
        mock_pending_stage_query.order_by.return_value = mock_pending_stage_query
        mock_pending_stage_query.all.return_value = [mock_pending_stage]

        # Mock the completion check to return True (stage eligible for completion)
        scheduler = RolloutScheduler(interval_minutes=1)
        scheduler._is_stage_eligible_for_completion = MagicMock(return_value=True)
        scheduler._activate_stage = AsyncMock(return_value=True)

        # Process schedules
        await scheduler.process_rollout_schedules()

        # Verify stage was marked as completed
        assert mock_active_stage.status == RolloutStageStatus.COMPLETED
        assert mock_active_stage.completed_date is not None
        assert mock_active_stage.updated_at is not None
        mock_session.add.assert_called_with(mock_active_stage)

        # Verify next stage was activated
        scheduler._activate_stage.assert_called_once()
        args = scheduler._activate_stage.call_args[0]
        assert args[0] == mock_session  # db
        assert args[1] == mock_schedule  # schedule
        assert args[2] == mock_pending_stage  # stage

        # Verify commit was called
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_scheduler_complete_final_stage(self, mock_session_class):
        """Test completing the final stage of a schedule."""
        # Setup mock database
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Create mock schedule and stage
        mock_schedule = MagicMock(spec=RolloutSchedule)
        mock_schedule.id = "schedule-1"
        mock_schedule.feature_flag_id = "flag-1"
        mock_schedule.status = RolloutScheduleStatus.ACTIVE
        mock_schedule.min_stage_duration = None
        mock_schedule.end_date = None

        mock_active_stage = MagicMock(spec=RolloutStage)
        mock_active_stage.id = "stage-1"
        mock_active_stage.rollout_schedule_id = "schedule-1"
        mock_active_stage.status = RolloutStageStatus.IN_PROGRESS
        mock_active_stage.stage_order = 1
        mock_active_stage.trigger_type = TriggerType.TIME_BASED
        mock_active_stage.updated_at = datetime.now(timezone.utc) - timedelta(hours=25)
        mock_active_stage.target_percentage = 25

        # Setup mock queries
        mock_schedules_query = MagicMock()
        mock_session.query.return_value = mock_schedules_query
        mock_schedules_query.filter.return_value = mock_schedules_query
        mock_schedules_query.all.return_value = [mock_schedule]

        mock_active_stage_query = MagicMock()
        mock_pending_stage_query = MagicMock()

        # Set up query chain for active and pending stages
        def mock_query_side_effect(arg):
            if arg == RolloutSchedule:
                return mock_schedules_query
            elif arg == RolloutStage:
                # This query is called twice - first for active stages, then for pending stages
                if not hasattr(mock_query_side_effect, 'called'):
                    mock_query_side_effect.called = True
                    return mock_active_stage_query
                else:
                    return mock_pending_stage_query

        mock_session.query.side_effect = mock_query_side_effect

        # One active stage
        mock_active_stage_query.filter.return_value = mock_active_stage_query
        mock_active_stage_query.first.return_value = mock_active_stage

        # No pending stages
        mock_pending_stage_query.filter.return_value = mock_pending_stage_query
        mock_pending_stage_query.order_by.return_value = mock_pending_stage_query
        mock_pending_stage_query.all.return_value = []

        # Mock the completion check to return True (stage eligible for completion)
        scheduler = RolloutScheduler(interval_minutes=1)
        scheduler._is_stage_eligible_for_completion = MagicMock(return_value=True)

        # Process schedules
        await scheduler.process_rollout_schedules()

        # Verify stage was marked as completed
        assert mock_active_stage.status == RolloutStageStatus.COMPLETED
        assert mock_active_stage.completed_date is not None
        assert mock_active_stage.updated_at is not None

        # Verify schedule was marked as completed
        assert mock_schedule.status == RolloutScheduleStatus.COMPLETED
        assert mock_schedule.updated_at is not None

        # Verify commit was called
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    def test_is_stage_eligible_for_activation(self, scheduler):
        """Test checking if a stage is eligible for activation."""
        current_time = datetime.now(timezone.utc)

        # Stage not in PENDING status
        stage = MagicMock(spec=RolloutStage)
        stage.status = RolloutStageStatus.IN_PROGRESS
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is False

        # TIME_BASED trigger with no start date (eligible immediately)
        stage = MagicMock(spec=RolloutStage)
        stage.status = RolloutStageStatus.PENDING
        stage.trigger_type = TriggerType.TIME_BASED
        stage.start_date = None
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is True

        # TIME_BASED trigger with future start date
        stage = MagicMock(spec=RolloutStage)
        stage.status = RolloutStageStatus.PENDING
        stage.trigger_type = TriggerType.TIME_BASED
        stage.start_date = current_time + timedelta(hours=1)
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is False

        # TIME_BASED trigger with past start date
        stage = MagicMock(spec=RolloutStage)
        stage.status = RolloutStageStatus.PENDING
        stage.trigger_type = TriggerType.TIME_BASED
        stage.start_date = current_time - timedelta(hours=1)
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is True

        # MANUAL trigger (not eligible for automatic activation)
        stage = MagicMock(spec=RolloutStage)
        stage.status = RolloutStageStatus.PENDING
        stage.trigger_type = TriggerType.MANUAL
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is False

        # METRIC_BASED trigger (not implemented)
        stage = MagicMock(spec=RolloutStage)
        stage.status = RolloutStageStatus.PENDING
        stage.trigger_type = TriggerType.METRIC_BASED
        stage.id = "test-id"
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is False

    def test_is_stage_eligible_for_completion(self, scheduler):
        """Test checking if a stage is eligible for completion."""
        current_time = datetime.now(timezone.utc)

        # Stage not in IN_PROGRESS status
        stage = MagicMock(spec=RolloutStage)
        stage.status = RolloutStageStatus.PENDING
        assert scheduler._is_stage_eligible_for_completion(stage, current_time) is False

        # TIME_BASED trigger with enough time elapsed
        stage = MagicMock(spec=RolloutStage)
        stage.status = RolloutStageStatus.IN_PROGRESS
        stage.trigger_type = TriggerType.TIME_BASED
        stage.updated_at = current_time - timedelta(hours=25)  # Default duration is 24 hours
        stage.trigger_configuration = None
        assert scheduler._is_stage_eligible_for_completion(stage, current_time) is True

        # TIME_BASED trigger with custom duration
        stage = MagicMock(spec=RolloutStage)
        stage.status = RolloutStageStatus.IN_PROGRESS
        stage.trigger_type = TriggerType.TIME_BASED
        stage.updated_at = current_time - timedelta(hours=6)
        stage.trigger_configuration = {"duration": 12}
        assert scheduler._is_stage_eligible_for_completion(stage, current_time) is False

        stage.updated_at = current_time - timedelta(hours=13)
        assert scheduler._is_stage_eligible_for_completion(stage, current_time) is True

        # MANUAL trigger (not eligible for automatic completion)
        stage = MagicMock(spec=RolloutStage)
        stage.status = RolloutStageStatus.IN_PROGRESS
        stage.trigger_type = TriggerType.MANUAL
        assert scheduler._is_stage_eligible_for_completion(stage, current_time) is False

        # METRIC_BASED trigger (not implemented)
        stage = MagicMock(spec=RolloutStage)
        stage.status = RolloutStageStatus.IN_PROGRESS
        stage.trigger_type = TriggerType.METRIC_BASED
        stage.id = "test-id"
        assert scheduler._is_stage_eligible_for_completion(stage, current_time) is False

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_activate_stage(self, mock_session_class):
        """Test activating a stage and updating feature flag."""
        mock_session = MagicMock()

        # Create mock objects
        mock_schedule = MagicMock(spec=RolloutSchedule)
        mock_schedule.id = "schedule-1"
        mock_schedule.feature_flag_id = "flag-1"

        mock_stage = MagicMock(spec=RolloutStage)
        mock_stage.id = "stage-1"
        mock_stage.name = "Stage 1"
        mock_stage.target_percentage = 25

        mock_feature_flag = MagicMock(spec=FeatureFlag)
        mock_feature_flag.key = "test-flag"

        # Setup mock query for feature flag
        mock_flag_query = MagicMock()
        mock_session.query.return_value = mock_flag_query
        mock_flag_query.filter.return_value = mock_flag_query
        mock_flag_query.with_for_update.return_value = mock_flag_query
        mock_flag_query.first.return_value = mock_feature_flag

        # Activate the stage
        scheduler = RolloutScheduler(interval_minutes=1)
        current_time = datetime.now(timezone.utc)
        result = await scheduler._activate_stage(mock_session, mock_schedule, mock_stage, current_time)

        # Verify results
        assert result is True
        assert mock_stage.status == RolloutStageStatus.IN_PROGRESS
        assert mock_stage.updated_at == current_time
        assert mock_feature_flag.rollout_percentage == 25
        assert mock_feature_flag.updated_at == current_time

        # Verify method calls
        mock_session.add.assert_has_calls([
            call(mock_stage),
            call(mock_feature_flag)
        ])
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_activate_stage_feature_flag_not_found(self, mock_session_class):
        """Test activating a stage when feature flag is not found."""
        mock_session = MagicMock()

        # Create mock objects
        mock_schedule = MagicMock(spec=RolloutSchedule)
        mock_schedule.id = "schedule-1"
        mock_schedule.feature_flag_id = "flag-1"

        mock_stage = MagicMock(spec=RolloutStage)
        mock_stage.id = "stage-1"
        mock_stage.name = "Stage 1"
        mock_stage.target_percentage = 25

        # Setup mock query for feature flag to return None
        mock_flag_query = MagicMock()
        mock_session.query.return_value = mock_flag_query
        mock_flag_query.filter.return_value = mock_flag_query
        mock_flag_query.with_for_update.return_value = mock_flag_query
        mock_flag_query.first.return_value = None

        # Activate the stage
        scheduler = RolloutScheduler(interval_minutes=1)
        current_time = datetime.now(timezone.utc)
        result = await scheduler._activate_stage(mock_session, mock_schedule, mock_stage, current_time)

        # Verify results
        assert result is False
        assert mock_stage.status == RolloutStageStatus.IN_PROGRESS  # Still updated
        mock_session.add.assert_called_once_with(mock_stage)
        mock_session.commit.assert_not_called()  # Shouldn't commit if flag not found

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_activate_stage_exception_handling(self, mock_session_class):
        """Test exception handling during stage activation."""
        mock_session = MagicMock()

        # Create mock objects
        mock_schedule = MagicMock(spec=RolloutSchedule)
        mock_schedule.id = "schedule-1"
        mock_schedule.feature_flag_id = "flag-1"

        mock_stage = MagicMock(spec=RolloutStage)
        mock_stage.id = "stage-1"
        mock_stage.name = "Stage 1"
        mock_stage.target_percentage = 25

        # Setup mock query to raise an exception
        mock_session.query.side_effect = Exception("Test error")

        # Activate the stage
        scheduler = RolloutScheduler(interval_minutes=1)
        current_time = datetime.now(timezone.utc)
        result = await scheduler._activate_stage(mock_session, mock_schedule, mock_stage, current_time)

        # Verify results
        assert result is False
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.asyncio.sleep')
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_scheduler_exception_handling(self, mock_session_class, mock_sleep):
        """Test scheduler exception handling during processing."""
        # Setup mock to raise exception
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.query.side_effect = Exception("Test error")

        # Create scheduler and run
        scheduler = RolloutScheduler(interval_minutes=1)
        scheduler.is_running = True

        # Mock sleep to stop after one iteration
        async def stop_after_call(*args, **kwargs):
            scheduler.is_running = False

        mock_sleep.side_effect = stop_after_call

        # Run the scheduler
        await scheduler._run_scheduler()

        # Verify error handling
        mock_session.close.assert_called_once()
