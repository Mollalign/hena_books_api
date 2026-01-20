"""
Analytics API Routes

Endpoints for tracking reading sessions and viewing analytics.
"""

from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.models.user import User
from app.schemas.analytics import (
    ReadingSessionCreate,
    ReadingSessionUpdate,
    ReadingSessionResponse,
    OverviewStats,
    BookStats,
    ReaderActivity,
)
from app.services.reading_session_service import ReadingSessionService
from app.services.analytics import AnalyticsService

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
    session_service = ReadingSessionService(db)
    session = await session_service.start_session(
        user_id=current_user.id,
        book_id=session_data.book_id
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
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
    session_service = ReadingSessionService(db)
    session = await session_service.update_session_progress(
        session_id=session_id,
        user_id=current_user.id,
        last_page_read=update_data.last_page_read,
        time_spent_seconds=update_data.time_spent_seconds
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session not found"
        )
    
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
    session_service = ReadingSessionService(db)
    session = await session_service.end_session(
        session_id=session_id,
        user_id=current_user.id
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading session not found"
        )
    
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
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_overview_stats()


@router.get("/admin/analytics/books", response_model=list[BookStats], tags=["Admin Analytics"])
async def get_book_statistics(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get reading statistics for all books.
    """
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_all_book_statistics()


@router.get("/admin/analytics/readers", response_model=list[ReaderActivity], tags=["Admin Analytics"])
async def get_reader_activity(
    limit: int = 20,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent reader activity.
    """
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_reader_activity(limit=limit)
