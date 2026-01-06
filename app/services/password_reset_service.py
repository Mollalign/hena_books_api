"""
Password Reset Service

Business logic layer for password reset operations.
Handles forgot password flow with email code verification.
"""

import secrets
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.security import hash_password
from app.utils.email import send_password_reset_code
from app.core.config import settings


class PasswordResetService:
    """Service for password reset business logic."""
    
    def __init__(self, db: AsyncSession):
        self.reset_repo = PasswordResetRepository(db)
        self.user_repo = UserRepository(db)
    
    def _generate_reset_code(self) -> str:
        """Generate a 6-digit random code."""
        return f"{secrets.randbelow(1000000):06d}"
    
    async def request_password_reset(self, email: str) -> dict:
        """
        Request a password reset by sending a code to the user's email.
        
        Args:
            email: User email address
            
        Returns:
            dict with message and expires_in_minutes
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)
        
        # Always return success message (security: don't reveal if email exists)
        expires_in_minutes = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        
        if not user:
            # Return success even if user doesn't exist (security best practice)
            return {
                "message": "If an account with that email exists, a reset code has been sent.",
                "expires_in_minutes": expires_in_minutes
            }
        
        if not user.is_active:
            # Return success even if account is inactive
            return {
                "message": "If an account with that email exists, a reset code has been sent.",
                "expires_in_minutes": expires_in_minutes
            }
        
        # Invalidate any existing unused reset codes for this user
        await self.reset_repo.invalidate_user_resets(user.id)
        
        # Generate new reset code
        code = self._generate_reset_code()
        
        # Create reset record
        reset = await self.reset_repo.create_reset_code(
            user_id=user.id,
            email=user.email,
            code=code
        )
        
        # Send email with code
        send_password_reset_code(
            email=user.email,
            code=code,
            expires_in_minutes=expires_in_minutes
        )
        
        return {
            "message": "If an account with that email exists, a reset code has been sent.",
            "expires_in_minutes": expires_in_minutes
        }
    
    async def verify_reset_code(self, email: str, code: str) -> dict:
        """
        Verify a password reset code.
        
        Args:
            email: User email address
            code: 6-digit reset code
            
        Returns:
            dict with valid status and message
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)
        if not user:
            return {
                "valid": False,
                "message": "Invalid email or code."
            }
        
        # Get valid reset code
        reset = await self.reset_repo.get_valid_by_code(code)
        
        if not reset:
            return {
                "valid": False,
                "message": "Invalid or expired reset code."
            }
        
        # Verify email matches
        if reset.email != email or reset.user_id != user.id:
            return {
                "valid": False,
                "message": "Invalid email or code."
            }
        
        return {
            "valid": True,
            "message": "Reset code is valid."
        }
    
    async def reset_password(
        self,
        email: str,
        code: str,
        new_password: str
    ) -> Optional[User]:
        """
        Reset user password using a valid reset code.
        
        Args:
            email: User email address
            code: 6-digit reset code
            new_password: New password
            
        Returns:
            Updated User if successful, None otherwise
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        
        # Get valid reset code
        reset = await self.reset_repo.get_valid_by_code(code)
        
        if not reset:
            return None
        
        # Verify email and user match
        if reset.email != email or reset.user_id != user.id:
            return None
        
        # Update password
        user.password_hash = hash_password(new_password)
        await self.reset_repo.db.commit()
        await self.reset_repo.db.refresh(user)
        
        # Mark reset code as used
        await self.reset_repo.mark_as_used(reset.id)
        
        # Invalidate any other unused reset codes for this user
        await self.reset_repo.invalidate_user_resets(user.id)
        
        return user

