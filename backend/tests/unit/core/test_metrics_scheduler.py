"""Unit tests for metrics scheduler."""
import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, AsyncMock, call

from backend.app.core.metrics_scheduler import MetricsScheduler
from backend.app.models.metrics.metric import AggregationPeriod


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    return MagicMock()


@pytest.fixture
def scheduler():
    """Create a metrics scheduler for testing."""
    scheduler = MetricsScheduler(interval_minutes=5)
    return scheduler


@pytest.mark.asyncio
async def test_scheduler_start_stop(scheduler):
    """Test that scheduler can be started and stopped correctly."""
    # Test starting the scheduler
    with patch("asyncio.create_task") as mock_create_task:
        mock_task = AsyncMock()
        mock_create_task.return_value = mock_task

        await scheduler.start()

        # Verify the scheduler is running
        assert scheduler.is_running is True
        assert scheduler.task is mock_task
        mock_create_task.assert_called_once()

    # Test starting the scheduler when it's already running
    with patch("asyncio.create_task") as mock_create_task:
        await scheduler.start()

        # Verify create_task was not called again
        mock_create_task.assert_not_called()

    # Test stopping the scheduler
    # Use patch to prevent awaiting AsyncMock directly
    with patch.object(scheduler, 'task') as mock_task:
        await scheduler.stop()

        # Verify the scheduler is stopped
        assert scheduler.is_running is False
        assert mock_task.cancel.called


@pytest.mark.skip(reason="This test is flaky and needs to be refactored")
@pytest.mark.asyncio
async def test_scheduler_run_scheduler(scheduler):
    """Test the scheduler loop runs and handles exceptions."""
    # Mock the aggregate_metrics method to track calls
    with patch.object(scheduler, "aggregate_metrics") as mock_aggregate:
        # Create a future that's already cancelled
        cancelled_future = asyncio.Future()
        cancelled_future.set_exception(asyncio.CancelledError())

        # Mock sleep to return None first, then return the cancelled future
        with patch("asyncio.sleep", side_effect=[None, cancelled_future]):
            mock_aggregate.return_value = None

            # Set scheduler to running
            scheduler.is_running = True

            # This should run until CancelledError is raised by the mocked sleep
            with pytest.raises(asyncio.CancelledError):
                await scheduler._run_scheduler()

            # Verify aggregate_metrics was called once
            mock_aggregate.assert_called_once()

    # Test error handling in the scheduler loop
    with patch.object(scheduler, "aggregate_metrics") as mock_aggregate:
        # Create a future that's already cancelled
        cancelled_future = asyncio.Future()
        cancelled_future.set_exception(asyncio.CancelledError())

        # Mock sleep to return None first, then return the cancelled future
        with patch("asyncio.sleep", side_effect=[None, cancelled_future]):
            # Make aggregate_metrics raise an exception
            mock_aggregate.side_effect = Exception("Test exception")

            # Set scheduler to running
            scheduler.is_running = True

            # This should catch the exception from aggregate_metrics and continue
            with pytest.raises(asyncio.CancelledError):
                await scheduler._run_scheduler()

            # Verify aggregate_metrics was called once
            mock_aggregate.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_aggregate_metrics(scheduler, mock_db_session):
    """Test that scheduler aggregates metrics for different time periods."""
    # Create current time for testing
    current_time = datetime.now(timezone.utc)

    # Mock MetricsService to track calls to aggregate_metrics
    with patch("backend.app.core.metrics_scheduler.MetricsService") as mock_service:
        # Configure mock to return different counts for different aggregation periods
        mock_service.aggregate_metrics.side_effect = [10, 20, 30, 40, 50, 60]

        # Mock SessionLocal to return our mock session
        with patch("backend.app.core.metrics_scheduler.SessionLocal", return_value=mock_db_session):
            # Mock datetime.now to return a consistent time
            with patch("backend.app.core.metrics_scheduler.datetime") as mock_datetime:
                mock_datetime.now.return_value = current_time
                # Pass through other datetime methods
                mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

                # Run the aggregation
                await scheduler.aggregate_metrics()

                # Check that MetricsService.aggregate_metrics was called for each period
                assert mock_service.aggregate_metrics.call_count == 6

                # Verify the calls with expected parameters
                expected_calls = [
                    # Minute aggregation for the last hour
                    call(
                        db=mock_db_session,
                        period=AggregationPeriod.MINUTE,
                        start_time=current_time - timedelta(hours=1),
                        end_time=current_time
                    ),
                    # Hourly aggregation for the last day
                    call(
                        db=mock_db_session,
                        period=AggregationPeriod.HOUR,
                        start_time=current_time - timedelta(days=1),
                        end_time=current_time
                    ),
                    # Daily aggregation for the last month
                    call(
                        db=mock_db_session,
                        period=AggregationPeriod.DAY,
                        start_time=current_time - timedelta(days=30),
                        end_time=current_time
                    ),
                    # Weekly aggregation for the last year
                    call(
                        db=mock_db_session,
                        period=AggregationPeriod.WEEK,
                        start_time=current_time - timedelta(days=365),
                        end_time=current_time
                    ),
                    # Monthly aggregation for all time
                    call(
                        db=mock_db_session,
                        period=AggregationPeriod.MONTH,
                        start_time=None,
                        end_time=current_time
                    ),
                    # Total aggregation (single record for all time)
                    call(
                        db=mock_db_session,
                        period=AggregationPeriod.TOTAL,
                        start_time=None,
                        end_time=current_time
                    ),
                ]
                mock_service.aggregate_metrics.assert_has_calls(expected_calls)

                # Verify the session was closed
                assert mock_db_session.close.called


@pytest.mark.asyncio
async def test_scheduler_aggregate_metrics_exception(scheduler, mock_db_session):
    """Test that scheduler handles exceptions during metrics aggregation."""
    # Mock MetricsService to raise an exception
    with patch("backend.app.core.metrics_scheduler.MetricsService") as mock_service:
        mock_service.aggregate_metrics.side_effect = Exception("Test aggregation exception")

        # Mock SessionLocal to return our mock session
        with patch("backend.app.core.metrics_scheduler.SessionLocal", return_value=mock_db_session):
            # Run the aggregation - should not raise an exception
            await scheduler.aggregate_metrics()

            # Verify the session was closed despite the exception
            assert mock_db_session.close.called


@pytest.mark.asyncio
async def test_scheduler_aggregate_metrics_partial_failure(scheduler, mock_db_session):
    """Test that scheduler continues processing when some aggregation periods fail."""
    # Mock MetricsService to succeed for some periods and fail for others
    with patch("backend.app.core.metrics_scheduler.MetricsService") as mock_service:
        mock_service.aggregate_metrics.side_effect = [
            10,  # MINUTE succeeds
            Exception("Hour aggregation failed"),  # HOUR fails
            30,  # DAY succeeds
            Exception("Week aggregation failed"),  # WEEK fails
            50,  # MONTH succeeds
            60,  # TOTAL succeeds
        ]

        # Mock SessionLocal to return our mock session
        with patch("backend.app.core.metrics_scheduler.SessionLocal", return_value=mock_db_session):
            # Run the aggregation
            await scheduler.aggregate_metrics()

            # Verify all periods were attempted despite some failures
            assert mock_service.aggregate_metrics.call_count == 6

            # Verify the session was closed
            assert mock_db_session.close.called
