"""
Unit tests for rollout scheduler.

This is a standalone test file that can run independently without loading the main application.
"""

import sys
import os
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, call

# Add the parent directory to the path so we can import the modules we need
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import the module we're testing and its dependencies
from backend.app.core.rollout_scheduler import RolloutScheduler
from backend.app.models.rollout_schedule import (
    RolloutScheduleStatus,
    RolloutStageStatus,
    TriggerType
)


# Mock the dependencies we don't want to load
class MockFeatureFlag:
    def __init__(self):
        self.id = "flag-1"
        self.key = "test-flag"
        self.rollout_percentage = 0
        self.updated_at = None


class MockRolloutSchedule:
    def __init__(self):
        self.id = "schedule-1"
        self.name = "Test Schedule"
        self.feature_flag_id = "flag-1"
        self.status = RolloutScheduleStatus.ACTIVE
        self.min_stage_duration = None
        self.end_date = None
        self.updated_at = None


class MockRolloutStage:
    def __init__(self, status=RolloutStageStatus.PENDING, stage_order=1):
        self.id = f"stage-{stage_order}"
        self.name = f"Stage {stage_order}"
        self.rollout_schedule_id = "schedule-1"
        self.status = status
        self.stage_order = stage_order
        self.trigger_type = TriggerType.TIME_BASED
        self.start_date = None
        self.target_percentage = 25 * stage_order
        self.updated_at = datetime.now(timezone.utc) - timedelta(hours=25) if status == RolloutStageStatus.IN_PROGRESS else None
        self.completed_date = None
        self.trigger_configuration = None


class TestRolloutScheduler:
    """Tests for the rollout scheduler functionality."""

    @pytest_asyncio.fixture
    async def scheduler(self):
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

    def test_is_stage_eligible_for_activation(self, scheduler):
        """Test checking if a stage is eligible for activation."""
        current_time = datetime.now(timezone.utc)

        # Stage not in PENDING status
        stage = MagicMock()
        stage.status = RolloutStageStatus.IN_PROGRESS
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is False

        # TIME_BASED trigger with no start date (eligible immediately)
        stage = MagicMock()
        stage.status = RolloutStageStatus.PENDING
        stage.trigger_type = TriggerType.TIME_BASED
        stage.start_date = None
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is True

        # TIME_BASED trigger with future start date
        stage = MagicMock()
        stage.status = RolloutStageStatus.PENDING
        stage.trigger_type = TriggerType.TIME_BASED
        stage.start_date = current_time + timedelta(hours=1)
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is False

        # TIME_BASED trigger with past start date
        stage = MagicMock()
        stage.status = RolloutStageStatus.PENDING
        stage.trigger_type = TriggerType.TIME_BASED
        stage.start_date = current_time - timedelta(hours=1)
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is True

        # MANUAL trigger (not eligible for automatic activation)
        stage = MagicMock()
        stage.status = RolloutStageStatus.PENDING
        stage.trigger_type = TriggerType.MANUAL
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is False

        # METRIC_BASED trigger (not implemented)
        stage = MagicMock()
        stage.status = RolloutStageStatus.PENDING
        stage.trigger_type = TriggerType.METRIC_BASED
        stage.id = "test-id"
        assert scheduler._is_stage_eligible_for_activation(stage, current_time) is False

    def test_is_stage_eligible_for_completion(self, scheduler):
        """Test checking if a stage is eligible for completion."""
        current_time = datetime.now(timezone.utc)

        # Stage not in IN_PROGRESS status
        stage = MagicMock()
        stage.status = RolloutStageStatus.PENDING
        assert scheduler._is_stage_eligible_for_completion(stage, current_time) is False

        # TIME_BASED trigger with enough time elapsed
        stage = MagicMock()
        stage.status = RolloutStageStatus.IN_PROGRESS
        stage.trigger_type = TriggerType.TIME_BASED
        stage.updated_at = current_time - timedelta(hours=25)  # Default duration is 24 hours
        stage.trigger_configuration = None
        assert scheduler._is_stage_eligible_for_completion(stage, current_time) is True

        # TIME_BASED trigger with custom duration
        stage = MagicMock()
        stage.status = RolloutStageStatus.IN_PROGRESS
        stage.trigger_type = TriggerType.TIME_BASED
        stage.updated_at = current_time - timedelta(hours=6)
        stage.trigger_configuration = {"duration": 12}
        assert scheduler._is_stage_eligible_for_completion(stage, current_time) is False

        stage.updated_at = current_time - timedelta(hours=13)
        assert scheduler._is_stage_eligible_for_completion(stage, current_time) is True

        # MANUAL trigger (not eligible for automatic completion)
        stage = MagicMock()
        stage.status = RolloutStageStatus.IN_PROGRESS
        stage.trigger_type = TriggerType.MANUAL
        assert scheduler._is_stage_eligible_for_completion(stage, current_time) is False

        # METRIC_BASED trigger (not implemented)
        stage = MagicMock()
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
        mock_schedule = MagicMock()
        mock_schedule.id = "schedule-1"
        mock_schedule.feature_flag_id = "flag-1"

        mock_stage = MagicMock()
        mock_stage.id = "stage-1"
        mock_stage.name = "Stage 1"
        mock_stage.target_percentage = 25

        mock_feature_flag = MagicMock()
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
        mock_schedule = MagicMock()
        mock_schedule.id = "schedule-1"
        mock_schedule.feature_flag_id = "flag-1"

        mock_stage = MagicMock()
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
    async def test_no_active_schedules(self, mock_session_class):
        """Test scheduler when there are no active schedules."""
        # Setup mock database session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Setup mock query for active schedules that returns empty list
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        # Process schedules
        scheduler = RolloutScheduler(interval_minutes=1)
        await scheduler.process_rollout_schedules()

        # Verify session handling
        mock_session.query.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_error_handling(self, mock_session_class):
        """Test error handling in the scheduler."""
        # Setup mock database session
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Setup mock query that raises an exception
        mock_session.query.side_effect = Exception("Test database error")

        # Process schedules - should handle exception gracefully
        scheduler = RolloutScheduler(interval_minutes=1)
        await scheduler.process_rollout_schedules()

        # Verify session closed even after error
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.core.rollout_scheduler.asyncio.sleep')
    @patch('backend.app.core.rollout_scheduler.SessionLocal')
    async def test_run_scheduler(self, mock_session_class, mock_sleep):
        """Test the scheduler loop runs and stops correctly."""
        # Setup
        scheduler = RolloutScheduler(interval_minutes=1)
        scheduler.process_rollout_schedules = AsyncMock()
        scheduler.is_running = True

        # Mock sleep to stop the loop after one iteration
        async def stop_after_call(*args, **kwargs):
            scheduler.is_running = False

        mock_sleep.side_effect = stop_after_call

        # Run scheduler loop
        await scheduler._run_scheduler()

        # Verify process_rollout_schedules was called and sleep was used
        scheduler.process_rollout_schedules.assert_called_once()
        mock_sleep.assert_called_once_with(60)  # 1 minute = 60 seconds
