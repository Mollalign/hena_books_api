"""
Security and Authentication Module

This module provides:
- Password hashing and verification (bcrypt)
- JWT token creation and validation
- Token refresh functionality
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
from fastapi import HTTPException, status

from app.core.config import settings

# ----------------------------------------------------
# Password Hashing
# ----------------------------------------------------

def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password (will be encoded to bytes)
        
    Returns:
        Hashed password string (bcrypt hash)
        
    Example:
        >>> hashed = hash_password("my_password")
        >>> verify_password("my_password", hashed)
        True
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string (bcrypt hash is already a string when decoded)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database (bcrypt hash)
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> verify_password("my_password", "$2b$12$...")
        True
    """
    try:
        # Convert to bytes
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        # Verify password
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# ----------------------------------------------------
# JWT Token Management
# ----------------------------------------------------

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing token payload (typically user_id, email, etc.)
        expires_delta: Optional custom expiration time. If None, uses ACCESS_TOKEN_EXPIRE_MINUTES
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token({"sub": "user@example.com", "user_id": str(user.id)})
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Dictionary containing token payload
        
    Returns:
        Encoded JWT refresh token string
        
    Example:
        >>> refresh_token = create_refresh_token({"sub": "user@example.com", "user_id": str(user.id)})
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload as dictionary
        
    Raises:
        HTTPException: If token is invalid, expired, or malformed
        
    Example:
        >>> payload = decode_token(token)
        >>> user_id = payload.get("user_id")
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID as string, or None if not found/invalid
        
    Example:
        >>> user_id = get_user_id_from_token(token)
    """
    try:
        payload = decode_token(token)
        # Try different possible keys for user ID
        user_id = payload.get("user_id") or payload.get("sub") or payload.get("id")
        return str(user_id) if user_id else None
    except HTTPException:
        return None


def get_email_from_token(token: str) -> Optional[str]:
    """
    Extract email from a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Email as string, or None if not found/invalid
        
    Example:
        >>> email = get_email_from_token(token)
    """
    try:
        payload = decode_token(token)
        email = payload.get("email") or payload.get("sub")
        return email
    except HTTPException:
        return None


def create_token_pair(
    user_id: str, 
    email: str, 
    account_id: Optional[str] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: User's UUID as string
        email: User's email address
        account_id: Optional account UUID as string (for SaaS multi-tenancy)
        additional_claims: Optional additional claims to include in tokens
        
    Returns:
        Dictionary with 'access_token' and 'refresh_token'
        
    Example:
        >>> tokens = create_token_pair(str(user.id), user.email, account_id=str(account.id))
        >>> access_token = tokens["access_token"]
        >>> refresh_token = tokens["refresh_token"]
    """
    token_data = {
        "user_id": user_id,
        "sub": email,  # Standard JWT claim for subject
        "email": email
    }
    
    # Add account_id if provided (for SaaS multi-tenancy)
    if account_id:
        token_data["account_id"] = account_id
    
    if additional_claims:
        token_data.update(additional_claims)
    
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def verify_token_type(token: str, expected_type: str = "access") -> bool:
    """
    Verify that a token is of the expected type (access or refresh).
    
    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        True if token type matches, False otherwise
        
    Example:
        >>> is_access = verify_token_type(token, "access")
    """
    try:
        payload = decode_token(token)
        token_type = payload.get("type")
        return token_type == expected_type
    except HTTPException:
        return False

