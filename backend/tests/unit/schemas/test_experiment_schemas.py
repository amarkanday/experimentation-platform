"""
Test Experiment Schemas.

This module contains tests for the Pydantic v2 experiment schema validation.
"""

import pytest
from datetime import datetime
import uuid

from backend.app.schemas.experiment_schemas import (
    ExperimentBase,
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentInDB,
    ExperimentResponse,
    ExperimentSimple,
    ExperimentListResponse
)


class TestExperimentSchemasValidation:
    """Tests for experiment schemas with Pydantic v2 patterns."""

    def test_experiment_base(self):
        """Test ExperimentBase schema."""
        data = {
            "key": "test-experiment",
            "name": "Test Experiment",
            "description": "This is a test experiment",
            "is_active": True
        }
        experiment = ExperimentBase(**data)

        assert experiment.key == "test-experiment"
        assert experiment.name == "Test Experiment"
        assert experiment.description == "This is a test experiment"
        assert experiment.is_active is True

    def test_experiment_create(self):
        """Test ExperimentCreate schema."""
        data = {
            "key": "test-experiment",
            "name": "Test Experiment",
            "description": "This is a test experiment",
            "is_active": True
        }
        experiment = ExperimentCreate(**data)

        assert experiment.key == "test-experiment"
        assert experiment.name == "Test Experiment"
        assert experiment.description == "This is a test experiment"
        assert experiment.is_active is True

    def test_experiment_update(self):
        """Test ExperimentUpdate schema."""
        data = {
            "key": "updated-key",
            "name": "Updated Name",
            "is_active": False
        }
        experiment = ExperimentUpdate(**data)

        assert experiment.key == "updated-key"
        assert experiment.name == "Updated Name"
        assert experiment.description is None
        assert experiment.is_active is False

    def test_experiment_in_db(self):
        """Test ExperimentInDB schema with Pydantic v2 from_attributes."""
        current_time = datetime.now()
        experiment_id = uuid.uuid4()
        user_id = uuid.uuid4()

        data = {
            "id": experiment_id,
            "user_id": user_id,
            "key": "test-experiment",
            "name": "Test Experiment",
            "description": "This is a test experiment",
            "is_active": True,
            "created_at": current_time,
            "updated_at": current_time
        }

        experiment = ExperimentInDB(**data)

        assert experiment.id == experiment_id
        assert experiment.user_id == user_id
        assert experiment.key == "test-experiment"
        assert experiment.name == "Test Experiment"
        assert experiment.created_at == current_time
        assert experiment.updated_at == current_time

        # Test Pydantic v2 model_config
        assert hasattr(ExperimentInDB, "model_config")
        assert ExperimentInDB.model_config.get("from_attributes") is True

    def test_experiment_simple(self):
        """Test ExperimentSimple schema with Pydantic v2 from_attributes."""
        experiment_id = uuid.uuid4()

        data = {
            "id": experiment_id,
            "key": "test-experiment",
            "name": "Test Experiment",
            "is_active": True
        }

        experiment = ExperimentSimple(**data)

        assert experiment.id == experiment_id
        assert experiment.key == "test-experiment"
        assert experiment.name == "Test Experiment"
        assert experiment.is_active is True

        # Test Pydantic v2 model_config
        assert hasattr(ExperimentSimple, "model_config")
        assert ExperimentSimple.model_config.get("from_attributes") is True

    def test_experiment_list_response(self):
        """Test ExperimentListResponse schema."""
        experiment_id = uuid.uuid4()

        data = {
            "experiments": [
                {
                    "id": experiment_id,
                    "key": "test-experiment",
                    "name": "Test Experiment",
                    "is_active": True
                }
            ],
            "total": 1
        }

        response = ExperimentListResponse(**data)

        assert len(response.experiments) == 1
        assert response.experiments[0].id == experiment_id
        assert response.experiments[0].key == "test-experiment"
        assert response.total == 1
