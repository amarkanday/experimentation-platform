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
        key_id = uuid.uuid4()
        user_id = uuid.uuid4()
        current_time = datetime.now()

        data = {
            "id": key_id,
            "user_id": user_id,
            "name": "Test API Key",
            "prefix": "test_prefix",
            "created_at": current_time,
            "last_used": None,
            "expires_at": current_time.replace(year=current_time.year + 1)
        }

        api_key = APIKeyResponse(**data)

        assert api_key.id == key_id
        assert api_key.user_id == user_id
        assert api_key.name == "Test API Key"
        assert api_key.prefix == "test_prefix"
        assert api_key.created_at == current_time
        assert api_key.last_used is None
        assert api_key.expires_at == data["expires_at"]

        # Test Pydantic v2 model_config
        assert hasattr(APIKeyResponse, "model_config")
        assert APIKeyResponse.model_config.get("from_attributes") is True

    def test_api_key_list(self):
        """Test APIKeyList schema with Pydantic v2 from_attributes."""
        key_id = uuid.uuid4()
        user_id = uuid.uuid4()
        current_time = datetime.now()

        key_data = {
            "id": key_id,
            "user_id": user_id,
            "name": "Test API Key",
            "prefix": "test_prefix",
            "created_at": current_time,
            "last_used": None,
            "expires_at": current_time.replace(year=current_time.year + 1)
        }

        data = {
            "items": [key_data],
            "total": 1
        }

        api_key_list = APIKeyList(**data)

        assert len(api_key_list.items) == 1
        assert api_key_list.items[0].id == key_id
        assert api_key_list.items[0].name == "Test API Key"
        assert api_key_list.total == 1

        # Test Pydantic v2 model_config
        assert hasattr(APIKeyList, "model_config")
        assert APIKeyList.model_config.get("from_attributes") is True
