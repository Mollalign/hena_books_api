"""
Reading Session Repository

Data access layer for ReadingSession model.
All reading session-related database operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.repositories.base import BaseRepository
from app.models.reading_session import ReadingSession


class ReadingSessionRepository(BaseRepository[ReadingSession]):
    """Repository for ReadingSession model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(ReadingSession, db)
    
    async def get_by_id(self, session_id: int) -> Optional[ReadingSession]:
        """Get a reading session by ID."""
        result = await self.db.execute(
            select(ReadingSession).where(ReadingSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_and_book(
        self,
        user_id: UUID,
        book_id: UUID
    ) -> Optional[ReadingSession]:
        """Get a reading session by user and book. Returns most recent if multiple exist."""
        result = await self.db.execute(
            select(ReadingSession).where(
                and_(
                    ReadingSession.user_id == user_id,
                    ReadingSession.book_id == book_id
                )
            ).order_by(desc(ReadingSession.started_at)).limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_active_session(
        self,
        user_id: UUID,
        book_id: UUID
    ) -> Optional[ReadingSession]:
        """Get an active (not ended) reading session. Returns most recent if multiple exist."""
        result = await self.db.execute(
            select(ReadingSession).where(
                and_(
                    ReadingSession.user_id == user_id,
                    ReadingSession.book_id == book_id,
                    ReadingSession.ended_at == None
                )
            ).order_by(desc(ReadingSession.started_at)).limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_user_sessions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReadingSession]:
        """Get all reading sessions for a user."""
        result = await self.db.execute(
            select(ReadingSession)
            .where(ReadingSession.user_id == user_id)
            .order_by(ReadingSession.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_book_sessions(
        self,
        book_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReadingSession]:
        """Get all reading sessions for a book."""
        result = await self.db.execute(
            select(ReadingSession)
            .where(ReadingSession.book_id == book_id)
            .order_by(ReadingSession.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def create_session(
        self,
        user_id: UUID,
        book_id: UUID
    ) -> ReadingSession:
        """Create a new reading session."""
        session = ReadingSession(
            user_id=user_id,
            book_id=book_id
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def update_session(
        self,
        session_id: int,
        last_page_read: Optional[int] = None,
        time_spent_seconds: Optional[int] = None,
        ended_at: Optional[datetime] = None
    ) -> Optional[ReadingSession]:
        """Update a reading session."""
        session = await self.get_by_id(session_id)
        if not session:
            return None
        
        if last_page_read is not None:
            session.last_page_read = last_page_read
        if time_spent_seconds is not None:
            session.total_time_seconds += time_spent_seconds
        if ended_at is not None:
            session.ended_at = ended_at
        
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def get_book_statistics(self, book_id: UUID) -> dict:
        """Get reading statistics for a book."""
        result = await self.db.execute(
            select(
                func.count(func.distinct(ReadingSession.user_id)).label("total_readers"),
                func.count(ReadingSession.id).label("total_sessions"),
                func.coalesce(func.sum(ReadingSession.total_time_seconds), 0).label("total_time"),
                func.coalesce(func.avg(ReadingSession.last_page_read), 0).label("avg_pages")
            ).where(ReadingSession.book_id == book_id)
        )
        stats = result.first()
        return {
            "total_readers": stats.total_readers or 0,
            "total_sessions": stats.total_sessions or 0,
            "total_time": stats.total_time or 0,
            "avg_pages": round(stats.avg_pages or 0, 1)
        }
    
    async def get_platform_statistics(self) -> dict:
        """Get overall platform reading statistics."""
        result = await self.db.execute(
            select(
                func.count(ReadingSession.id).label("total_sessions"),
                func.coalesce(func.sum(ReadingSession.total_time_seconds), 0).label("total_time")
            )
        )
        stats = result.first()
        return {
            "total_sessions": stats.total_sessions or 0,
            "total_time": stats.total_time or 0
        }
    
    async def get_active_readers_count(self, since: datetime) -> int:
        """Get count of active readers since a given datetime."""
        result = await self.db.execute(
            select(func.count(func.distinct(ReadingSession.user_id))).where(
                ReadingSession.started_at >= since
            )
        )
        return result.scalar() or 0
    
    async def get_most_popular_books(self, limit: int = 10) -> List[dict]:
        """Get most popular books by reader count."""
        from app.models.book import Book
        result = await self.db.execute(
            select(
                Book.id,
                Book.title,
                Book.cover_url,
                func.count(func.distinct(ReadingSession.user_id)).label("readers"),
                func.count(ReadingSession.id).label("sessions"),
                func.coalesce(func.sum(ReadingSession.total_time_seconds), 0).label("time")
            )
            .join(ReadingSession, ReadingSession.book_id == Book.id, isouter=True)
            .group_by(Book.id)
            .order_by(func.count(func.distinct(ReadingSession.user_id)).desc())
            .limit(limit)
        )
        return [dict(row._mapping) for row in result.all()]
    
    async def get_reader_activity(self, limit: int = 20) -> List[dict]:
        """Get recent reader activity."""
        from app.models.user import User
        result = await self.db.execute(
            select(
                User.id,
                User.name,
                User.email,
                func.count(func.distinct(ReadingSession.book_id)).label("books"),
                func.coalesce(func.sum(ReadingSession.total_time_seconds), 0).label("time"),
                func.max(ReadingSession.started_at).label("last_active")
            )
            .join(ReadingSession, ReadingSession.user_id == User.id)
            .group_by(User.id)
            .order_by(func.max(ReadingSession.started_at).desc())
            .limit(limit)
        )
        return [dict(row._mapping) for row in result.all()]

