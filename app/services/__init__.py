"""
Services Layer

Business logic layer following the Service pattern.
All business logic is encapsulated here.
"""

from app.services.auth import AuthService
from app.services.user_service import UserService
from app.services.book_service import BookService
from app.services.reading_session_service import ReadingSessionService
from app.services.analytics import AnalyticsService
from app.services.cloudinary import (
    upload_book_file,
    upload_cover_image,
    delete_file,
    get_download_url,
)

__all__ = [
    "AuthService",
    "UserService",
    "BookService",
    "ReadingSessionService",
    "AnalyticsService",
    "upload_book_file",
    "upload_cover_image",
    "delete_file",
    "get_download_url",
]

