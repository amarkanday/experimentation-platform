"""
Test API Key Schemas.

This module contains tests for the Pydantic v2 API key schema validation.
"""

import pytest
from datetime import datetime
import uuid

from backend.app.routers.api_key_routes import (
    APIKeyResponse,
    APIKeyList
)


class TestAPIKeySchemasValidation:
    """Tests for API key schemas with Pydantic v2 patterns."""

    def test_api_key_response(self):
        """Test APIKeyResponse schema with Pydantic v2 from_attributes."""
        key_id = str(uuid.uuid4())
        current_time = datetime.now()

        data = {
            "id": key_id,
            "key": "test_key_12345",
            "name": "Test API Key",
            "description": "Test description",
            "scopes": "read:data write:data",
            "is_active": True,
            "expires_at": current_time.replace(year=current_time.year + 1),
            "created_at": current_time,
            "updated_at": current_time
        }

        api_key = APIKeyResponse(**data)

        assert api_key.id == key_id
        assert api_key.key == "test_key_12345"
        assert api_key.name == "Test API Key"
        assert api_key.description == "Test description"
        assert api_key.scopes == "read:data write:data"
        assert api_key.is_active is True
        assert api_key.created_at == current_time
        assert api_key.updated_at == current_time
        assert api_key.expires_at == data["expires_at"]

        # Test Pydantic v2 model_config
        assert hasattr(APIKeyResponse, "model_config")
        assert APIKeyResponse.model_config.get("from_attributes") is True

    def test_api_key_list(self):
        """Test APIKeyList schema with Pydantic v2 from_attributes."""
        key_id = str(uuid.uuid4())
        current_time = datetime.now()

        data = {
            "id": key_id,
            "name": "Test API Key",
            "description": "Test description",
            "scopes": "read:data write:data",
            "is_active": True,
            "expires_at": current_time.replace(year=current_time.year + 1),
            "created_at": current_time,
            "updated_at": current_time
        }

        api_key_list = APIKeyList(**data)

        assert api_key_list.id == key_id
        assert api_key_list.name == "Test API Key"
        assert api_key_list.description == "Test description"
        assert api_key_list.scopes == "read:data write:data"
        assert api_key_list.is_active is True
        assert api_key_list.created_at == current_time
        assert api_key_list.updated_at == current_time
        assert api_key_list.expires_at == data["expires_at"]

        # Test Pydantic v2 model_config
        assert hasattr(APIKeyList, "model_config")
        assert APIKeyList.model_config.get("from_attributes") is True
