"""
Authentication Service

Handles JWT token generation, validation, and password hashing.
"""

from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.core.security import verify_password, create_access_token, create_refresh_token, create_tokens, hash_password



async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get a user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    name: str,
    role: UserRole = UserRole.USER
) -> User:
    """Create a new user with hashed password."""
    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name,
        role=role
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_admin_user(
    db: AsyncSession,
    email: str,
    password: str,
    name: str
) -> User:
    """Create an admin user (use during initial setup)."""
    # Check if admin already exists
    existing = await get_user_by_email(db, email)
    if existing:
        return existing
    return await create_user(db, email, password, name, UserRole.ADMIN)
