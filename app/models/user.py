"""
User Model

Represents registered users of the book platform.
Includes admin role for you (the author) and regular users (readers).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class UserRole(str, enum.Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """
    User model for authentication and reading tracking.
    
    Attributes:
        id: Primary key
        email: Unique email address
        password_hash: Hashed password (never store plain text)
        name: Display name
        role: user or admin
        is_active: Account status
        created_at: Registration timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "users"


    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    reading_sessions = relationship("ReadingSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
