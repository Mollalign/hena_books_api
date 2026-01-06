"""
Schemas Package

Export all schemas for easy importing.
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
)
from app.schemas.auth import (
    LoginRequest,
    Token,
    TokenPayload,
    RefreshTokenRequest,
    PasswordChange,
)
from app.schemas.book import (
    BookBase,
    BookCreate,
    BookUpdate,
    BookResponse,
    BookDetailResponse,
    BookAdminResponse,
    BookListResponse,
)
from app.schemas.analytics import (
    BookStats,
    ReaderActivity,
    DailyTrend,
    OverviewStats,
    AnalyticsResponse,
    ReadingSessionCreate,
    ReadingSessionUpdate,
    ReadingSessionResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    # Auth
    "LoginRequest",
    "Token",
    "TokenPayload",
    "RefreshTokenRequest",
    "PasswordChange",
    # Book
    "BookBase",
    "BookCreate",
    "BookUpdate",
    "BookResponse",
    "BookDetailResponse",
    "BookAdminResponse",
    "BookListResponse",
    # Analytics
    "BookStats",
    "ReaderActivity",
    "DailyTrend",
    "OverviewStats",
    "AnalyticsResponse",
    "ReadingSessionCreate",
    "ReadingSessionUpdate",
    "ReadingSessionResponse",
]
