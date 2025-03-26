"""
Authentication endpoints for the API.

This module provides endpoints for user authentication, including
registration, login, and password reset.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.api import deps

from backend.app.schemas.auth import (
    SignUpRequest,
    SignUpResponse,
    ConfirmSignUpRequest,
    ConfirmSignUpResponse,
    TokenResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ConfirmForgotPasswordRequest,
    ConfirmForgotPasswordResponse,
    RefreshTokenRequest,
    UserInfoResponse
)

from app.services.auth_service import CognitoAuthService

router = APIRouter()


@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
def signup(signup_data: SignUpRequest) -> Any:
    """
    Register a new user.
    """
    auth_service = CognitoAuthService()
    try:
        response = auth_service.sign_up(
            username=signup_data.username,
            password=signup_data.password,
            email=signup_data.email,
            given_name=signup_data.given_name,
            family_name=signup_data.family_name,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/confirm", response_model=ConfirmSignUpResponse)
def confirm_signup(confirm_data: ConfirmSignUpRequest) -> Any:
    """
    Confirm user registration with the verification code.
    """
    auth_service = CognitoAuthService()
    try:
        response = auth_service.confirm_sign_up(
            username=confirm_data.username,
            confirmation_code=confirm_data.confirmation_code,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/token", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    auth_service = CognitoAuthService()
    try:
        response = auth_service.sign_in(
            username=form_data.username,
            password=form_data.password,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(forgot_password_data: ForgotPasswordRequest) -> Any:
    """
    Initiate the forgot password flow.
    """
    auth_service = CognitoAuthService()
    try:
        response = auth_service.forgot_password(
            username=forgot_password_data.username,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/reset-password", response_model=ConfirmForgotPasswordResponse)
def reset_password(reset_data: ConfirmForgotPasswordRequest) -> Any:
    """
    Complete the forgot password flow by setting a new password.
    """
    auth_service = CognitoAuthService()
    try:
        response = auth_service.confirm_forgot_password(
            username=reset_data.username,
            confirmation_code=reset_data.confirmation_code,
            new_password=reset_data.new_password,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_data: RefreshTokenRequest) -> Any:
    """
    Refresh the access token using a refresh token.
    """
    auth_service = CognitoAuthService()
    try:
        response = auth_service.refresh_token(
            refresh_token=refresh_data.refresh_token,
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserInfoResponse)
def get_user_info(token: str = Depends(deps.get_token)) -> Any:
    """
    Get current user information.
    """
    auth_service = CognitoAuthService()
    try:
        response = auth_service.get_user(access_token=token)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
