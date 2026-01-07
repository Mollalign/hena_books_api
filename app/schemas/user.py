"""
User Schemas

Pydantic models for user request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserResponse(UserBase):
    """Schema for user response (public info)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime


class UserInDB(UserResponse):
    """Schema for user with sensitive data (internal use)."""
    password_hash: str
    updated_at: datetime
