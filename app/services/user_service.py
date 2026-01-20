"""
User Service

Business logic layer for user operations.
Handles user management operations.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.security import hash_password


class UserService:
    """Service for user business logic."""
    
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        return await self.user_repo.get_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return await self.user_repo.get_by_email(email)
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users."""
        return await self.user_repo.get_all_users(skip=skip, limit=limit)
    
    async def update_user_profile(
        self,
        user_id: UUID,
        name: Optional[str] = None,
        password: Optional[str] = None
    ) -> Optional[User]:
        """Update user profile."""
        update_data = {}
        if name:
            update_data["name"] = name
        if password:
            update_data["password_hash"] = hash_password(password)
        
        if not update_data:
            return await self.user_repo.get_by_id(user_id)
        
        return await self.user_repo.update_user(user_id, **update_data)
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete a user."""
        return await self.user_repo.delete_user(user_id)

