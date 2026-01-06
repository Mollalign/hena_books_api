"""
Reading Session Service

Business logic layer for reading session operations.
Handles reading session tracking and analytics.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.reading_session_repository import ReadingSessionRepository
from app.repositories.book_repository import BookRepository
from app.models.reading_session import ReadingSession


class ReadingSessionService:
    """Service for reading session business logic."""
    
    def __init__(self, db: AsyncSession):
        self.session_repo = ReadingSessionRepository(db)
        self.book_repo = BookRepository(db)
    
    async def start_session(
        self,
        user_id: int,
        book_id: int
    ) -> ReadingSession:
        """Start a new reading session or return existing active session."""
        # Check if book exists and is published
        book = await self.book_repo.get_published_by_id(book_id)
        if not book:
            return None
        
        # Check for existing active session
        active_session = await self.session_repo.get_active_session(
            user_id, book_id
        )
        if active_session:
            return active_session
        
        # Create new session
        return await self.session_repo.create_session(user_id, book_id)
    
    async def update_session_progress(
        self,
        session_id: int,
        user_id: int,
        last_page_read: Optional[int] = None,
        time_spent_seconds: Optional[int] = None
    ) -> Optional[ReadingSession]:
        """Update reading progress."""
        # Verify session belongs to user
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            return None
        
        return await self.session_repo.update_session(
            session_id,
            last_page_read=last_page_read,
            time_spent_seconds=time_spent_seconds
        )
    
    async def end_session(
        self,
        session_id: int,
        user_id: int
    ) -> Optional[ReadingSession]:
        """End a reading session."""
        # Verify session belongs to user
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            return None
        
        return await self.session_repo.update_session(
            session_id,
            ended_at=datetime.utcnow()
        )
    
    async def get_session_by_id(
        self,
        session_id: int,
        user_id: Optional[int] = None
    ) -> Optional[ReadingSession]:
        """Get a session by ID, optionally verifying user ownership."""
        session = await self.session_repo.get_by_id(session_id)
        if session and user_id and session.user_id != user_id:
            return None
        return session

