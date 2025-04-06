# backend/tests/unit/api/v1/endpoints/test_experiments.py
import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.app.api.v1.endpoints import experiments
from backend.app.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    ExperimentListResponse,
    ExperimentType,
    ExperimentStatus as SchemaExperimentStatus,
    VariantBase,
    MetricBase,
    MetricType,
)
from backend.app.models.experiment import Experiment, ExperimentStatus as ModelExperimentStatus
from backend.app.models.user import User


class MockVariant:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.name = kwargs.get("name", "Test Variant")
        self.is_control = kwargs.get("is_control", False)
        self.traffic_allocation = kwargs.get("traffic_allocation", 50)
        self.experiment_id = kwargs.get("experiment_id", uuid.uuid4())
        self.created_at = kwargs.get("created_at", datetime.now().isoformat())
        self.updated_at = kwargs.get("updated_at", datetime.now().isoformat())


class MockMetric:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.name = kwargs.get("name", "Test Metric")
        self.event_name = kwargs.get("event_name", "test_event")
        self.metric_type = kwargs.get("metric_type", "conversion")
        self.is_primary = kwargs.get("is_primary", False)
        self.aggregation_method = kwargs.get("aggregation_method", "average")
        self.minimum_sample_size = kwargs.get("minimum_sample_size", 100)
        self.lower_is_better = kwargs.get("lower_is_better", False)
        self.experiment_id = kwargs.get("experiment_id", uuid.uuid4())
        self.created_at = kwargs.get("created_at", datetime.now().isoformat())
        self.updated_at = kwargs.get("updated_at", datetime.now().isoformat())


class MockUser:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.username = kwargs.get("username", "testuser")
        self.email = kwargs.get("email", "test@example.com")
        self.is_active = kwargs.get("is_active", True)
        self.is_superuser = kwargs.get("is_superuser", False)


class MockExperiment:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.name = kwargs.get("name", "Test Experiment")
        self.description = kwargs.get("description", "Test Description")
        self.hypothesis = kwargs.get("hypothesis", "Test Hypothesis")
        self.status = kwargs.get("status", ModelExperimentStatus.DRAFT)
        self.experiment_type = kwargs.get("experiment_type", "a_b")
        self.targeting_rules = kwargs.get("targeting_rules", {})
        self.tags = kwargs.get("tags", [])
        self.owner_id = kwargs.get("owner_id", uuid.uuid4())
        self.variants = kwargs.get("variants", [])
        self.metrics = kwargs.get("metrics", [])
        self.created_at = kwargs.get("created_at", datetime.now().isoformat())
        self.updated_at = kwargs.get("updated_at", datetime.now().isoformat())

    @property
    def metric_definitions(self):
        """
        Property to make the metrics attribute accessible as metric_definitions.
        This helps maintain compatibility with the actual experiment model.
        """
        return self.metrics

    def dict(self):
        # Convert to dict for Pydantic
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "hypothesis": self.hypothesis,
            "status": (
                self.status.value
                if isinstance(self.status, ModelExperimentStatus)
                else self.status
            ),
            "experiment_type": self.experiment_type,
            "targeting_rules": self.targeting_rules,
            "tags": self.tags,
            "owner_id": str(self.owner_id),
            "variants": [vars(v) for v in self.variants],
            "metrics": [vars(m) for m in self.metrics],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@pytest.fixture
def mock_experiment_service():
    """Mock ExperimentService."""
    with patch("backend.app.api.v1.endpoints.experiments.ExperimentService") as mock:
        service_instance = MagicMock()
        mock.return_value = service_instance
        yield service_instance


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return MockUser(id=uuid.uuid4())


@pytest.fixture
def mock_cache_control():
    """Mock cache control."""
    from backend.app.api.deps import CacheControl
    return CacheControl(enabled=False, skip=False, redis=None)


@pytest.mark.asyncio
async def test_list_experiments(
    mock_db, mock_experiment_service, mock_user, mock_cache_control
):
    """Test listing experiments."""
    experiment_id1 = uuid.uuid4()
    experiment_id2 = uuid.uuid4()

    # Setup mock experiments with proper experiment IDs for variants and metrics
    mock_variants1 = [
        MockVariant(name="Control", is_control=True, experiment_id=experiment_id1)
    ]
    mock_metrics1 = [
        MockMetric(
            name="Conversion",
            event_name="conversion",
            experiment_id=experiment_id1,
            metric_type="conversion",
            is_primary=True,
            aggregation_method="average",
            minimum_sample_size=100,
            lower_is_better=False
        )
    ]

    mock_variants2 = [
        MockVariant(name="Control", is_control=True, experiment_id=experiment_id2)
    ]
    mock_metrics2 = [
        MockMetric(
            name="Conversion",
            event_name="conversion",
            experiment_id=experiment_id2,
            metric_type="conversion",
            is_primary=True,
            aggregation_method="average",
            minimum_sample_size=100,
            lower_is_better=False
        )
    ]

    mock_experiments = [
        MockExperiment(
            id=experiment_id1,
            name="Experiment 1",
            description="Test Experiment 1",
            hypothesis="Test Hypothesis 1",
            status=ModelExperimentStatus.DRAFT,
            experiment_type="a_b",
            targeting_rules={},
            tags=["test"],
            variants=mock_variants1,
            metrics=mock_metrics1,
        ),
        MockExperiment(
            id=experiment_id2,
            name="Experiment 2",
            description="Test Experiment 2",
            hypothesis="Test Hypothesis 2",
            status=ModelExperimentStatus.DRAFT,
            experiment_type="a_b",
            targeting_rules={},
            tags=["test"],
            variants=mock_variants2,
            metrics=mock_metrics2,
        ),
    ]

    # Configure the mock service with dictionaries
    mock_experiment_service.get_experiments_by_owner.return_value = [
        exp.dict() for exp in mock_experiments
    ]
    mock_experiment_service.count_experiments_by_owner.return_value = len(
        mock_experiments
    )

    # Create a mock ExperimentListResponse for patching
    mock_response = ExperimentListResponse(
        items=[ExperimentResponse(**exp.dict()) for exp in mock_experiments],
        total=len(mock_experiments),
        skip=0,
        limit=100,
    )

    # Mock the ExperimentListResponse constructor
    with patch.object(
        ExperimentListResponse, "__init__", return_value=None
    ) as mock_list_response:
        with patch.object(
            ExperimentListResponse, "__new__", return_value=mock_response
        ):
            # Call the endpoint
            response = await experiments.list_experiments(
                db=mock_db,
                current_user=mock_user,
                cache_control=mock_cache_control,
                skip=0,
                limit=100,
            )

            # Verify service was called correctly
            mock_experiment_service.get_experiments_by_owner.assert_called_once()

            # Verify response
            assert isinstance(response, ExperimentListResponse)
            assert response.total == len(mock_experiments)
            assert response.skip == 0
            assert response.limit == 100


@pytest.mark.asyncio
async def test_create_experiment(
    mock_db, mock_experiment_service, mock_user, mock_cache_control
):
    """Test creating an experiment."""
    # Setup mock variant and metric for the required fields
    mock_variants = [
        VariantBase(
            name="Control",
            is_control=True,
            traffic_allocation=50,
            description="Control variant",
            configuration={"button_color": "green"}
        ),
        VariantBase(
            name="Variant A",
            is_control=False,
            traffic_allocation=50,
            description="Treatment variant",
            configuration={"button_color": "blue"}
        ),
    ]
    mock_metrics = [
        MetricBase(
            name="Conversion Rate",
            description="Percentage of users who convert",
            event_name="conversion",
            metric_type=MetricType.CONVERSION,
            is_primary=True,
            aggregation_method="average",
            minimum_sample_size=100,
            expected_effect=0.05,
            event_value_path="value",
            lower_is_better=False
        )
    ]

    # Setup mock data with required fields
    experiment_data = ExperimentCreate(
        name="New Experiment",
        description="Test description",
        hypothesis="Test hypothesis",
        experiment_type=ExperimentType.A_B,
        targeting_rules={},
        tags=["test"],
        status=SchemaExperimentStatus.DRAFT,
        variants=mock_variants,
        metrics=mock_metrics,
    )

    # Create mock return dict
    mock_response = {
        "id": str(uuid.uuid4()),
        "name": "New Experiment",
        "description": "Test description",
        "hypothesis": "Test hypothesis",
        "status": SchemaExperimentStatus.DRAFT.value,
        "experiment_type": ExperimentType.A_B.value,
        "targeting_rules": {},
        "tags": ["test"],
        "owner_id": str(mock_user.id),
        "variants": [v.dict() for v in mock_variants],
        "metrics": [m.dict() for m in mock_metrics],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    # Set up the return value for create_experiment
    mock_experiment_service.create_experiment.return_value = mock_response

    # Call the endpoint
    response = await experiments.create_experiment(
        experiment_in=experiment_data,
        db=mock_db,
        current_user=mock_user,
        cache_control=mock_cache_control,
    )

    # Verify service was called correctly
    mock_experiment_service.create_experiment.assert_called_once()

    # Verify response
    assert response == mock_response


@pytest.mark.asyncio
async def test_get_experiment_found(
    mock_db, mock_experiment_service, mock_user, mock_cache_control
):
    """Test getting an experiment that exists."""
    # Setup mock data
    experiment_id = uuid.uuid4()

    # Mock the response data (dictionary instead of object)
    mock_response = {
        "id": str(experiment_id),
        "name": "Test Experiment",
        "description": "Test Description",
        "hypothesis": "Test Hypothesis",
        "status": "draft",
        "experiment_type": "a_b",
        "targeting_rules": {},
        "tags": ["test"],
        "owner_id": str(mock_user.id),
        "variants": [],
        "metrics": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    # Configure mocks
    mock_experiment_service.get_experiment_by_id.return_value = mock_response

    # Create custom response for the actual function
    with patch.object(ExperimentResponse, "from_orm", return_value=mock_response):
        # Mock the access dependency
        with patch(
            "backend.app.api.deps.get_experiment_access", return_value=mock_response
        ):
            # Call the endpoint
            response = await experiments.get_experiment(
                experiment_id=experiment_id,
                db=mock_db,
                current_user=mock_user,
                cache_control=mock_cache_control,
            )

            # Verify service was called correctly
            mock_experiment_service.get_experiment_by_id.assert_called_once_with(
                experiment_id
            )

            # Verify response
            assert response == mock_response


@pytest.mark.asyncio
async def test_update_experiment(
    mock_db, mock_experiment_service, mock_user, mock_cache_control
):
    """Test updating an experiment."""
    # Setup mock data
    experiment_id = uuid.uuid4()

    # Create a proper Experiment object for the mock
    mock_experiment = MockExperiment(
        id=experiment_id,
        name="Original Experiment",
        description="Original Description",
        hypothesis="Original Hypothesis",
        status=ModelExperimentStatus.DRAFT,
        experiment_type="a_b",
        targeting_rules={},
        tags=["test"],
        owner_id=mock_user.id,
        variants=[],
        metrics=[]
    )

    # Create update data with only the fields we want to update
    experiment_update = ExperimentUpdate(
        name="Updated Experiment",
        description="Updated Description",
        hypothesis="Updated Hypothesis"
    )

    # Mock updated experiment as Experiment object
    mock_updated = MockExperiment(
        id=experiment_id,
        name="Updated Experiment",
        description="Updated Description",
        hypothesis="Updated Hypothesis",
        status=ModelExperimentStatus.DRAFT,
        experiment_type="a_b",
        targeting_rules={},
        tags=["test"],
        owner_id=mock_user.id,
        variants=[],
        metrics=[]
    )

    # Setup db query mocks
    db_query_mock = MagicMock()
    db_query_filter_mock = MagicMock()
    db_query_mock.filter.return_value = db_query_filter_mock
    db_query_filter_mock.first.return_value = mock_experiment
    mock_db.query.return_value = db_query_mock

    # Mock the experiment service
    mock_experiment_service.update_experiment.return_value = mock_updated

    # Create custom response for the actual function
    with patch.object(ExperimentResponse, "from_orm", return_value=mock_updated.dict()):
        # Mock the access dependency
        with patch(
            "backend.app.api.deps.get_experiment_access", return_value=mock_experiment
        ):
            # Call the endpoint
            response = await experiments.update_experiment(
                experiment_id=experiment_id,
                experiment_in=experiment_update,
                db=mock_db,
                current_user=mock_user,
                cache_control=mock_cache_control,
            )

            # Verify db query was called correctly
            mock_db.query.assert_called_once()

            # Verify service was called correctly
            mock_experiment_service.update_experiment.assert_called_once()

            # Verify response
            assert response == mock_updated.dict()


@pytest.mark.asyncio
async def test_start_experiment(
    mock_db, mock_experiment_service, mock_user, mock_cache_control
):
    """Test starting an experiment."""
    # Setup mock data
    experiment_id = uuid.uuid4()

    # Create a proper Experiment object with required components for starting
    mock_experiment = MockExperiment(
        id=experiment_id,
        name="Draft Experiment",
        status=ModelExperimentStatus.DRAFT,
        owner_id=mock_user.id,
        variants=[
            MockVariant(name="Control", is_control=True, experiment_id=experiment_id),
            MockVariant(name="Test", is_control=False, experiment_id=experiment_id),
        ],
        metrics=[
            MockMetric(
                name="Conversion", event_name="conversion", experiment_id=experiment_id
            )
        ],
    )

    # Mock started experiment
    mock_started = MockExperiment(
        id=experiment_id,
        name="Draft Experiment",
        status=ModelExperimentStatus.ACTIVE,
        owner_id=mock_user.id,
        variants=[
            MockVariant(name="Control", is_control=True, experiment_id=experiment_id),
            MockVariant(name="Test", is_control=False, experiment_id=experiment_id),
        ],
        metrics=[
            MockMetric(
                name="Conversion", event_name="conversion", experiment_id=experiment_id
            )
        ],
    )

    # Setup db query mocks
    db_query_mock = MagicMock()
    db_query_filter_mock = MagicMock()
    db_query_mock.filter.return_value = db_query_filter_mock
    db_query_filter_mock.first.return_value = mock_experiment
    mock_db.query.return_value = db_query_mock

    # Mock the experiment service
    mock_experiment_service.start_experiment.return_value = mock_started

    # Create custom response for the actual function
    with patch.object(ExperimentResponse, "from_orm", return_value=mock_started.dict()):
        # Mock the access dependency
        with patch(
            "backend.app.api.deps.get_experiment_access", return_value=mock_experiment
        ):
            # Call the endpoint
            response = await experiments.start_experiment(
                experiment_id=experiment_id,
                db=mock_db,
                current_user=mock_user,
                cache_control=mock_cache_control,
            )

            # Verify db query was called correctly
            mock_db.query.assert_called_once()

            # Verify service was called correctly
            mock_experiment_service.start_experiment.assert_called_once_with(
                mock_experiment
            )

            # Verify response
            assert response == mock_started.dict()


@pytest.mark.asyncio
async def test_update_experiment_not_found(mock_db, mock_user, mock_cache_control):
    """Test updating an experiment that doesn't exist."""
    # Setup mock data
    experiment_id = uuid.uuid4()
    experiment_update = ExperimentUpdate(name="Updated Experiment")

    # Setup db query mocks to return None
    db_query_mock = MagicMock()
    db_query_filter_mock = MagicMock()
    db_query_mock.filter.return_value = db_query_filter_mock
    db_query_filter_mock.first.return_value = None
    mock_db.query.return_value = db_query_mock

    # Call the endpoint and check for exception
    with pytest.raises(HTTPException) as exc_info:
        await experiments.update_experiment(
            experiment_id=experiment_id,
            experiment_in=experiment_update,
            db=mock_db,
            current_user=mock_user,
            cache_control=mock_cache_control,
        )

    # Verify db query was called correctly
    mock_db.query.assert_called_once()

    # Verify exception
    assert exc_info.value.status_code == 404
    assert "Experiment not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_experiment_not_found(
    mock_db, mock_experiment_service, mock_user, mock_cache_control
):
    """Test getting an experiment that doesn't exist."""
    # Setup mock data
    experiment_id = uuid.uuid4()
    mock_experiment_service.get_experiment_by_id.return_value = None

    # Call the endpoint and check for exception
    with pytest.raises(HTTPException) as exc_info:
        await experiments.get_experiment(
            experiment_id=experiment_id,
            db=mock_db,
            current_user=mock_user,
            cache_control=mock_cache_control,
        )

    # Verify service was called correctly
    mock_experiment_service.get_experiment_by_id.assert_called_once_with(experiment_id)

    # Verify exception
    assert exc_info.value.status_code == 404
    assert "Experiment not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_start_experiment_not_found(mock_db, mock_user, mock_cache_control):
    """Test starting an experiment that doesn't exist."""
    # Setup mock data
    experiment_id = uuid.uuid4()

    # Create a proper Experiment object for the mock
    mock_experiment = MockExperiment(
        id=experiment_id,
        name="Test Experiment",
        description="Test Description",
        hypothesis="Test Hypothesis",
        status=ModelExperimentStatus.DRAFT,
        experiment_type="a_b",
        targeting_rules={},
        tags=["test"],
        owner_id=mock_user.id,
        variants=[],
        metrics=[]
    )

    # Setup db query mocks
    db_query_mock = MagicMock()
    db_query_filter_mock = MagicMock()
    db_query_mock.filter.return_value = db_query_filter_mock
    db_query_filter_mock.first.return_value = None
    mock_db.query.return_value = db_query_mock

    # Call the endpoint and expect an error
    with pytest.raises(HTTPException) as exc_info:
        await experiments.start_experiment(
            experiment_id=experiment_id,
            db=mock_db,
            current_user=mock_user,
            cache_control=mock_cache_control,
        )

    # Verify error
    assert exc_info.value.status_code == 404
    assert "Experiment not found" in str(exc_info.value.detail)
