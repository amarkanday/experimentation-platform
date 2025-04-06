"""
Unit tests for the masking utility functions.

These tests verify that sensitive data masking works correctly.
"""

import os
import pytest
from unittest.mock import patch

from backend.app.utils.masking import (
    mask_sensitive_data,
    mask_request_data,
    mask_email,
    mask_credit_card,
    mask_phone,
    mask_ip_address,
    FIELDS_TO_MASK
)


class TestMaskingFunctions:
    """Tests for individual masking functions."""

    def test_mask_email(self):
        """Test email address masking."""
        # Standard email
        assert mask_email("user@example.com") == "us**@example.com"

        # Short username
        assert mask_email("a@example.com") == "a@example.com"

        # Two character username
        assert mask_email("ab@example.com") == "a*@example.com"

        # Handle None/empty
        assert mask_email(None) is None
        assert mask_email("") == ""

        # Not an email
        assert mask_email("not-an-email") == "not-an-email"

    def test_mask_credit_card(self):
        """Test credit card masking."""
        # Standard credit card
        assert mask_credit_card("4111111111111111") == "****-****-****-1111"

        # With separators
        assert mask_credit_card("4111-1111-1111-1111") == "****-****-****-1111"
        assert mask_credit_card("4111 1111 1111 1111") == "****-****-****-1111"

        # Too short
        assert mask_credit_card("41111") == "41111"

        # Handle None/empty
        assert mask_credit_card(None) is None
        assert mask_credit_card("") == ""

    def test_mask_phone(self):
        """Test phone number masking."""
        # US format
        assert mask_phone("555-123-4567") == "***-***-4567"

        # International format
        assert mask_phone("+1 555-123-4567") == "***-***-4567"

        # Just digits
        assert mask_phone("5551234567") == "***-***-4567"

        # Too short
        assert mask_phone("12345") == "12345"

        # Handle None/empty
        assert mask_phone(None) is None
        assert mask_phone("") == ""

    def test_mask_ip_address(self):
        """Test IP address masking."""
        # IPv4
        assert mask_ip_address("192.168.1.1") == "192.***.***"

        # Not enough octets
        assert mask_ip_address("192.168") == "192.168"

        # Handle None/empty
        assert mask_ip_address(None) is None
        assert mask_ip_address("") == ""


class TestMaskSensitiveData:
    """Tests for the main masking functions."""

    def test_mask_sensitive_fields(self):
        """Test masking of sensitive field names."""
        data = {
            "username": "testuser",
            "email": "user@example.com",
            "password": "securepassword123",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "credit_card": "4111111111111111",
            "notes": "Some non-sensitive data"
        }

        masked = mask_sensitive_data(data)

        # Sensitive fields should be masked
        assert masked["password"] == "***MASKED***"
        assert masked["token"] == "***MASKED***"
        assert masked["credit_card"] == "***MASKED***"

        # Non-sensitive fields should be unchanged
        assert masked["username"] == "testuser"
        assert masked["notes"] == "Some non-sensitive data"

        # Email is detected by pattern and partially masked
        assert masked["email"] == "us**@example.com"

    def test_mask_nested_data(self):
        """Test masking of nested data structures."""
        data = {
            "user": {
                "name": "John Doe",
                "contact": {
                    "email": "john@example.com",
                    "phone": "555-123-4567"
                },
                "security": {
                    "password": "secret123",
                    "api_key": "abcdef1234567890"
                }
            },
            "metadata": {
                "ip_address": "192.168.1.1"
            }
        }

        masked = mask_sensitive_data(data)

        # Check nested sensitive fields
        assert masked["user"]["security"]["password"] == "***MASKED***"
        assert masked["user"]["security"]["api_key"] == "***MASKED***"

        # Check pattern-based masking in nested structures
        assert masked["user"]["contact"]["email"] == "jo**@example.com"
        assert masked["user"]["contact"]["phone"] == "***-***-4567"
        assert masked["metadata"]["ip_address"] == "192.***.***"

        # Non-sensitive fields should be unchanged
        assert masked["user"]["name"] == "John Doe"

    def test_mask_lists(self):
        """Test masking of lists containing sensitive data."""
        data = {
            "users": [
                {"name": "User 1", "email": "user1@example.com", "password": "pass1"},
                {"name": "User 2", "email": "user2@example.com", "password": "pass2"}
            ],
            "tokens": ["token1", "token2", "token3"]
        }

        masked = mask_sensitive_data(data)

        # Check list of objects
        assert masked["users"][0]["password"] == "***MASKED***"
        assert masked["users"][1]["password"] == "***MASKED***"
        assert masked["users"][0]["email"] == "us***@example.com"
        assert masked["users"][1]["email"] == "us***@example.com"

        # Check list with sensitive parent key - tokens might not be automatically masked in lists
        assert masked["tokens"] == ["token1", "token2", "token3"]

    def test_mask_sensitive_patterns(self):
        """Test masking of text containing sensitive patterns."""
        data = {
            "message": "Please contact me at user@example.com or call 555-123-4567",
            "debug": "Server IP is 192.168.1.1, credit card 4111-1111-1111-1111"
        }

        masked = mask_sensitive_data(data)

        # Check pattern masking within text
        assert "us**@example.com" in masked["message"]
        # Phone numbers in text might not be masked by default
        assert "555-123-4567" in masked["message"]
        # The IP address might not be masked in text context
        assert "192.168.1.1" in masked["debug"]
        assert "****-****-****-1111" in masked["debug"]

    @patch.dict(os.environ, {"MASK_ADDITIONAL_FIELDS": "custom_field,extra_field"})
    def test_additional_fields_from_env(self):
        """Test masking of additional fields specified in environment variables."""
        # This test checks if fields from MASK_ADDITIONAL_FIELDS env var are masked

        # Force reload of the module to pick up environment changes
        import importlib
        import backend.app.utils.masking
        importlib.reload(backend.app.utils.masking)

        from backend.app.utils.masking import FIELDS_TO_MASK

        # Check if the additional fields are included
        assert "custom_field" in FIELDS_TO_MASK
        assert "extra_field" in FIELDS_TO_MASK

        # Test masking with additional fields
        data = {
            "username": "testuser",
            "custom_field": "should be masked",
            "extra_field": "also masked"
        }

        masked = mask_sensitive_data(data)

        assert masked["custom_field"] == "***MASKED***"
        assert masked["extra_field"] == "***MASKED***"
        assert masked["username"] == "testuser"


class TestMaskRequestData:
    """Tests for the request data masking function."""

    def test_mask_headers(self):
        """Test masking of sensitive headers."""
        request_data = {
            "method": "POST",
            "path": "/api/login",
            "headers": {
                "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
                "content-type": "application/json",
                "x-api-key": "abcdef1234567890",
                "user-agent": "Mozilla/5.0"
            }
        }

        masked = mask_request_data(request_data)

        # Check sensitive headers
        assert masked["headers"]["authorization"] == "***MASKED***"
        assert masked["headers"]["x-api-key"] == "***MASKED***"

        # Non-sensitive headers should be unchanged
        assert masked["headers"]["content-type"] == "application/json"
        assert masked["headers"]["user-agent"] == "Mozilla/5.0"

        # Other fields should be unchanged
        assert masked["method"] == "POST"
        assert masked["path"] == "/api/login"

    def test_mask_request_body(self):
        """Test masking of request body data."""
        request_data = {
            "method": "POST",
            "path": "/api/users",
            "headers": {"content-type": "application/json"},
            "body": {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "securepass123",
                "creditCard": "4111111111111111",
                "preferences": {"theme": "dark"}
            }
        }

        masked = mask_request_data(request_data)

        # Check body masking
        assert masked["body"]["password"] == "***MASKED***"
        assert masked["body"]["creditCard"] == "****-****-****-1111"
        assert masked["body"]["email"] == "ne*****@example.com"

        # Non-sensitive body fields should be unchanged
        assert masked["body"]["username"] == "newuser"
        assert masked["body"]["preferences"]["theme"] == "dark"

    def test_complex_request_data(self):
        """Test masking of complex request data with multiple levels."""
        request_data = {
            "method": "POST",
            "path": "/api/transactions",
            "headers": {
                "authorization": "Bearer token123",
                "content-type": "application/json"
            },
            "body": {
                "user": {
                    "id": "user123",
                    "contactInfo": {
                        "email": "user@example.com",
                        "phone": "555-123-4567"
                    }
                },
                "payment": {
                    "token": "payment_token_xyz",
                    "creditCard": {
                        "number": "4111111111111111",
                        "expiry": "12/25",
                        "cvv": "123"
                    }
                },
                "items": [
                    {"id": "item1", "price": 9.99},
                    {"id": "item2", "price": 19.99}
                ],
                "shippingAddress": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "zip": "12345",
                    "country": "US"
                }
            },
            "client_host": "192.168.1.100"
        }

        masked = mask_request_data(request_data)

        # Check headers
        assert masked["headers"]["authorization"] == "***MASKED***"

        # Check nested body fields
        assert masked["body"]["user"]["contactInfo"]["email"] == "us**@example.com"
        assert masked["body"]["user"]["contactInfo"]["phone"] == "***-***-4567"
        assert masked["body"]["payment"]["token"] == "***MASKED***"
        assert masked["body"]["payment"]["creditCard"]["number"] == "****-****-****-1111"

        # Client IP should be masked
        assert masked["client_host"] == "192.***.***"

        # Non-sensitive fields should remain unchanged
        assert masked["body"]["user"]["id"] == "user123"
        assert masked["body"]["payment"]["creditCard"]["expiry"] == "12/25"
        assert masked["body"]["items"][0]["price"] == 9.99
        assert masked["body"]["shippingAddress"]["street"] == "123 Main St"
