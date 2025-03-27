import boto3
import os
import logging
from typing import Dict, Any, Optional  # Add this import line
import pytest

import os
import logging
from unittest.mock import patch, MagicMock

from backend.app.services.auth_service import CognitoAuthService

# Configure logging
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 client for Cognito."""
    with patch("boto3.client") as mock_client:
        # Create mock Cognito client
        cognito_client = MagicMock()
        mock_client.return_value = cognito_client
        yield cognito_client


@pytest.fixture
def auth_service(mock_boto3_client):
    """Create auth service with mocked boto3 client."""
    # Mock environment variables
    with patch.dict(
        os.environ,
        {"COGNITO_USER_POOL_ID": "test-pool-id", "COGNITO_CLIENT_ID": "test-client-id"},
    ):
        service = CognitoAuthService()
        yield service


def test_init_with_environment_vars():
    """Test initialization with environment variables."""
    # Mock environment variables
    with patch.dict(
        os.environ,
        {"COGNITO_USER_POOL_ID": "test-pool-id", "COGNITO_CLIENT_ID": "test-client-id"},
    ):
        with patch("logging.getLogger") as mock_logger:
            service = CognitoAuthService()

            # Verify values were loaded from environment
            assert service.user_pool_id == "test-pool-id"
            assert service.client_id == "test-client-id"

            # Logger should not warn about missing config
            mock_logger.return_value.warning.assert_not_called()


def test_init_without_environment_vars():
    """Test initialization without environment variables."""
    # Remove environment variables
    with patch.dict(os.environ, {}, clear=True):
        # Create a mock logger
        mock_logger = MagicMock()
        # Patch the logger at the module level where CognitoAuthService uses it
        with patch("backend.app.services.auth_service.logger", mock_logger):
            service = CognitoAuthService()

            # Verify warning was logged
            mock_logger.warning.assert_called_once_with(
                "COGNITO_USER_POOL_ID or COGNITO_CLIENT_ID not set"
            )


def test_sign_up_success(auth_service, mock_boto3_client):
    """Test successful user sign up."""
    # Mock Cognito response
    mock_boto3_client.sign_up.return_value = {
        "UserSub": "test-user-id",
        "CodeDeliveryDetails": {
            "Destination": "e***@example.com",
            "DeliveryMedium": "EMAIL",
            "AttributeName": "email",
        },
    }

    # Call sign_up method
    result = auth_service.sign_up(
        username="testuser",
        password="Password123!",
        email="test@example.com",
        given_name="Test",
        family_name="User",
    )

    # Verify Cognito client was called correctly
    mock_boto3_client.sign_up.assert_called_once_with(
        ClientId="test-client-id",
        Username="testuser",
        Password="Password123!",
        UserAttributes=[
            {"Name": "email", "Value": "test@example.com"},
            {"Name": "given_name", "Value": "Test"},
            {"Name": "family_name", "Value": "User"},
        ],
    )

    # Verify result
    assert result["user_id"] == "test-user-id"
    assert result["confirmed"] is False
    assert "message" in result


def test_sign_up_error(auth_service, mock_boto3_client):
    """Test sign up with error."""
    # Mock Cognito error
    mock_boto3_client.sign_up.side_effect = Exception("Username exists")

    # Call sign_up method and check for exception
    with pytest.raises(ValueError) as exc_info:
        auth_service.sign_up(
            username="testuser",
            password="Password123!",
            email="test@example.com",
            given_name="Test",
            family_name="User",
        )

    # Verify error message
    assert "Username exists" in str(exc_info.value)


def test_confirm_sign_up_success(auth_service, mock_boto3_client):
    """Test successful confirmation of user sign up."""
    # Mock successful confirmation
    mock_boto3_client.confirm_sign_up.return_value = {}

    # Call confirm_sign_up method
    result = auth_service.confirm_sign_up(
        username="testuser", confirmation_code="123456"
    )

    # Verify Cognito client was called correctly
    mock_boto3_client.confirm_sign_up.assert_called_once_with(
        ClientId="test-client-id", Username="testuser", ConfirmationCode="123456"
    )

    # Verify result
    assert result["confirmed"] is True
    assert "message" in result


def test_confirm_sign_up_error(auth_service, mock_boto3_client):
    """Test confirmation with error."""
    # Mock Cognito error
    mock_boto3_client.confirm_sign_up.side_effect = Exception(
        "Invalid confirmation code"
    )

    # Call confirm_sign_up method and check for exception
    with pytest.raises(ValueError) as exc_info:
        auth_service.confirm_sign_up(username="testuser", confirmation_code="invalid")

    # Verify error message
    assert "Invalid confirmation code" in str(exc_info.value)


def test_sign_in_success(auth_service, mock_boto3_client):
    """Test successful user sign in."""
    # Mock Cognito response
    mock_boto3_client.initiate_auth.return_value = {
        "AuthenticationResult": {
            "AccessToken": "access-token",
            "IdToken": "id-token",
            "RefreshToken": "refresh-token",
            "ExpiresIn": 3600,
            "TokenType": "Bearer",
        }
    }

    # Call sign_in method
    result = auth_service.sign_in(username="testuser", password="Password123!")

    # Verify Cognito client was called correctly
    mock_boto3_client.initiate_auth.assert_called_once_with(
        ClientId="test-client-id",
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": "testuser", "PASSWORD": "Password123!"},
    )

    # Verify result
    assert result["access_token"] == "access-token"
    assert result["id_token"] == "id-token"
    assert result["refresh_token"] == "refresh-token"
    assert result["expires_in"] == 3600
    assert result["token_type"] == "Bearer"


def test_sign_in_error(auth_service, mock_boto3_client):
    """Test sign in with error."""
    # Mock Cognito error
    mock_boto3_client.initiate_auth.side_effect = Exception(
        "Incorrect username or password"
    )

    # Call sign_in method and check for exception
    with pytest.raises(ValueError) as exc_info:
        auth_service.sign_in(username="testuser", password="incorrect")

    # Verify error message
    assert "Incorrect username or password" in str(exc_info.value)


def sign_in(self, username: str, password: str) -> Dict[str, Any]:
    """Authenticate a user and get tokens."""
    try:
        response = self.client.initiate_auth(
            ClientId=self.client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password,
            },
        )

        # Check if this is a challenge response
        if "ChallengeName" in response:
            # Return challenge information with status
            logger.info(f"Authentication challenge required for user: {username}")
            return {
                "status": "CHALLENGE",
                "challenge_name": response.get("ChallengeName"),
                "session": response.get("Session"),
                "challenge_parameters": response.get("ChallengeParameters", {}),
            }

        # Normal successful authentication
        auth_result = response.get("AuthenticationResult", {})

        logger.info(f"Sign-in successful for user: {username}")

        return {
            "status": "SUCCESS",
            "access_token": auth_result.get("AccessToken"),
            "id_token": auth_result.get("IdToken"),
            "refresh_token": auth_result.get("RefreshToken"),
            "expires_in": auth_result.get("ExpiresIn", 3600),
            "token_type": auth_result.get("TokenType", "Bearer"),
        }

    except Exception as e:
        logger.error(f"Sign-in error: {str(e)}")
        raise ValueError(str(e))


def test_forgot_password(auth_service, mock_boto3_client):
    """Test forgot password flow."""
    # Mock Cognito response
    mock_boto3_client.forgot_password.return_value = {
        "CodeDeliveryDetails": {
            "Destination": "e***@example.com",
            "DeliveryMedium": "EMAIL",
            "AttributeName": "email",
        }
    }

    # Call forgot_password method
    result = auth_service.forgot_password("testuser")

    # Verify Cognito client was called correctly
    mock_boto3_client.forgot_password.assert_called_once_with(
        ClientId="test-client-id", Username="testuser"
    )

    # Verify result
    assert "message" in result


def test_forgot_password_error(auth_service, mock_boto3_client):
    """Test forgot password with error."""
    # Mock Cognito error
    mock_boto3_client.forgot_password.side_effect = Exception("User not found")

    # Call forgot_password method and check for exception
    with pytest.raises(ValueError) as exc_info:
        auth_service.forgot_password("nonexistent")

    # Verify error message
    assert "User not found" in str(exc_info.value)


def test_confirm_forgot_password(auth_service, mock_boto3_client):
    """Test confirming forgot password."""
    # Mock Cognito response
    mock_boto3_client.confirm_forgot_password.return_value = {}

    # Call confirm_forgot_password method
    result = auth_service.confirm_forgot_password(
        username="testuser", confirmation_code="123456", new_password="NewPassword123!"
    )

    # Verify Cognito client was called correctly
    mock_boto3_client.confirm_forgot_password.assert_called_once_with(
        ClientId="test-client-id",
        Username="testuser",
        ConfirmationCode="123456",
        Password="NewPassword123!",
    )

    # Verify result
    assert "message" in result


def test_confirm_forgot_password_error(auth_service, mock_boto3_client):
    """Test confirming forgot password with error."""
    # Mock Cognito error
    mock_boto3_client.confirm_forgot_password.side_effect = Exception(
        "Invalid verification code"
    )

    # Call confirm_forgot_password method and check for exception
    with pytest.raises(ValueError) as exc_info:
        auth_service.confirm_forgot_password(
            username="testuser",
            confirmation_code="invalid",
            new_password="NewPassword123!",
        )

    # Verify error message
    assert "Invalid verification code" in str(exc_info.value)
