"""
API Dependencies

Dependency injection for authentication and authorization.
Provides reusable dependencies for route handlers.
"""

from typing import Optional
from uuid import UUID
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    AdminRequiredError,
    UserNotFoundError,
)
from app.models.user import User, UserRole
from app.services.auth import AuthService


# JWT Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user": user.email}
    
    Raises:
        AuthenticationError: If no token provided
        InvalidTokenError: If token is invalid or expired
        UserNotFoundError: If user not found or inactive
    """
    if not credentials:
        raise AuthenticationError("Authentication required")
    
    # Decode and validate token
    payload = decode_token(credentials.credentials)
    if not payload:
        raise InvalidTokenError()
    
    if payload.type != "access":
        raise InvalidTokenError("Invalid token type. Access token required.")
    
    # Parse user ID from token
    try:
        user_id = UUID(payload.sub)
    except (ValueError, TypeError):
        raise InvalidTokenError("Invalid user ID in token")
    
    # Fetch user from database
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    
    if not user:
        raise UserNotFoundError()
    
    if not user.is_active:
        raise AuthenticationError("Account is inactive")
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    
    Useful for endpoints that work with or without authentication.
    
    Usage:
        @router.get("/public")
        async def public_route(user: Optional[User] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello, {user.name}!"}
            return {"message": "Hello, guest!"}
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except Exception:
        return None


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current user and verify they have admin role.
    
    Usage:
        @router.get("/admin-only")
        async def admin_route(admin: User = Depends(get_admin_user)):
            return {"admin": admin.email}
    
    Raises:
        AdminRequiredError: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise AdminRequiredError()
    return current_user


# =============================================================================
# UTILITY DEPENDENCIES
# =============================================================================

def get_pagination_params(
    page: int = 1,
    per_page: int = 12
) -> dict:
    """
    Get pagination parameters with defaults and validation.
    
    Usage:
        @router.get("/items")
        async def list_items(pagination: dict = Depends(get_pagination_params)):
            page = pagination["page"]
            per_page = pagination["per_page"]
    """
    # Clamp values to reasonable ranges
    page = max(1, page)
    per_page = max(1, min(50, per_page))
    
    return {
        "page": page,
        "per_page": per_page,
        "skip": (page - 1) * per_page
    }
