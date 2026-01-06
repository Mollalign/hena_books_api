"""
Book Model

Represents books uploaded by the admin (you).
Stores metadata and Cloudinary URLs for cover and PDF file.
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date
from sqlalchemy.orm import relationship

from .base import BaseModel


class Book(BaseModel):
    """
    Book model for storing uploaded book information.
    
    Attributes:
        id: Primary key
        title: Book title
        description: Full description/synopsis
        cover_url: Cloudinary URL for cover image
        file_url: Cloudinary secure URL for PDF
        file_public_id: Cloudinary public ID (for deletion)
        page_count: Total pages (optional)
        published_date: When the book was published (optional)
        is_featured: Whether to show on landing page
        is_published: Whether visible to public
        created_at: Upload timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "books"

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    cover_public_id = Column(String(255), nullable=True)
    file_url = Column(String(500), nullable=False)
    file_public_id = Column(String(255), nullable=False)
    page_count = Column(Integer, nullable=True)
    published_date = Column(Date, nullable=True)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False)

    # Relationships
    reading_sessions = relationship("ReadingSession", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}')>"
