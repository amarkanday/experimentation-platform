import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.app.models.experiment import Experiment, ExperimentStatus
from backend.app.services.experiment_service import ExperimentService
from backend.app.schemas.experiment import ScheduleConfig


@pytest.fixture
def experiment_service(db_session):
    """Create experiment service for testing."""
    return ExperimentService(db_session)


@pytest.fixture
def draft_experiment(db_session):
    """Create a draft experiment for testing."""
    experiment = Experiment(
        id=uuid4(),
        name="Test Experiment",
        status=ExperimentStatus.DRAFT,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(experiment)
    db_session.commit()
    return experiment


class TestExperimentScheduling:
    """Tests for experiment scheduling functionality."""

    def test_update_experiment_schedule_valid(self, experiment_service, draft_experiment):
        """Test updating experiment schedule with valid data."""
        # Set up test data
        start_date = datetime.now(timezone.utc) + timedelta(days=1)
        end_date = start_date + timedelta(days=7)
        schedule = {
            "start_date": start_date,
            "end_date": end_date,
            "time_zone": "UTC"
        }

        # Update schedule
        updated_experiment = experiment_service.update_experiment_schedule(
            draft_experiment, schedule
        )

        # Assert results
        assert "id" in updated_experiment
        assert updated_experiment["start_date"] is not None
        assert updated_experiment["end_date"] is not None

        # Verify experiment was updated in the database
        assert draft_experiment.start_date.replace(tzinfo=timezone.utc) == start_date
        assert draft_experiment.end_date.replace(tzinfo=timezone.utc) == end_date

    def test_update_experiment_schedule_custom_timezone(self, experiment_service, draft_experiment):
        """Test updating experiment schedule with custom timezone."""
        # Set up test data
        start_date = datetime.now(timezone.utc) + timedelta(days=1)
        end_date = start_date + timedelta(days=7)
        schedule = {
            "start_date": start_date,
            "end_date": end_date,
            "time_zone": "America/New_York"
        }

        # Set metadata to empty dictionary
        draft_experiment.metadata = {}

        # Update schedule
        updated_experiment = experiment_service.update_experiment_schedule(
            draft_experiment, schedule
        )

        # Assert results
        assert draft_experiment.start_date.replace(tzinfo=timezone.utc) == start_date
        assert draft_experiment.end_date.replace(tzinfo=timezone.utc) == end_date
        assert draft_experiment.metadata is not None
        assert "time_zone" in draft_experiment.metadata
        assert draft_experiment.metadata["time_zone"] == "America/New_York"

    def test_update_experiment_schedule_invalid_dates(self, experiment_service, draft_experiment):
        """Test updating experiment schedule with invalid dates."""
        # Set up test data with end date before start date
        start_date = datetime.now(timezone.utc) + timedelta(days=2)
        end_date = datetime.now(timezone.utc) + timedelta(days=1)
        schedule = {
            "start_date": start_date,
            "end_date": end_date,
            "time_zone": "UTC"
        }

        # Update schedule should fail
        with pytest.raises(ValueError) as exc_info:
            experiment_service.update_experiment_schedule(draft_experiment, schedule)

        assert "End date must be after start date" in str(exc_info.value)

    def test_update_experiment_schedule_active_experiment(self, experiment_service, draft_experiment, db_session):
        """Test updating schedule for an active experiment which should fail."""
        # Set experiment to active
        draft_experiment.status = ExperimentStatus.ACTIVE
        db_session.commit()

        schedule = {
            "start_date": datetime.now(timezone.utc) + timedelta(days=1),
            "end_date": datetime.now(timezone.utc) + timedelta(days=7),
            "time_zone": "UTC"
        }

        # Update schedule should fail
        with pytest.raises(ValueError) as exc_info:
            experiment_service.update_experiment_schedule(draft_experiment, schedule)

        assert "Cannot schedule experiment with status" in str(exc_info.value)
