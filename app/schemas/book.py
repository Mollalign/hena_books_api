"""
Book Schemas

Pydantic models for book request/response validation.
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class BookBase(BaseModel):
    """Base book schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    page_count: Optional[int] = Field(None, ge=1)
    published_date: Optional[date] = None
    is_featured: bool = False
    is_published: bool = True


class BookCreate(BookBase):
    """Schema for creating a book (used with file upload)."""
    pass


class BookUpdate(BaseModel):
    """Schema for updating book details."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    page_count: Optional[int] = Field(None, ge=1)
    published_date: Optional[date] = None
    is_featured: Optional[bool] = None
    is_published: Optional[bool] = None


class BookResponse(BookBase):
    """Schema for book response (public info)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    cover_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BookDetailResponse(BookResponse):
    """Schema for detailed book response (includes reading stats)."""
    total_readers: Optional[int] = 0
    total_reading_time_hours: Optional[float] = 0.0


class BookAdminResponse(BookResponse):
    """Schema for admin book response (includes file URLs)."""
    file_url: str
    file_public_id: str
    cover_public_id: Optional[str] = None


class BookListResponse(BaseModel):
    """Schema for paginated book list."""
    books: List[BookResponse]
    total: int
    page: int
    per_page: int
