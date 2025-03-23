from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field
from backend.app.services.auth_service import CognitoAuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = CognitoAuthService()


# Models for request/response
class UserSignUpRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: EmailStr
    given_name: str
    family_name: str
    company: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None


class ConfirmSignUpRequest(BaseModel):
    username: str
    confirmation_code: str


class ResendCodeRequest(BaseModel):
    username: str


class ForgotPasswordRequest(BaseModel):
    username: str


class ConfirmForgotPasswordRequest(BaseModel):
    username: str
    confirmation_code: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    previous_password: str
    proposed_password: str = Field(..., min_length=8)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# Define the OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# Dependency for getting the current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        return auth_service.get_user(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Endpoints
@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignUpRequest):
    try:
        result = auth_service.sign_up(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            given_name=user_data.given_name,
            family_name=user_data.family_name,
            company=user_data.company,
            department=user_data.department,
            role=user_data.role,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/confirm")
async def confirm_signup(data: ConfirmSignUpRequest):
    try:
        result = auth_service.confirm_sign_up(data.username, data.confirmation_code)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/resend-code")
async def resend_confirmation_code(data: ResendCodeRequest):
    try:
        result = auth_service.resend_confirmation_code(data.username)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        result = auth_service.sign_in(form_data.username, form_data.password)

        # Handle challenges
        if result.get("status") != "SUCCESS":
            return result

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


@router.post("/challenge")
async def auth_challenge(
    challenge_name: str, username: str, session: str, responses: Dict[str, str]
):
    try:
        result = auth_service.respond_to_auth_challenge(
            challenge_name, username, session, responses
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    try:
        result = auth_service.forgot_password(data.username)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/confirm-forgot-password")
async def confirm_forgot_password(data: ConfirmForgotPasswordRequest):
    try:
        result = auth_service.confirm_forgot_password(
            data.username, data.confirmation_code, data.new_password
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest, token: str = Depends(oauth2_scheme)
):
    try:
        result = auth_service.change_password(
            token, data.previous_password, data.proposed_password
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/refresh")
async def refresh_token(data: RefreshTokenRequest):
    try:
        result = auth_service.refresh_tokens(data.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    try:
        result = auth_service.sign_out(token)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/me")
async def get_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    return user
