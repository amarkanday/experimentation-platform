"""Unit tests for experiment scheduler."""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, AsyncMock, call

from backend.app.models.experiment import Experiment, ExperimentStatus
from backend.app.core.scheduler import ExperimentScheduler


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    return MagicMock()


@pytest.fixture
def scheduler():
    """Create an experiment scheduler for testing."""
    scheduler = ExperimentScheduler(interval_minutes=5)
    return scheduler


@pytest.mark.asyncio
async def test_scheduler_activate_experiments(
    scheduler, mock_db_session
):
    """Test that scheduler activates experiments when start_date is reached."""
    # Create mock experiments
    mock_experiment = MagicMock(spec=Experiment)
    mock_experiment.id = "test-id"
    mock_experiment.name = "Test Experiment"
    mock_experiment.status = ExperimentStatus.DRAFT
    mock_experiment.start_date = datetime.now(timezone.utc) - timedelta(minutes=10)
    mock_experiment.end_date = datetime.now(timezone.utc) + timedelta(days=1)

    # Create separate query mocks for activation and completion
    activate_query = MagicMock()
    activate_query.filter.return_value.all.return_value = [mock_experiment]

    complete_query = MagicMock()
    complete_query.filter.return_value.all.return_value = []

    # Set up the mock db to return different query objects
    mock_db_session.query.side_effect = [activate_query, complete_query]

    # Patch SessionLocal to return our mock session
    with patch("backend.app.core.scheduler.SessionLocal", return_value=mock_db_session):
        # Run the scheduler
        await scheduler.process_scheduled_experiments()

        # Check that the experiment was updated
        assert mock_experiment.status == ExperimentStatus.ACTIVE
        assert mock_db_session.add.called
        assert mock_db_session.commit.called


@pytest.mark.asyncio
async def test_scheduler_completes_experiments(
    scheduler, mock_db_session
):
    """Test that scheduler completes experiments when end_date is reached."""
    # Create mock experiments
    mock_experiment = MagicMock(spec=Experiment)
    mock_experiment.id = "test-id"
    mock_experiment.name = "Test Experiment"
    mock_experiment.status = ExperimentStatus.ACTIVE
    mock_experiment.start_date = datetime.now(timezone.utc) - timedelta(days=5)
    mock_experiment.end_date = datetime.now(timezone.utc) - timedelta(hours=1)

    # Create separate query mocks for activation and completion
    activate_query = MagicMock()
    activate_query.filter.return_value.all.return_value = []

    complete_query = MagicMock()
    complete_query.filter.return_value.all.return_value = [mock_experiment]

    # Set up the mock db to return different query objects
    mock_db_session.query.side_effect = [activate_query, complete_query]

    # Patch SessionLocal to return our mock session
    with patch("backend.app.core.scheduler.SessionLocal", return_value=mock_db_session):
        # Run the scheduler
        await scheduler.process_scheduled_experiments()

        # Check that the experiment was updated
        assert mock_experiment.status == ExperimentStatus.COMPLETED
        assert mock_db_session.add.called
        assert mock_db_session.commit.called


@pytest.mark.asyncio
async def test_scheduler_no_eligible_experiments(
    scheduler, mock_db_session
):
    """Test scheduler when no experiments need to be updated."""
    # Create separate query mocks for activation and completion
    activate_query = MagicMock()
    activate_query.filter.return_value.all.return_value = []

    complete_query = MagicMock()
    complete_query.filter.return_value.all.return_value = []

    # Set up the mock db to return different query objects
    mock_db_session.query.side_effect = [activate_query, complete_query]

    # Patch SessionLocal to return our mock session
    with patch("backend.app.core.scheduler.SessionLocal", return_value=mock_db_session):
        # Run the scheduler
        await scheduler.process_scheduled_experiments()

        # Check that commit was not called
        mock_db_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_scheduler_exception_handling(
    scheduler, mock_db_session
):
    """Test that scheduler handles exceptions gracefully."""
    # Setup the mock DB to raise an exception
    mock_db_session.query.side_effect = Exception("Test exception")

    # Patch SessionLocal to return our mock session
    with patch("backend.app.core.scheduler.SessionLocal", return_value=mock_db_session):
        # Run the scheduler - should not raise an exception
        await scheduler.process_scheduled_experiments()

        # Ensure the DB session was closed
        assert mock_db_session.close.called


@pytest.mark.asyncio
async def test_scheduler_activation_with_timezone(
    scheduler, mock_db_session
):
    """Test that scheduler handles timezone metadata correctly."""
    # Create mock experiment with timezone metadata
    mock_experiment = MagicMock(spec=Experiment)
    mock_experiment.id = "test-id"
    mock_experiment.name = "Test Experiment with Timezone"
    mock_experiment.status = ExperimentStatus.DRAFT
    mock_experiment.start_date = datetime.now(timezone.utc) - timedelta(minutes=10)
    mock_experiment.end_date = datetime.now(timezone.utc) + timedelta(days=1)
    mock_experiment.metadata = {"time_zone": "America/New_York"}

    # Create separate query mocks for activation and completion
    activate_query = MagicMock()
    activate_query.filter.return_value.all.return_value = [mock_experiment]

    complete_query = MagicMock()
    complete_query.filter.return_value.all.return_value = []

    # Set up the mock db to return different query objects
    mock_db_session.query.side_effect = [activate_query, complete_query]

    # Patch SessionLocal to return our mock session
    with patch("backend.app.core.scheduler.SessionLocal", return_value=mock_db_session):
        # Run the scheduler
        await scheduler.process_scheduled_experiments()

        # Check that the experiment was updated
        assert mock_experiment.status == ExperimentStatus.ACTIVE
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
