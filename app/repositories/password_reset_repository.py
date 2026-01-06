"""
Password Reset Repository

Data access layer for PasswordReset model.
All password reset-related database operations.
"""

from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.repositories.base import BaseRepository
from app.models.password_reset import PasswordReset
from app.core.config import settings


class PasswordResetRepository(BaseRepository[PasswordReset]):
    """Repository for PasswordReset model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(PasswordReset, db)
    
    async def get_by_code(self, code: str) -> Optional[PasswordReset]:
        """Get a password reset by code."""
        result = await self.db.execute(
            select(PasswordReset).where(PasswordReset.code == code)
        )
        return result.scalar_one_or_none()
    
    async def get_valid_by_code(self, code: str) -> Optional[PasswordReset]:
        """Get a valid (not expired, not used) password reset by code."""
        reset = await self.get_by_code(code)
        if reset and reset.is_valid():
            return reset
        return None
    
    async def get_latest_by_email(self, email: str) -> Optional[PasswordReset]:
        """Get the latest password reset for an email."""
        result = await self.db.execute(
            select(PasswordReset)
            .where(PasswordReset.email == email)
            .order_by(PasswordReset.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def create_reset_code(
        self,
        user_id: int,
        email: str,
        code: str
    ) -> PasswordReset:
        """Create a new password reset code."""
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )
        
        reset = PasswordReset(
            user_id=user_id,
            email=email,
            code=code,
            expires_at=expires_at
        )
        
        self.db.add(reset)
        await self.db.commit()
        await self.db.refresh(reset)
        return reset
    
    async def mark_as_used(self, reset_id: int) -> Optional[PasswordReset]:
        """Mark a password reset code as used."""
        reset = await self.get_by_id(reset_id)
        if not reset:
            return None
        
        reset.used_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(reset)
        return reset
    
    async def invalidate_user_resets(self, user_id: int) -> None:
        """Invalidate all unused reset codes for a user."""
        result = await self.db.execute(
            select(PasswordReset).where(
                and_(
                    PasswordReset.user_id == user_id,
                    PasswordReset.used_at == None
                )
            )
        )
        resets = result.scalars().all()
        
        for reset in resets:
            reset.used_at = datetime.utcnow()
        
        await self.db.commit()
    
    async def cleanup_expired(self) -> int:
        """Delete expired reset codes. Returns count of deleted records."""
        expired_codes = await self.db.execute(
            select(PasswordReset).where(
                PasswordReset.expires_at < datetime.utcnow()
            )
        )
        count = 0
        for reset in expired_codes.scalars().all():
            await self.db.delete(reset)
            count += 1
        
        await self.db.commit()
        return count

