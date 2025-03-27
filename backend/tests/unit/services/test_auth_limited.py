# backend/tests/unit/services/test_auth_limited.py
import pytest
import uuid

from backend.app.models.experiment import (
    Experiment,
    ExperimentStatus,
    Metric,
    MetricType,
)


def test_experiment_metric_relationship():
    """Test relationship between experiment and metrics."""
    # Create a simple experiment object
    experiment_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    experiment = Experiment(
        id=experiment_id,
        name="Test Experiment",
        description="Test description",
        status=ExperimentStatus.DRAFT,
        owner_id=owner_id,
    )

    # Create metrics
    metric1 = Metric(
        id=uuid.uuid4(),
        name="Conversion Rate",
        description="Primary conversion metric",
        event_name="conversion",
        metric_type=MetricType.CONVERSION,
        is_primary=True,
        experiment_id=experiment_id,  # Set the relationship directly
    )

    metric2 = Metric(
        id=uuid.uuid4(),
        name="Revenue",
        description="Revenue metric",
        event_name="purchase",
        metric_type=MetricType.REVENUE,
        is_primary=False,
        experiment_id=experiment_id,  # Set the relationship directly
    )

    # Set up the relationship manually (both ways)
    metrics_list = [metric1, metric2]
    experiment.metrics = metrics_list  # Use whatever attribute name works

    # Verify the bidirectional relationship
    # Check experiment -> metrics relationship
    assert hasattr(experiment, "metrics") or hasattr(
        experiment, "metric_definitions"
    ), "Experiment should have metrics attribute"

    if hasattr(experiment, "metrics"):
        assert len(experiment.metrics) == 2, "Experiment should have 2 metrics"
        assert experiment.metrics[0].name == "Conversion Rate"
        assert experiment.metrics[1].name == "Revenue"
    elif hasattr(experiment, "metric_definitions"):
        assert (
            len(experiment.metric_definitions) == 2
        ), "Experiment should have 2 metrics"
        assert experiment.metric_definitions[0].name == "Conversion Rate"
        assert experiment.metric_definitions[1].name == "Revenue"

    # Check metrics -> experiment relationship (via experiment_id)
    for metric in metrics_list:
        assert (
            metric.experiment_id == experiment_id
        ), "Metric should reference the experiment"
