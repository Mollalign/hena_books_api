"""
Auth API Routes

Endpoints for user authentication and registration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
from app.core.security import create_tokens, decode_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


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
    
    # Check if email already exists
    existing_user = await auth_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = await auth_service.create_user(
        email=user_data.email,
        password=user_data.password,
        name=user_data.name
    )
    
    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password to get JWT tokens.
    
    Returns access token (60 min) and refresh token (7 days).
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token, refresh_token = create_tokens(user.id)
    
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
    Get a new access token using a valid refresh token.
    """
    payload = decode_token(token_data.refresh_token)
    
    if not payload or payload.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate new tokens
    user_id = int(payload.sub)
    access_token, refresh_token = create_tokens(user_id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current authenticated user's profile.
    """
    return current_user


# =============================================================================
# PASSWORD RESET ENDPOINTS
# =============================================================================

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset code.
    
    Sends a 6-digit code to the user's email address.
    The code expires in 15 minutes (configurable).
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
    
    Requires:
    - Valid email
    - Valid reset code (not expired, not used)
    - New password (minimum 6 characters)
    
    After successful reset, the code is marked as used and cannot be reused.
    """
    reset_service = PasswordResetService(db)
    user = await reset_service.reset_password(
        email=request.email,
        code=request.code,
        new_password=request.new_password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email, code, or code has expired"
        )
    
    return user
