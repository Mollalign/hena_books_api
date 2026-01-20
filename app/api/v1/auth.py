"""
Auth API Routes

Endpoints for user authentication, registration, and password management.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_tokens, decode_token
from app.core.exceptions import InvalidTokenError
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import (
    LoginRequest,
    Token,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    VerifyResetCodeRequest,
    VerifyResetCodeResponse,
    ResetPasswordRequest,
)
from app.services.auth import AuthService
from app.services.password_reset_service import PasswordResetService


router = APIRouter(prefix="/auth", tags=["Authentication"])


# =============================================================================
# REGISTRATION & LOGIN
# =============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.
    
    - **email**: Unique email address
    - **name**: Display name
    - **password**: Minimum 6 characters
    """
    auth_service = AuthService(db)
    return await auth_service.register_user(
        email=user_data.email,
        password=user_data.password,
        name=user_data.name
    )


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password to get JWT tokens.
    
    Returns:
    - **access_token**: Valid for 60 minutes
    - **refresh_token**: Valid for 7 days
    """
    auth_service = AuthService(db)
    user, access_token, refresh_token = await auth_service.authenticate_and_create_tokens(
        email=login_data.email,
        password=login_data.password
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get new access and refresh tokens using a valid refresh token.
    """
    payload = decode_token(token_data.refresh_token)
    
    if not payload or payload.type != "refresh":
        raise InvalidTokenError("Invalid refresh token")
    
    # Generate new tokens
    access_token, refresh_token = create_tokens(payload.sub)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


# =============================================================================
# USER INFO
# =============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current authenticated user's profile.
    """
    return current_user


# =============================================================================
# PASSWORD RESET
# =============================================================================

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset code.
    
    Sends a 6-digit code to the user's email address.
    The code expires in 15 minutes.
    """
    reset_service = PasswordResetService(db)
    result = await reset_service.request_password_reset(request.email)
    
    return ForgotPasswordResponse(
        message=result["message"],
        expires_in_minutes=result["expires_in_minutes"]
    )


@router.post("/verify-reset-code", response_model=VerifyResetCodeResponse)
async def verify_reset_code(
    request: VerifyResetCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify a password reset code.
    
    Checks if the provided code is valid and not expired.
    """
    reset_service = PasswordResetService(db)
    result = await reset_service.verify_reset_code(request.email, request.code)
    
    return VerifyResetCodeResponse(
        valid=result["valid"],
        message=result["message"]
    )


@router.post("/reset-password", response_model=UserResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using a valid reset code.
    
    Requirements:
    - Valid email
    - Valid reset code (not expired, not used)
    - New password (minimum 6 characters)
    
    After successful reset, the code is invalidated.
    """
    reset_service = PasswordResetService(db)
    user = await reset_service.reset_password(
        email=request.email,
        code=request.code,
        new_password=request.new_password
    )
    return user
