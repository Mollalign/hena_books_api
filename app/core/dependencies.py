"""
Dependency Injection Module

This module provides FastAPI dependencies for:
- Database sessions
- Authentication
- Current user
- Authorization
"""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.core.security import decode_token, get_user_id_from_token
from app.models.user import User

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


# Database session dependency - use get_db directly from database module
get_database_session = get_db


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_database_session)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Usage:
        @router.get("/profile")
        async def get_profile(current_user: User = Depends(get_current_user)):
            return current_user
    
    Raises:
        HTTPException: 401 if token is missing, invalid, or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token and extract user ID
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user_id = payload.get("user_id") or payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Convert to UUID if it's a string
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            # If user_id is email, query by email instead
            email = payload.get("email") or payload.get("sub")
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            stmt = select(User).where(User.email == email)
        else:
            stmt = select(User).where(User.id == user_uuid)
        
        # Query user from database
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user.
    Ensures user account is active.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(get_current_active_user)):
            ...
    
    Raises:
        HTTPException: 403 if user account is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user
