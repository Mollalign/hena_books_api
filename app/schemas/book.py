"""
Book Schemas

Pydantic models for book request/response validation.
Updated for Christian/Biblical book platform.
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.models.book import BookCategory


class BookBase(BaseModel):
    """Base book schema with common fields."""
    
    title: str = Field(..., min_length=1, max_length=255, description="Book title")
    author: Optional[str] = Field(None, max_length=255, description="Book author")
    description: Optional[str] = Field(None, description="Book description/synopsis")
    category: BookCategory = Field(
        default=BookCategory.OTHER,
        description="Book category"
    )
    scripture_focus: Optional[str] = Field(
        None,
        max_length=255,
        description="Primary scripture reference (e.g., 'Romans 8:28-39')"
    )
    page_count: Optional[int] = Field(None, ge=1, description="Total page count")
    published_date: Optional[date] = Field(None, description="Original publication date")
    is_featured: bool = Field(False, description="Show on homepage featured section")
    is_published: bool = Field(True, description="Visible to public")


class BookCreate(BookBase):
    """Schema for creating a book (used with file upload)."""
    pass


class BookUpdate(BaseModel):
    """Schema for updating book details (all fields optional)."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[BookCategory] = None
    scripture_focus: Optional[str] = Field(None, max_length=255)
    page_count: Optional[int] = Field(None, ge=1)
    published_date: Optional[date] = None
    is_featured: Optional[bool] = None
    is_published: Optional[bool] = None


class BookResponse(BaseModel):
    """Schema for book response (public info)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    author: Optional[str] = None
    description: Optional[str] = None
    category: BookCategory
    scripture_focus: Optional[str] = None
    cover_url: Optional[str] = None
    page_count: Optional[int] = None
    published_date: Optional[date] = None
    is_featured: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime
    
    @property
    def display_author(self) -> str:
        """Returns author name or 'Unknown Author' if not set."""
        return self.author or "Unknown Author"


class BookDetailResponse(BookResponse):
    """Schema for detailed book response (includes reading stats)."""
    
    total_readers: int = 0
    total_reading_time_hours: float = 0.0


class BookAdminResponse(BookResponse):
    """Schema for admin book response (includes file URLs and IDs)."""
    
    file_url: str
    file_public_id: str
    cover_public_id: Optional[str] = None


class BookListResponse(BaseModel):
    """Schema for paginated book list."""
    
    books: List[BookResponse]
    total: int
    page: int
    per_page: int

    @property
    def total_pages(self) -> int:
        """Calculate total pages."""
        if self.per_page <= 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1


class BookFilterParams(BaseModel):
    """Schema for book filtering parameters."""
    
    search: Optional[str] = Field(None, description="Search by title or author")
    category: Optional[BookCategory] = Field(None, description="Filter by category")
    featured_only: bool = Field(False, description="Only featured books")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(12, ge=1, le=50, description="Items per page")