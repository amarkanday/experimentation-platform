import boto3
import os
import logging
from typing import Dict, Any, Optional

"""
AWS Cognito authentication service.

This module provides a service for handling authentication operations using AWS Cognito.
"""

from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)


class CognitoAuthService:
    """Service for AWS Cognito authentication operations."""

    def __init__(self):
        # Load configuration from environment variables
        self.user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
        self.client_id = os.environ.get("COGNITO_CLIENT_ID")
        self.region = os.environ.get("AWS_REGION", "us-east-1")

        if not self.user_pool_id or not self.client_id:
            logger.warning("COGNITO_USER_POOL_ID or COGNITO_CLIENT_ID not set")

        # Initialize Cognito Identity Provider client
        self.client = boto3.client("cognito-idp", region_name=self.region)

    def sign_up(
        self,
        username: str,
        password: str,
        email: str,
        given_name: str,
        family_name: str,
    ) -> Dict[str, Any]:
        """Register a new user in the Cognito User Pool."""
        try:
            # Format user attributes for Cognito
            user_attributes = [
                {"Name": "email", "Value": email},
                {"Name": "given_name", "Value": given_name},
                {"Name": "family_name", "Value": family_name},
            ]

            response = self.client.sign_up(
                ClientId=self.client_id,
                Username=username,
                Password=password,
                UserAttributes=user_attributes,
            )

            logger.info(f"User registered successfully: {username}")
            return {
                "user_id": response["UserSub"],
                "confirmed": False,
                "message": "User registration successful. Please check "
                "your email for verification code.",
            }

        except ClientError as e:
            logger.error(f"Sign-up error: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error during sign-up: {str(e)}")
            # Pass through the original error message
            raise ValueError(str(e))

    def confirm_sign_up(self, username: str, confirmation_code: str) -> Dict[str, Any]:
        """Confirm user registration with the code sent to their email."""
        try:
            self.client.confirm_sign_up(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
            )

            logger.info(f"User confirmed successfully: {username}")
            return {
                "message": "Account confirmed successfully. You can now sign in.",
                "confirmed": True,
            }

        except ClientError as e:
            logger.error(f"Confirmation error: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error during confirmation: {str(e)}")
            # Pass through the original error message
            raise ValueError(str(e))

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

            auth_result = response.get("AuthenticationResult", {})

            logger.info(f"Sign-in successful for user: {username}")

            return {
                "access_token": auth_result.get("AccessToken"),
                "id_token": auth_result.get("IdToken"),
                "refresh_token": auth_result.get("RefreshToken"),
                "expires_in": auth_result.get("ExpiresIn", 3600),
                "token_type": auth_result.get("TokenType", "Bearer"),
            }

        except ClientError as e:
            logger.error(f"Sign-in error: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error during sign-in: {str(e)}")
            # Pass through the original error message
            raise ValueError(str(e))

    def forgot_password(self, username: str) -> Dict[str, Any]:
        """Initiate the forgot password flow."""
        try:
            self.client.forgot_password(ClientId=self.client_id, Username=username)

            logger.info(f"Forgot password flow initiated for user: {username}")
            return {"message": "Password reset code has been sent to your email."}

        except ClientError as e:
            logger.error(f"Forgot password error: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error during forgot password: {str(e)}")
            # Pass through the original error message
            raise ValueError(str(e))

    def confirm_forgot_password(
        self, username: str, confirmation_code: str, new_password: str
    ) -> Dict[str, Any]:
        """Complete the forgot password flow by setting a new password."""
        try:
            self.client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=confirmation_code,
                Password=new_password,
            )

            logger.info(f"Password reset successful for user: {username}")
            return {
                "message": "Password has been reset successfully. You can now sign in."
            }

        except ClientError as e:
            logger.error(f"Confirm forgot password error: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error during password reset: {str(e)}")
            # Pass through the original error message
            raise ValueError(str(e))

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the authentication tokens using a refresh token."""
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={
                    "REFRESH_TOKEN": refresh_token,
                },
            )

            auth_result = response.get("AuthenticationResult", {})

            logger.info("Token refreshed successfully")

            return {
                "access_token": auth_result.get("AccessToken"),
                "id_token": auth_result.get("IdToken"),
                "expires_in": auth_result.get("ExpiresIn", 3600),
                "token_type": auth_result.get("TokenType", "Bearer"),
            }

        except ClientError as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            raise ValueError("An unexpected error occurred during token refresh")

    def get_user(self, access_token: str) -> Dict[str, Any]:
        """Get user details from the access token."""
        try:
            response = self.client.get_user(AccessToken=access_token)

            # Extract user attributes
            user_attributes = {
                attr["Name"]: attr["Value"]
                for attr in response.get("UserAttributes", [])
            }

            logger.info(
                f"User details retrieved for username: {response.get('Username')}"
            )

            return {"username": response.get("Username"), "attributes": user_attributes}

        except ClientError as e:
            logger.error(f"Get user error: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error getting user details: {str(e)}")
            raise ValueError("An unexpected error occurred retrieving user details")


# Create a single instance of the service
auth_service = CognitoAuthService()
