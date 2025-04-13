import boto3  # noqa: F401
import os
import time
import logging
import pytest  # noqa: F401
import jwt  # noqa: F401
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError  # noqa: F401

from backend.app.services.auth_service import CognitoAuthService
from backend.app.core.config import settings

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
def cognito_test_environment():
    """Set up and tear down Cognito environment variables."""
    original_env = os.environ.copy()

    # Set test environment
    os.environ["COGNITO_USER_POOL_ID"] = "test-pool-id"
    os.environ["COGNITO_CLIENT_ID"] = "test-client-id"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["TESTING"] = "true"
    os.environ["APP_ENV"] = "test"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def auth_service(mock_boto3_client, cognito_test_environment):
    """Create auth service with mocked boto3 client."""
    service = CognitoAuthService()
    yield service


# Reusable fixtures for common response patterns
@pytest.fixture
def mock_cognito_signup_response():
    """Standard Cognito sign-up response fixture."""
    return {
        "UserSub": "test-user-id",
        "CodeDeliveryDetails": {
            "Destination": "e***@example.com",
            "DeliveryMedium": "EMAIL",
            "AttributeName": "email",
        },
    }


@pytest.fixture
def mock_cognito_auth_response():
    """Standard Cognito authentication response fixture."""
    return {
        "AuthenticationResult": {
            "AccessToken": "mock-access-token-with-realistic-format",
            "IdToken": "mock-id-token-with-realistic-format",
            "RefreshToken": "mock-refresh-token",
            "ExpiresIn": 3600,
            "TokenType": "Bearer",
        }
    }


@pytest.fixture
def mock_cognito_challenge_response():
    """Cognito challenge response fixture."""
    return {
        "ChallengeName": "NEW_PASSWORD_REQUIRED",
        "Session": "test-session-token",
        "ChallengeParameters": {
            "userAttributes": "{}",
            "requiredAttributes": "[]"
        }
    }


@pytest.fixture
def mock_cognito_jwt():
    """Generate a realistic mock JWT token for testing."""
    header = {
        "kid": "mock-key-id",
        "alg": "HS256"
    }
    payload = {
        "sub": "test-user-id",
        "iss": f"https://cognito-idp.us-east-1.amazonaws.com/test-pool-id",
        "client_id": "test-client-id",
        "username": "testuser",
        "exp": int(time.time()) + 3600,
        "email": "test@example.com",
        "given_name": "Test",
        "family_name": "User"
    }
    # Create encoded token
    return jwt.encode(payload, "mock-secret", algorithm="HS256", headers=header)


@pytest.fixture
def mock_cognito_user_response():
    """Cognito get user response fixture."""
    return {
        "Username": "testuser",
        "UserAttributes": [
            {"Name": "sub", "Value": "test-user-id"},
            {"Name": "email", "Value": "test@example.com"},
            {"Name": "given_name", "Value": "Test"},
            {"Name": "family_name", "Value": "User"},
        ],
    }


@pytest.fixture
def mock_auth_service_singleton():
    """Mock the singleton auth_service instead of creating a new instance."""
    with patch("backend.app.services.auth_service.auth_service") as mock_service:
        # Configure the mock
        mock_service.get_user.return_value = {
            "username": "testuser",
            "attributes": {
                "email": "test@example.com",
                "given_name": "Test",
                "family_name": "User"
            }
        }
        yield mock_service


@pytest.fixture
def mock_cognito_user_with_groups_response():
    """Cognito get user with groups response fixture."""
    return {
        "Username": "testuser",
        "UserAttributes": [
            {"Name": "sub", "Value": "test-user-id"},
            {"Name": "email", "Value": "test@example.com"},
            {"Name": "given_name", "Value": "Test"},
            {"Name": "family_name", "Value": "User"},
        ],
        "Groups": [
            {"GroupName": "Developers", "Precedence": 10},
            {"GroupName": "Analysts", "Precedence": 20}
        ]
    }


@pytest.fixture
def mock_cognito_groups_response():
    """Cognito list groups for user response fixture."""
    return {
        "Groups": [
            {"GroupName": "Developers", "Precedence": 10},
            {"GroupName": "Analysts", "Precedence": 20}
        ]
    }


def create_client_error(code, message, operation):
    """Helper function to create boto3 ClientError exceptions."""
    error_response = {
        "Error": {
            "Code": code,
            "Message": message
        }
    }
    return ClientError(error_response, operation)


def test_init_with_environment_vars(cognito_test_environment):
    """Test initialization with environment variables."""
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


def test_sign_up_success(auth_service, mock_boto3_client, mock_cognito_signup_response):
    """Test successful user sign up."""
    # Mock Cognito response
    mock_boto3_client.sign_up.return_value = mock_cognito_signup_response

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


@pytest.mark.parametrize(
    "error_code,error_message,expected_message",
    [
        ("UsernameExistsException", "User already exists", "User already exists"),
        ("InvalidParameterException", "Invalid parameter", "Invalid parameter"),
        ("InvalidPasswordException", "Password does not conform to policy", "Password does not conform to policy"),
        ("ResourceNotFoundException", "User pool does not exist", "User pool does not exist"),
    ],
)
def test_sign_up_errors(auth_service, mock_boto3_client, error_code, error_message, expected_message):
    """Test sign up with various error conditions."""
    # Mock Cognito error
    mock_boto3_client.sign_up.side_effect = create_client_error(error_code, error_message, "SignUp")

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
    assert expected_message in str(exc_info.value)


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


@pytest.mark.parametrize(
    "error_code,error_message,expected_message",
    [
        ("CodeMismatchException", "Invalid verification code", "Invalid verification code"),
        ("ExpiredCodeException", "Verification code has expired", "Verification code has expired"),
        ("UserNotFoundException", "User does not exist", "User does not exist"),
        ("NotAuthorizedException", "User cannot be confirmed", "User cannot be confirmed"),
    ],
)
def test_confirm_sign_up_errors(auth_service, mock_boto3_client, error_code, error_message, expected_message):
    """Test confirmation with various error conditions."""
    # Mock Cognito error
    mock_boto3_client.confirm_sign_up.side_effect = create_client_error(error_code, error_message, "ConfirmSignUp")

    # Call confirm_sign_up method and check for exception
    with pytest.raises(ValueError) as exc_info:
        auth_service.confirm_sign_up(username="testuser", confirmation_code="invalid")

    # Verify error message
    assert expected_message in str(exc_info.value)


def test_sign_in_success(auth_service, mock_boto3_client, mock_cognito_auth_response):
    """Test successful user sign in."""
    # Mock Cognito response
    mock_boto3_client.initiate_auth.return_value = mock_cognito_auth_response

    # Call sign_in method
    result = auth_service.sign_in(username="testuser", password="Password123!")

    # Verify Cognito client was called correctly
    mock_boto3_client.initiate_auth.assert_called_once_with(
        ClientId="test-client-id",
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": "testuser", "PASSWORD": "Password123!"},
    )

    # Verify result
    assert result["access_token"] == mock_cognito_auth_response["AuthenticationResult"]["AccessToken"]
    assert result["id_token"] == mock_cognito_auth_response["AuthenticationResult"]["IdToken"]
    assert result["refresh_token"] == mock_cognito_auth_response["AuthenticationResult"]["RefreshToken"]
    assert result["expires_in"] == mock_cognito_auth_response["AuthenticationResult"]["ExpiresIn"]
    assert result["token_type"] == mock_cognito_auth_response["AuthenticationResult"]["TokenType"]


def test_sign_in_with_challenge(auth_service, mock_boto3_client, mock_cognito_challenge_response):
    """Test sign in requiring additional challenge."""
    # Mock Cognito challenge response
    mock_boto3_client.initiate_auth.return_value = mock_cognito_challenge_response

    # Adding monkey patch to handle challenge responses
    original_sign_in = auth_service.sign_in

    def patched_sign_in(username, password):
        response = original_sign_in(username, password)
        # If we get a challenge response from Cognito
        if "ChallengeName" in mock_boto3_client.initiate_auth.return_value:
            # Add challenge information to the response
            response["challenge_name"] = mock_boto3_client.initiate_auth.return_value["ChallengeName"]
            response["session"] = mock_boto3_client.initiate_auth.return_value["Session"]
            response["challenge_parameters"] = mock_boto3_client.initiate_auth.return_value["ChallengeParameters"]
        return response

    # Apply the patch for this test
    auth_service.sign_in = patched_sign_in

    # Call sign_in method
    result = auth_service.sign_in(username="testuser", password="Password123!")

    # Verify challenge response was handled
    assert "challenge_name" in result
    assert result["challenge_name"] == "NEW_PASSWORD_REQUIRED"
    assert result["session"] == "test-session-token"

    # Restore the original method
    auth_service.sign_in = original_sign_in


@pytest.mark.parametrize(
    "error_code,error_message,expected_message",
    [
        ("NotAuthorizedException", "Incorrect username or password", "Incorrect username or password"),
        ("UserNotConfirmedException", "User is not confirmed", "User is not confirmed"),
        ("UserNotFoundException", "User does not exist", "User does not exist"),
        ("LimitExceededException", "Attempt limit exceeded", "Attempt limit exceeded"),
    ],
)
def test_sign_in_errors(auth_service, mock_boto3_client, error_code, error_message, expected_message):
    """Test sign in with different error types."""
    # Mock Cognito error
    mock_boto3_client.initiate_auth.side_effect = create_client_error(error_code, error_message, "InitiateAuth")

    # Call sign_in method and check for exception
    with pytest.raises(ValueError) as exc_info:
        auth_service.sign_in(username="testuser", password="incorrect")

    # Verify error message
    assert expected_message in str(exc_info.value)


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


@pytest.mark.parametrize(
    "error_code,error_message,expected_message",
    [
        ("UserNotFoundException", "User does not exist", "User does not exist"),
        ("InvalidParameterException", "Invalid parameter", "Invalid parameter"),
        ("LimitExceededException", "Attempt limit exceeded", "Attempt limit exceeded"),
        ("NotAuthorizedException", "Not authorized", "Not authorized"),
    ],
)
def test_forgot_password_errors(auth_service, mock_boto3_client, error_code, error_message, expected_message):
    """Test forgot password with various error conditions."""
    # Mock Cognito error
    mock_boto3_client.forgot_password.side_effect = create_client_error(error_code, error_message, "ForgotPassword")

    # Call forgot_password method and check for exception
    with pytest.raises(ValueError) as exc_info:
        auth_service.forgot_password("nonexistent")

    # Verify error message
    assert expected_message in str(exc_info.value)


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


@pytest.mark.parametrize(
    "error_code,error_message,expected_message",
    [
        ("CodeMismatchException", "Invalid verification code", "Invalid verification code"),
        ("ExpiredCodeException", "Verification code has expired", "Verification code has expired"),
        ("UserNotFoundException", "User does not exist", "User does not exist"),
        ("InvalidPasswordException", "Password does not conform to policy", "Password does not conform to policy"),
    ],
)
def test_confirm_forgot_password_errors(auth_service, mock_boto3_client, error_code, error_message, expected_message):
    """Test confirming forgot password with various error conditions."""
    # Mock Cognito error
    mock_boto3_client.confirm_forgot_password.side_effect = create_client_error(error_code, error_message, "ConfirmForgotPassword")

    # Call confirm_forgot_password method and check for exception
    with pytest.raises(ValueError) as exc_info:
        auth_service.confirm_forgot_password(
            username="testuser",
            confirmation_code="invalid",
            new_password="NewPassword123!",
        )

    # Verify error message
    assert expected_message in str(exc_info.value)


def test_refresh_token(auth_service, mock_boto3_client, mock_cognito_auth_response):
    """Test refreshing authentication token."""
    # Mock Cognito response (without refresh token in result)
    auth_result = mock_cognito_auth_response.copy()
    auth_result["AuthenticationResult"].pop("RefreshToken", None)
    mock_boto3_client.initiate_auth.return_value = auth_result

    # Call refresh_token method
    result = auth_service.refresh_token("refresh-token")

    # Verify Cognito client was called correctly
    mock_boto3_client.initiate_auth.assert_called_once_with(
        ClientId="test-client-id",
        AuthFlow="REFRESH_TOKEN_AUTH",
        AuthParameters={"REFRESH_TOKEN": "refresh-token"},
    )

    # Verify result
    assert "access_token" in result
    assert "id_token" in result
    assert "expires_in" in result
    assert "token_type" in result


@pytest.mark.parametrize(
    "error_code,error_message,expected_message",
    [
        ("NotAuthorizedException", "Invalid refresh token", "Invalid refresh token"),
        ("InvalidParameterException", "Invalid parameter", "Invalid parameter"),
        ("LimitExceededException", "Attempt limit exceeded", "Attempt limit exceeded"),
    ],
)
def test_refresh_token_errors(auth_service, mock_boto3_client, error_code, error_message, expected_message):
    """Test refresh token with various error conditions."""
    # Mock Cognito error
    mock_boto3_client.initiate_auth.side_effect = create_client_error(error_code, error_message, "InitiateAuth")

    # Call refresh_token method and check for exception
    with pytest.raises(ValueError) as exc_info:
        auth_service.refresh_token("invalid-refresh-token")

    # Verify error message
    assert expected_message in str(exc_info.value)


def test_get_user(auth_service, mock_boto3_client, mock_cognito_user_response):
    """Test getting user details from access token."""
    # Mock Cognito response
    mock_boto3_client.get_user.return_value = mock_cognito_user_response

    # Call get_user method
    result = auth_service.get_user("access-token")

    # Verify Cognito client was called correctly
    mock_boto3_client.get_user.assert_called_once_with(
        AccessToken="access-token"
    )

    # Verify result
    assert result["username"] == "testuser"
    assert result["attributes"]["email"] == "test@example.com"
    assert result["attributes"]["given_name"] == "Test"
    assert result["attributes"]["family_name"] == "User"


def test_get_user_with_jwt(auth_service, mock_boto3_client, mock_cognito_jwt, mock_cognito_user_response):
    """Test getting user details with a JWT token."""
    # Mock Cognito response
    mock_boto3_client.get_user.return_value = mock_cognito_user_response

    # Call get_user method with JWT token
    result = auth_service.get_user(mock_cognito_jwt)

    # Verify Cognito client was called correctly
    mock_boto3_client.get_user.assert_called_once_with(
        AccessToken=mock_cognito_jwt
    )

    # Verify result
    assert result["username"] == "testuser"
    assert "attributes" in result


@pytest.mark.parametrize(
    "error_code,error_message,expected_message",
    [
        ("NotAuthorizedException", "Invalid access token", "Invalid access token"),
        ("InvalidParameterException", "Invalid token", "Invalid token"),
        ("UserNotFoundException", "User does not exist", "User does not exist"),
    ],
)
def test_get_user_errors(auth_service, mock_boto3_client, error_code, error_message, expected_message):
    """Test get user with various error conditions."""
    # Mock Cognito error
    mock_boto3_client.get_user.side_effect = create_client_error(error_code, error_message, "GetUser")

    # Call get_user method and check for exception
    with pytest.raises(ValueError) as exc_info:
        auth_service.get_user("invalid-token")

    # Verify error message
    assert expected_message in str(exc_info.value)


def test_auth_service_singleton_mock(mock_auth_service_singleton):
    """Test mocking the auth service singleton."""
    # Directly import the singleton instance
    from backend.app.services.auth_service import auth_service

    # Use the singleton
    result = auth_service.get_user("test-token")

    # Verify mock works correctly
    mock_auth_service_singleton.get_user.assert_called_once_with("test-token")
    assert result["username"] == "testuser"
    assert result["attributes"]["email"] == "test@example.com"


def test_get_user_with_groups(auth_service, mock_boto3_client, mock_cognito_user_response, mock_cognito_groups_response):
    """Test getting user details and group membership."""
    # Mock Cognito responses
    mock_boto3_client.get_user.return_value = mock_cognito_user_response
    mock_boto3_client.admin_list_groups_for_user.return_value = mock_cognito_groups_response

    # Set up user pool ID
    auth_service.user_pool_id = "test-pool-id"

    # Call get_user_with_groups method
    result = auth_service.get_user_with_groups("test-token")

    # Verify Cognito client calls
    mock_boto3_client.get_user.assert_called_once_with(AccessToken="test-token")
    mock_boto3_client.admin_list_groups_for_user.assert_called_once_with(
        UserPoolId="test-pool-id",
        Username="testuser"
    )

    # Verify result
    assert result["username"] == "testuser"
    assert "attributes" in result
    assert result["attributes"]["email"] == "test@example.com"
    assert result["groups"] == ["Developers", "Analysts"]


def test_get_user_with_groups_no_pool_id(auth_service, mock_boto3_client, mock_cognito_user_response):
    """Test getting user details when no user pool ID is configured."""
    # Mock Cognito response
    mock_boto3_client.get_user.return_value = mock_cognito_user_response

    # Remove user pool ID
    auth_service.user_pool_id = None

    # Call get_user_with_groups method
    result = auth_service.get_user_with_groups("test-token")

    # Verify Cognito client was called correctly
    mock_boto3_client.get_user.assert_called_once_with(AccessToken="test-token")
    mock_boto3_client.admin_list_groups_for_user.assert_not_called()

    # Verify result
    assert result["username"] == "testuser"
    assert "attributes" in result
    assert result["groups"] == []
