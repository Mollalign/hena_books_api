"""
Analytics Service

Business logic layer for analytics operations.
Handles reading statistics and platform analytics.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.reading_session_repository import ReadingSessionRepository
from app.repositories.book_repository import BookRepository
from app.repositories.user_repository import UserRepository
from app.schemas.analytics import (
    OverviewStats,
    BookStats,
    ReaderActivity,
    UserReadingStats,
)


class AnalyticsService:
    """Service for analytics business logic."""
    
    def __init__(self, db: AsyncSession):
        self.session_repo = ReadingSessionRepository(db)
        self.book_repo = BookRepository(db)
        self.user_repo = UserRepository(db)
        self.db = db
    
    async def get_user_reading_stats(self, user_id: UUID) -> UserReadingStats:
        """Get reading statistics for a specific user."""
        from app.models.reading_session import ReadingSession
        from sqlalchemy import select, func
        
        result = await self.db.execute(
            select(
                func.count(func.distinct(ReadingSession.book_id)).label("books_read"),
                func.coalesce(func.sum(ReadingSession.total_time_seconds), 0).label("total_time"),
                func.count(ReadingSession.id).label("total_sessions")
            )
            .where(ReadingSession.user_id == user_id)
        )
        
        stats = result.first()
        
        return UserReadingStats(
            total_books_read=stats.books_read if stats else 0,
            total_reading_time_hours=round((stats.total_time if stats else 0) / 3600, 2),
            total_sessions=stats.total_sessions if stats else 0
        )
    
    async def get_book_statistics(self, book_id: int) -> dict:
        """Get reading statistics for a specific book."""
        return await self.session_repo.get_book_statistics(book_id)
    
    async def get_overview_stats(self) -> OverviewStats:
        """Get overall platform statistics."""
        # Total users
        total_users = await self.user_repo.count()
        
        # Total books
        total_books = await self.book_repo.count()
        
        # Reading session statistics
        session_stats = await self.session_repo.get_platform_statistics()
        
        # Active readers today
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        active_today = await self.session_repo.get_active_readers_count(today_start)
        
        # Active readers this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_week = await self.session_repo.get_active_readers_count(week_ago)
        
        # Most popular book
        popular_books = await self.session_repo.get_most_popular_books(limit=1)
        most_popular = None
        if popular_books and popular_books[0]["readers"] > 0:
            book_data = popular_books[0]
            most_popular = BookStats(
                book_id=book_data["id"],
                title=book_data["title"],
                cover_url=book_data["cover_url"],
                total_readers=book_data["readers"],
                total_sessions=book_data["sessions"],
                total_reading_time_hours=round(book_data["time"] / 3600, 2),
                average_pages_read=0  # Would need more complex query
            )
        
        return OverviewStats(
            total_users=total_users,
            total_books=total_books,
            total_reading_sessions=session_stats["total_sessions"],
            total_reading_time_hours=round(session_stats["total_time"] / 3600, 2),
            active_readers_today=active_today,
            active_readers_week=active_week,
            most_popular_book=most_popular
        )
    
    async def get_all_book_statistics(self) -> List[BookStats]:
        """Get reading statistics for all books."""
        from app.models.reading_session import ReadingSession
        from sqlalchemy import select, func
        
        # Access db through one of the repositories
        result = await self.book_repo.db.execute(
            select(
                self.book_repo.model.id,
                self.book_repo.model.title,
                self.book_repo.model.cover_url,
                func.count(func.distinct(ReadingSession.user_id)).label("readers"),
                func.count(ReadingSession.id).label("sessions"),
                func.coalesce(func.sum(ReadingSession.total_time_seconds), 0).label("time"),
                func.coalesce(func.avg(ReadingSession.last_page_read), 0).label("avg_pages")
            )
            .join(ReadingSession, ReadingSession.book_id == self.book_repo.model.id, isouter=True)
            .group_by(self.book_repo.model.id)
            .order_by(func.count(func.distinct(ReadingSession.user_id)).desc())
        )
        
        books = result.all()
        
        return [
            BookStats(
                book_id=b.id,
                title=b.title,
                cover_url=b.cover_url,
                total_readers=b.readers,
                total_sessions=b.sessions,
                total_reading_time_hours=round(b.time / 3600, 2),
                average_pages_read=round(b.avg_pages, 1)
            )
            for b in books
        ]
    
    async def get_reader_activity(self, limit: int = 20) -> List[ReaderActivity]:
        """Get recent reader activity."""
        activity_data = await self.session_repo.get_reader_activity(limit=limit)
        
        return [
            ReaderActivity(
                user_id=r["id"],
                user_name=r["name"],
                email=r["email"],
                books_read=r["books"],
                total_reading_time_hours=round(r["time"] / 3600, 2),
                last_active=r["last_active"]
            )
            for r in activity_data
        ]

