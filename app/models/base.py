"""
Base Model Module

This module provides a base class for all SQLAlchemy models with common fields:
- id: Primary key (UUID)
- created_at: Timestamp when record was created
- updated_at: Timestamp when record was last updated

Key Concepts:
1. SQLAlchemy Declarative Base - Used to define models as Python classes
2. Model Inheritance - All models inherit from BaseModel to get common fields
3. Automatic Timestamps - Uses server_default and onupdate for automatic timestamps
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

# Import the Base from your database module
from app.core.database import Base


class BaseModel(Base):
    """
    Abstract base model class that provides common fields for all models.
    
    Attributes:
        id (UUID): Primary key, auto-generated UUID
        created_at (DateTime): Timestamp set automatically when record is created
        updated_at (DateTime): Timestamp updated automatically when record is modified
    
    Usage:
        class User(BaseModel):
            __tablename__ = "users"
            
            email = Column(String(255), unique=True, nullable=False)
            # ... other fields
    """
    
    # This makes the class abstract - no table will be created for BaseModel itself
    __abstract__ = True
    
    # Primary Key - UUID for better security and distributed systems
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,  # Python-side default
        server_default=func.gen_random_uuid(),  # Database-side default (requires pgcrypto)
        nullable=False,
        index=True
    )
    
    # Created timestamp - set once when record is created
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # Database sets this automatically
        nullable=False
    )
    
    # Updated timestamp - updates every time the record is modified
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # Set initially
        onupdate=func.now(),  # Update on every modification
        nullable=False
    )
    
    def __repr__(self):
        """String representation for debugging."""
        return f"<{self.__class__.__name__}(id={self.id})>"
