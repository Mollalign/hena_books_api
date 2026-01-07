from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import bcrypt

from jose import JWTError, jwt
from app.core.config import settings
from app.schemas.auth import TokenPayload


def _ensure_password_bytes(password: str, max_bytes: int = 72) -> bytes:
    """Ensure password doesn't exceed bcrypt's 72-byte limit."""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > max_bytes:
        # Truncate to 72 bytes
        return password_bytes[:max_bytes]
    return password_bytes


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    # Ensure password doesn't exceed bcrypt's 72-byte limit
    password_bytes = _ensure_password_bytes(password)
    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string (bcrypt hash is always valid UTF-8)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a bcrypt hash."""
    try:
        # Ensure password doesn't exceed bcrypt's 72-byte limit
        password_bytes = _ensure_password_bytes(plain_password)
        hashed_bytes = hashed_password.encode('utf-8')
        # Verify password
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, Exception) as e:
        # Log the error for debugging but don't expose it
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(user_id) -> str:
    """Create a new access token for a user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id) -> str:
    """Create a new refresh token for a user."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_tokens(user_id) -> Tuple[str, str]:
    """Create both access and refresh tokens."""
    return create_access_token(user_id), create_refresh_token(user_id)


def decode_token(token: str) -> Optional[TokenPayload]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None
