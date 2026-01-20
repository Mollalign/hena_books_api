"""
Authentication Service

Handles user authentication, registration, and token management.
"""

from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.models.user import User, UserRole
from app.core.security import (
    verify_password,
    hash_password,
    create_tokens,
    create_access_token,
    create_refresh_token,
)
from app.core.exceptions import (
    InvalidCredentialsError,
    UserNotFoundError,
    DuplicateEmailError,
)


class AuthService:
    """
    Service for authentication business logic.
    
    Handles:
    - User authentication
    - User registration
    - Token generation
    """
    
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
    
    # =========================================================================
    # USER RETRIEVAL
    # =========================================================================
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        return await self.user_repo.get_by_email(email)
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        return await self.user_repo.get_by_id(user_id)
    
    async def get_active_user_by_id(self, user_id: UUID) -> User:
        """
        Get an active user by ID.
        
        Raises:
            UserNotFoundError: If user not found or inactive
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UserNotFoundError()
        return user
    
    # =========================================================================
    # AUTHENTICATION
    # =========================================================================
    
    async def authenticate(self, email: str, password: str) -> User:
        """
        Authenticate a user by email and password.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            Authenticated user
            
        Raises:
            InvalidCredentialsError: If credentials are incorrect or user is inactive
        """
        user = await self.user_repo.get_by_email(email)
        
        if not user:
            raise InvalidCredentialsError()
        
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        
        if not user.is_active:
            raise InvalidCredentialsError()
        
        return user
    
    async def authenticate_and_create_tokens(
        self,
        email: str,
        password: str
    ) -> Tuple[User, str, str]:
        """
        Authenticate user and create JWT tokens.
        
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            InvalidCredentialsError: If authentication fails
        """
        user = await self.authenticate(email, password)
        access_token, refresh_token = create_tokens(user.id)
        return user, access_token, refresh_token
    
    # =========================================================================
    # REGISTRATION
    # =========================================================================
    
    async def register_user(
        self,
        email: str,
        password: str,
        name: str
    ) -> User:
        """
        Register a new user.
        
        Args:
            email: User's email address
            password: Plain text password
            name: User's display name
            
        Returns:
            Newly created user
            
        Raises:
            DuplicateEmailError: If email already exists
        """
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise DuplicateEmailError()
        
        return await self.user_repo.create_user(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role=UserRole.USER
        )
    
    async def create_admin_user(
        self,
        email: str,
        password: str,
        name: str
    ) -> User:
        """
        Create an admin user (for initial setup).
        
        If user already exists, returns existing user.
        """
        existing = await self.user_repo.get_by_email(email)
        if existing:
            return existing
        
        return await self.user_repo.create_user(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role=UserRole.ADMIN
        )
    
    # =========================================================================
    # PASSWORD MANAGEMENT
    # =========================================================================
    
    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> User:
        """
        Change a user's password.
        
        Raises:
            UserNotFoundError: If user not found
            InvalidCredentialsError: If current password is incorrect
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError()
        
        return await self.user_repo.update_user(
            user_id,
            password_hash=hash_password(new_password)
        )
    
    async def reset_password(self, user_id: UUID, new_password: str) -> User:
        """
        Reset a user's password (admin or reset flow).
        
        Raises:
            UserNotFoundError: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        
        return await self.user_repo.update_user(
            user_id,
            password_hash=hash_password(new_password)
        )
