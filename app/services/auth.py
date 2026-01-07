"""
Authentication Service

Handles JWT token generation, validation, and password hashing.
"""

from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.models.user import User, UserRole
from app.core.security import verify_password, create_access_token, create_refresh_token, create_tokens, hash_password


class AuthService:
    """Service for authentication business logic."""
    
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        return await self.user_repo.get_by_email(email)
    
    async def get_user_by_id(self, user_id) -> Optional[User]:
        """Get a user by ID (UUID)."""
        # Handle both UUID and string UUID
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except (ValueError, TypeError):
                return None
        return await self.user_repo.get_by_id(user_id)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user
    
    async def create_user(
        self,
        email: str,
        password: str,
        name: str,
        role: UserRole = UserRole.USER
    ) -> User:
        """Create a new user with hashed password."""
        return await self.user_repo.create_user(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role=role
        )
    
    async def create_admin_user(
        self,
        email: str,
        password: str,
        name: str
    ) -> User:
        """Create an admin user (use during initial setup)."""
        # Check if admin already exists
        existing = await self.user_repo.get_by_email(email)
        if existing:
            return existing
        return await self.create_user(email, password, name, UserRole.ADMIN)


# Legacy functions for backward compatibility (will be removed after updating endpoints)
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user by email address (legacy)."""
    service = AuthService(db)
    return await service.get_user_by_email(email)


async def get_user_by_id(db: AsyncSession, user_id) -> Optional[User]:
    """Get a user by ID (legacy)."""
    service = AuthService(db)
    return await service.get_user_by_id(user_id)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password (legacy)."""
    service = AuthService(db)
    return await service.authenticate_user(email, password)


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    name: str,
    role: UserRole = UserRole.USER
) -> User:
    """Create a new user with hashed password (legacy)."""
    service = AuthService(db)
    return await service.create_user(email, password, name, role)


async def create_admin_user(
    db: AsyncSession,
    email: str,
    password: str,
    name: str
) -> User:
    """Create an admin user (legacy)."""
    service = AuthService(db)
    return await service.create_admin_user(email, password, name)
