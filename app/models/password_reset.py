"""
Password Reset Model

Stores password reset codes for forgot password functionality.
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.config import settings


class PasswordReset(Base):
    """
    Password reset model for storing reset codes.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to users table (UUID)
        code: 6-digit reset code
        email: User email (for quick lookup)
        expires_at: Expiration timestamp
        used_at: When the code was used (null if not used)
        created_at: When the code was created
    """
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(6), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="password_resets")

    def __repr__(self):
        return f"<PasswordReset(id={self.id}, email='{self.email}', code='{self.code}')>"
    
    def is_expired(self) -> bool:
        """Check if the reset code has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_used(self) -> bool:
        """Check if the reset code has been used."""
        return self.used_at is not None
    
    def is_valid(self) -> bool:
        """Check if the reset code is valid (not expired and not used)."""
        return not self.is_expired() and not self.is_used()

