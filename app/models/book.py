"""
Book Model

Represents Christian/Biblical books uploaded by the admin.
Stores metadata and Cloudinary URLs for cover and PDF file.
"""

from datetime import date
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, Date, Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import BaseModel


class BookCategory(str, Enum):
    """Categories for Christian/Biblical books."""
    
    BIBLICAL_STUDIES = "Biblical Studies"
    THEOLOGY = "Theology"
    DEVOTIONAL = "Devotional"
    CHRISTIAN_LIVING = "Christian Living"
    PRAYER_WORSHIP = "Prayer & Worship"
    CHURCH_HISTORY = "Church History"
    APOLOGETICS = "Apologetics"
    FAMILY_MARRIAGE = "Family & Marriage"
    YOUTH_CHILDREN = "Youth & Children"
    MISSIONS_EVANGELISM = "Missions & Evangelism"
    SPIRITUAL_GROWTH = "Spiritual Growth"
    BIOGRAPHY_TESTIMONY = "Biography & Testimony"
    COMMENTARY = "Commentary"
    REFERENCE = "Reference"
    OTHER = "Other"


class Book(BaseModel):
    """
    Book model for storing uploaded biblical/Christian book information.
    
    Attributes:
        id: Primary key (UUID)
        title: Book title
        author: Book author name
        description: Full description/synopsis
        category: Book category (Biblical Studies, Theology, etc.)
        scripture_focus: Primary scripture reference (e.g., "Romans 8", "John 3:16")
        cover_url: Cloudinary URL for cover image
        cover_public_id: Cloudinary public ID for cover (for deletion)
        file_url: Cloudinary secure URL for PDF
        file_public_id: Cloudinary public ID for PDF (for deletion)
        page_count: Total pages (optional)
        published_date: When the book was originally published
        is_featured: Whether to show on landing page
        is_published: Whether visible to public
        created_at: Upload timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "books"

    # Basic Info
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Christian-specific fields
    category = Column(
        SQLEnum(BookCategory),
        default=BookCategory.OTHER,
        nullable=False,
        index=True
    )
    scripture_focus = Column(String(255), nullable=True)  # e.g., "Romans 8:28-39"
    
    # Media files
    cover_url = Column(String(500), nullable=True)
    cover_public_id = Column(String(255), nullable=True)
    file_url = Column(String(500), nullable=False)
    file_public_id = Column(String(255), nullable=False)
    
    # Metadata
    page_count = Column(Integer, nullable=True)
    published_date = Column(Date, nullable=True)
    
    # Visibility flags
    is_featured = Column(Boolean, default=False, nullable=False, index=True)
    is_published = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    reading_sessions = relationship(
        "ReadingSession",
        back_populates="book",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, title='{self.title}', category='{self.category.value}')>"
    
    @property
    def display_author(self) -> str:
        """Returns author name or 'Unknown Author' if not set."""
        return self.author or "Unknown Author"
