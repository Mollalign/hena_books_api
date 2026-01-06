"""
Analytics API Routes

Endpoints for tracking reading sessions and viewing analytics.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.models.user import User
from app.models.book import Book
from app.models.reading_session import ReadingSession
from app.schemas.analytics import (
    ReadingSessionCreate,
    ReadingSessionUpdate,
    ReadingSessionResponse,
    OverviewStats,
    BookStats,
    ReaderActivity,
    DailyTrend,
    AnalyticsResponse,
)

router = APIRouter(tags=["Analytics"])


# =============================================================================
# READING SESSION ENDPOINTS (Authenticated Users)
# =============================================================================

@router.post("/reading/start", response_model=ReadingSessionResponse, tags=["Reading"])
async def start_reading_session(
    session_data: ReadingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new reading session for a book.
    """
    # Check if book exists and is published
    result = await db.execute(
        select(Book).where(
            and_(Book.id == session_data.book_id, Book.is_published == True)
        )
    )
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Check for existing active session
    existing = await db.execute(
        select(ReadingSession).where(
            and_(
                ReadingSession.user_id == current_user.id,
                ReadingSession.book_id == session_data.book_id,
                ReadingSession.ended_at == None
            )
        )
    )
    active_session = existing.scalar_one_or_none()
    
    if active_session:
        # Return existing session instead of creating new
        return active_session
    
    # Create new session
    session = ReadingSession(
        user_id=current_user.id,
        book_id=session_data.book_id
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return session


@router.put("/reading/{session_id}/update", response_model=ReadingSessionResponse, tags=["Reading"])
async def update_reading_progress(
    session_id: int,
    update_data: ReadingSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update reading progress (page number and time spent).
    """
    result = await db.execute(
        select(ReadingSession).where(
            and_(
                ReadingSession.id == session_id,
                ReadingSession.user_id == current_user.id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session not found"
        )
    
    session.last_page_read = update_data.last_page_read
    session.total_time_seconds += update_data.time_spent_seconds
    
    await db.commit()
    await db.refresh(session)
    
    return session


@router.post("/reading/{session_id}/end", response_model=ReadingSessionResponse, tags=["Reading"])
async def end_reading_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    End a reading session.
    """
    result = await db.execute(
        select(ReadingSession).where(
            and_(
                ReadingSession.id == session_id,
                ReadingSession.user_id == current_user.id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session not found"
        )
    
    session.ended_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(session)
    
    return session


# =============================================================================
# ANALYTICS ENDPOINTS (Admin Only)
# =============================================================================

@router.get("/admin/analytics/overview", response_model=OverviewStats, tags=["Admin Analytics"])
async def get_analytics_overview(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall platform statistics.
    """
    # Total users (excluding admin)
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar() or 0
    
    # Total books
    books_result = await db.execute(select(func.count(Book.id)))
    total_books = books_result.scalar() or 0
    
    # Total reading sessions and time
    sessions_result = await db.execute(
        select(
            func.count(ReadingSession.id).label("total_sessions"),
            func.coalesce(func.sum(ReadingSession.total_time_seconds), 0).label("total_time")
        )
    )
    sessions_data = sessions_result.first()
    
    # Active readers today
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    active_today_result = await db.execute(
        select(func.count(func.distinct(ReadingSession.user_id))).where(
            ReadingSession.started_at >= today_start
        )
    )
    active_today = active_today_result.scalar() or 0
    
    # Active readers this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_week_result = await db.execute(
        select(func.count(func.distinct(ReadingSession.user_id))).where(
            ReadingSession.started_at >= week_ago
        )
    )
    active_week = active_week_result.scalar() or 0
    
    # Most popular book
    popular_result = await db.execute(
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
        .limit(1)
    )
    popular = popular_result.first()
    
    most_popular = None
    if popular and popular.readers > 0:
        most_popular = BookStats(
            book_id=popular.id,
            title=popular.title,
            cover_url=popular.cover_url,
            total_readers=popular.readers,
            total_sessions=popular.sessions,
            total_reading_time_hours=round(popular.time / 3600, 2),
            average_pages_read=0  # Would need more complex query
        )
    
    return OverviewStats(
        total_users=total_users,
        total_books=total_books,
        total_reading_sessions=sessions_data.total_sessions,
        total_reading_time_hours=round(sessions_data.total_time / 3600, 2),
        active_readers_today=active_today,
        active_readers_week=active_week,
        most_popular_book=most_popular
    )


@router.get("/admin/analytics/books", response_model=list[BookStats], tags=["Admin Analytics"])
async def get_book_statistics(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get reading statistics for all books.
    """
    result = await db.execute(
        select(
            Book.id,
            Book.title,
            Book.cover_url,
            func.count(func.distinct(ReadingSession.user_id)).label("readers"),
            func.count(ReadingSession.id).label("sessions"),
            func.coalesce(func.sum(ReadingSession.total_time_seconds), 0).label("time"),
            func.coalesce(func.avg(ReadingSession.last_page_read), 0).label("avg_pages")
        )
        .join(ReadingSession, ReadingSession.book_id == Book.id, isouter=True)
        .group_by(Book.id)
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


@router.get("/admin/analytics/readers", response_model=list[ReaderActivity], tags=["Admin Analytics"])
async def get_reader_activity(
    limit: int = 20,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent reader activity.
    """
    result = await db.execute(
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
    
    readers = result.all()
    
    return [
        ReaderActivity(
            user_id=r.id,
            user_name=r.name,
            email=r.email,
            books_read=r.books,
            total_reading_time_hours=round(r.time / 3600, 2),
            last_active=r.last_active
        )
        for r in readers
    ]
