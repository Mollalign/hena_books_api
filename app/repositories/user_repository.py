"""
User Repository

Data access layer for User model.
All user-related database operations.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.repositories.base import BaseRepository
from app.models.user import User, UserRole


class UserRepository(BaseRepository[User]):
    """Repository for User model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id_with_sessions(self, user_id: int) -> Optional[User]:
        """Get a user by ID with reading sessions loaded."""
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.reading_sessions))
        )
        return result.scalar_one_or_none()
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users ordered by creation date."""
        result = await self.db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def create_user(
        self,
        email: str,
        password_hash: str,
        name: str,
        role: UserRole = UserRole.USER,
        is_active: bool = True
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
            is_active=is_active
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields."""
        return await self.update(user_id, **kwargs)
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID."""
        return await self.delete(user_id)

