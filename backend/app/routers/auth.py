from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.param_functions import Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

from backend.app.services.auth_service import CognitoAuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = CognitoAuthService()

# Models for request/response


class UserSignUpRequest(BaseModel):
    username: str
    password: str
    email: EmailStr
    given_name: str
    family_name: str


class ConfirmSignUpRequest(BaseModel):
    username: str
    confirmation_code: str


class ForgotPasswordRequest(BaseModel):
    username: str


class ConfirmForgotPasswordRequest(BaseModel):
    username: str
    confirmation_code: str
    new_password: str


# Endpoints
@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignUpRequest):
    """Register a new user"""
    try:
        result = auth_service.sign_up(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            given_name=user_data.given_name,
            family_name=user_data.family_name,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/confirm")
async def confirm_signup(data: ConfirmSignUpRequest):
    """Confirm user registration with verification code"""
    try:
        result = auth_service.confirm_sign_up(data.username, data.confirmation_code)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint that follows OAuth2 password flow"""
    try:
        result = auth_service.sign_in(form_data.username, form_data.password)

        # Format the response for OAuth2
        return {
            "access_token": result.get("access_token"),
            "token_type": "bearer",
            "refresh_token": result.get("refresh_token"),
            "id_token": result.get("id_token"),
            "expires_in": result.get("expires_in"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Initiate password reset process"""
    try:
        result = auth_service.forgot_password(data.username)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-password")
async def reset_password(data: ConfirmForgotPasswordRequest):
    """Complete password reset with verification code"""
    try:
        result = auth_service.confirm_forgot_password(
            data.username, data.confirmation_code, data.new_password
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
