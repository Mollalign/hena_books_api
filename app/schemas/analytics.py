"""
Analytics Schemas

Pydantic models for analytics responses.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class BookStats(BaseModel):
    """Statistics for a single book."""
    book_id: int
    title: str
    cover_url: Optional[str] = None
    total_readers: int
    total_sessions: int
    total_reading_time_hours: float
    average_pages_read: float


class ReaderActivity(BaseModel):
    """Activity record for a single reader."""
    user_id: int
    user_name: str
    email: str
    books_read: int
    total_reading_time_hours: float
    last_active: datetime


class DailyTrend(BaseModel):
    """Daily reading trend data point."""
    date: str  # YYYY-MM-DD
    sessions: int
    unique_readers: int
    total_time_hours: float


class OverviewStats(BaseModel):
    """Overall platform statistics."""
    total_users: int
    total_books: int
    total_reading_sessions: int
    total_reading_time_hours: float
    active_readers_today: int
    active_readers_week: int
    most_popular_book: Optional[BookStats] = None


class AnalyticsResponse(BaseModel):
    """Complete analytics response."""
    overview: OverviewStats
    book_stats: List[BookStats]
    recent_readers: List[ReaderActivity]
    daily_trends: List[DailyTrend]


class ReadingSessionCreate(BaseModel):
    """Schema for starting a reading session."""
    book_id: int


class ReadingSessionUpdate(BaseModel):
    """Schema for updating reading session progress."""
    last_page_read: int
    time_spent_seconds: int


class ReadingSessionResponse(BaseModel):
    """Schema for reading session response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    book_id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    last_page_read: int
    total_time_seconds: int
