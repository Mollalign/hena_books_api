"""
Repository Layer

Data access layer following the Repository pattern.
All database operations are encapsulated here.
"""

from app.repositories.base import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.book_repository import BookRepository
from app.repositories.reading_session_repository import ReadingSessionRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "BookRepository",
    "ReadingSessionRepository",
]

