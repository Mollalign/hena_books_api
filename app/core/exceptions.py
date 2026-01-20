"""
Custom Exceptions Module

Centralized exception handling for the Hena Books API.
Provides clear, consistent error responses across the application.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class HenaException(HTTPException):
    """Base exception for all Hena Books API errors."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# =============================================================================
# Authentication Exceptions
# =============================================================================

class AuthenticationError(HenaException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class InvalidTokenError(AuthenticationError):
    """Raised when token is invalid or expired."""
    
    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(detail=detail)


class TokenExpiredError(AuthenticationError):
    """Raised when token has expired."""
    
    def __init__(self):
        super().__init__(detail="Token has expired")


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are incorrect."""
    
    def __init__(self):
        super().__init__(detail="Incorrect email or password")


# =============================================================================
# Authorization Exceptions
# =============================================================================

class AuthorizationError(HenaException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class AdminRequiredError(AuthorizationError):
    """Raised when admin access is required."""
    
    def __init__(self):
        super().__init__(detail="Admin access required")


# =============================================================================
# Resource Exceptions
# =============================================================================

class NotFoundError(HenaException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str = "Resource", detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or f"{resource} not found"
        )


class BookNotFoundError(NotFoundError):
    """Raised when a book is not found."""
    
    def __init__(self):
        super().__init__(resource="Book")


class UserNotFoundError(NotFoundError):
    """Raised when a user is not found."""
    
    def __init__(self):
        super().__init__(resource="User")


class SessionNotFoundError(NotFoundError):
    """Raised when a reading session is not found."""
    
    def __init__(self):
        super().__init__(resource="Reading session")


# =============================================================================
# Validation Exceptions
# =============================================================================

class ValidationError(HenaException):
    """Raised when validation fails."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class DuplicateEmailError(ValidationError):
    """Raised when email is already registered."""
    
    def __init__(self):
        super().__init__(detail="Email already registered")


class InvalidFileTypeError(ValidationError):
    """Raised when file type is not allowed."""
    
    def __init__(self, allowed_types: str = "PDF"):
        super().__init__(detail=f"Invalid file type. Allowed: {allowed_types}")


class InvalidResetCodeError(ValidationError):
    """Raised when password reset code is invalid."""
    
    def __init__(self):
        super().__init__(detail="Invalid or expired reset code")


# =============================================================================
# Server Exceptions
# =============================================================================

class ServerError(HenaException):
    """Raised when an internal server error occurs."""
    
    def __init__(self, detail: str = "An unexpected error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class FileUploadError(ServerError):
    """Raised when file upload fails."""
    
    def __init__(self, detail: str = "Failed to upload file"):
        super().__init__(detail=detail)


class DatabaseError(ServerError):
    """Raised when a database operation fails."""
    
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(detail=detail)


class ExternalServiceError(HenaException):
    """Raised when an external service (e.g., Cloudinary) fails."""
    
    def __init__(self, service: str, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail or f"External service error: {service}"
        )
