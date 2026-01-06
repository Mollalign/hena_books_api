"""
Auth Schemas

Pydantic models for authentication requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for login request."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for decoded JWT token payload."""
    sub: str  # user id
    exp: int  # expiration timestamp
    type: str  # "access" or "refresh"


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


class PasswordChange(BaseModel):
    """Schema for password change request."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=100)


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    """Schema for verify reset code request."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="6-digit reset code")


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="6-digit reset code")
    new_password: str = Field(..., min_length=6, max_length=100)


class ForgotPasswordResponse(BaseModel):
    """Schema for forgot password response."""
    message: str
    expires_in_minutes: int


class VerifyResetCodeResponse(BaseModel):
    """Schema for verify reset code response."""
    valid: bool
    message: str
