import unittest
from unittest.mock import patch, MagicMock
import os
import boto3
from botocore.exceptions import ClientError
import pytest
import logging

# Configure logging to print to console
logging.basicConfig(level=logging.INFO)


# Import the auth service
from backend.app.services.auth_service import CognitoAuthService


class TestCognitoAuthService(unittest.TestCase):
    """Unit tests for the CognitoAuthService."""

    def setUp(self):
        """Set up test environment before each test."""
        # IMPORTANT: Create patcher for environment variables BEFORE initializing the service
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "COGNITO_USER_POOL_ID": "test-user-pool-id",
                "COGNITO_CLIENT_ID": "test-client-id",
                "AWS_REGION": "us-west-2",
            },
        )
        self.env_patcher.start()

        # Create service instance with patched environment vars
        self.auth_service = CognitoAuthService()

        # Mock the boto3 client
        self.mock_client = MagicMock()
        self.auth_service.client = self.mock_client

    def tearDown(self):
        """Clean up after each test."""
        # Stop environment variable patcher
        self.env_patcher.stop()

    def test_initialization(self):
        """Test service initialization with environment variables."""
        auth_service = CognitoAuthService()
        self.assertEqual(auth_service.user_pool_id, "test-user-pool-id")
        self.assertEqual(auth_service.client_id, "test-client-id")

    def test_initialization_without_env_vars(self):
        """Test service initialization without environment variables."""
        # Use a separate patcher to test without env vars
        with patch.dict("os.environ", {}, clear=True):
            with self.assertLogs(level="WARNING") as cm:
                auth_service = CognitoAuthService()
                self.assertIn(
                    "COGNITO_USER_POOL_ID or COGNITO_CLIENT_ID not set", cm.output[0]
                )

    def test_sign_up_success(self):
        """Test successful user registration."""
        # Mock the sign_up response
        self.mock_client.sign_up.return_value = {
            "UserSub": "test-user-sub",
            "UserConfirmed": False,
        }

        # Call the service method
        result = self.auth_service.sign_up(
            username="testuser",
            password="Password123!",
            email="test@example.com",
            given_name="Test",
            family_name="User",
        )

        # Assert the client was called with correct parameters
        self.mock_client.sign_up.assert_called_with(
            ClientId="test-client-id",
            Username="testuser",
            Password="Password123!",
            UserAttributes=[
                {"Name": "email", "Value": "test@example.com"},
                {"Name": "given_name", "Value": "Test"},
                {"Name": "family_name", "Value": "User"},
            ],
        )

        # Assert the result is as expected
        self.assertEqual(result["user_id"], "test-user-sub")
        self.assertFalse(result["confirmed"])
        self.assertIn("message", result)

    def test_sign_up_username_exists(self):
        """Test sign up with existing username."""
        # Mock the exception
        error_response = {
            "Error": {
                "Code": "UsernameExistsException",
                "Message": "User already exists",
            }
        }
        exception = ClientError(error_response, "SignUp")
        self.mock_client.sign_up.side_effect = exception

        # Assert the exception is raised
        with self.assertRaises(ValueError) as context:
            self.auth_service.sign_up(
                username="existinguser",
                password="Password123!",
                email="test@example.com",
                given_name="Test",
                family_name="User",
            )
        self.assertIn("User already exists", str(context.exception))

    def test_confirm_sign_up_success(self):
        """Test successful confirmation of user registration."""
        # Mock the confirm_sign_up response (it returns empty dict on success)
        self.mock_client.confirm_sign_up.return_value = {}

        # Call the service method
        result = self.auth_service.confirm_sign_up(
            username="testuser", confirmation_code="123456"
        )

        # Assert the client was called with correct parameters
        self.mock_client.confirm_sign_up.assert_called_with(
            ClientId="test-client-id", Username="testuser", ConfirmationCode="123456"
        )

        # Assert the result is as expected
        self.assertTrue(result["confirmed"])
        self.assertIn("message", result)

    def test_confirm_sign_up_invalid_code(self):
        """Test confirmation with invalid code."""
        # Mock the exception
        error_response = {
            "Error": {
                "Code": "CodeMismatchException",
                "Message": "Invalid verification code",
            }
        }
        exception = ClientError(error_response, "ConfirmSignUp")
        self.mock_client.confirm_sign_up.side_effect = exception

        # Assert the exception is raised
        with self.assertRaises(ValueError) as context:
            self.auth_service.confirm_sign_up(
                username="testuser", confirmation_code="wrong-code"
            )
        self.assertIn("Invalid verification code", str(context.exception))

    def test_sign_in_success(self):
        """Test successful sign-in."""
        # Mock the initiate_auth response
        self.mock_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "AccessToken": "access-token",
                "IdToken": "id-token",
                "RefreshToken": "refresh-token",
                "ExpiresIn": 3600,
                "TokenType": "Bearer",
            }
        }

        # Call the service method
        result = self.auth_service.sign_in(username="testuser", password="Password123!")

        # Assert the client was called with correct parameters
        self.mock_client.initiate_auth.assert_called_with(
            ClientId="test-client-id",
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": "testuser",
                "PASSWORD": "Password123!",
            },
        )

        # Assert the result is as expected
        self.assertEqual(result["access_token"], "access-token")
        self.assertEqual(result["id_token"], "id-token")
        self.assertEqual(result["refresh_token"], "refresh-token")
        self.assertEqual(result["expires_in"], 3600)
        self.assertEqual(result["token_type"], "Bearer")

    def test_sign_in_incorrect_credentials(self):
        """Test sign in with incorrect credentials."""
        # Mock the exception
        error_response = {
            "Error": {
                "Code": "NotAuthorizedException",
                "Message": "Incorrect username or password",
            }
        }
        exception = ClientError(error_response, "InitiateAuth")
        self.mock_client.initiate_auth.side_effect = exception

        # Assert the exception is raised
        with self.assertRaises(ValueError) as context:
            self.auth_service.sign_in(username="testuser", password="WrongPassword")
        self.assertIn("Incorrect username or password", str(context.exception))

    def test_forgot_password_success(self):
        """Test successful initiation of forgot password flow."""
        # Mock the forgot_password response
        self.mock_client.forgot_password.return_value = {
            "CodeDeliveryDetails": {
                "Destination": "t***@e***",
                "DeliveryMedium": "EMAIL",
                "AttributeName": "email",
            }
        }

        # Call the service method
        result = self.auth_service.forgot_password(username="testuser")

        # Assert the client was called with correct parameters
        self.mock_client.forgot_password.assert_called_with(
            ClientId="test-client-id", Username="testuser"
        )

        # Assert the result is as expected
        self.assertIn("message", result)

    def test_confirm_forgot_password_success(self):
        """Test successful reset of password."""
        # Mock the confirm_forgot_password response
        self.mock_client.confirm_forgot_password.return_value = {}

        # Call the service method
        result = self.auth_service.confirm_forgot_password(
            username="testuser",
            confirmation_code="123456",
            new_password="NewPassword123!",
        )

        # Assert the client was called with correct parameters
        self.mock_client.confirm_forgot_password.assert_called_with(
            ClientId="test-client-id",
            Username="testuser",
            ConfirmationCode="123456",
            Password="NewPassword123!",
        )

        # Assert the result is as expected
        self.assertIn("message", result)

    def test_confirm_forgot_password_invalid_code(self):
        """Test password reset with invalid code."""
        # Mock the exception
        error_response = {
            "Error": {
                "Code": "CodeMismatchException",
                "Message": "Invalid verification code",
            }
        }
        exception = ClientError(error_response, "ConfirmForgotPassword")
        self.mock_client.confirm_forgot_password.side_effect = exception

        # Assert the exception is raised
        with self.assertRaises(ValueError) as context:
            self.auth_service.confirm_forgot_password(
                username="testuser",
                confirmation_code="wrong-code",
                new_password="NewPassword123!",
            )
        self.assertIn("Invalid verification code", str(context.exception))


if __name__ == "__main__":
    unittest.main()
