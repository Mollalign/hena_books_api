"""
Reading Session Model

Tracks user reading activity for analytics.
Records when users start reading, how long they read, and which page they reached.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReadingSession(Base):
    """
    Reading session model for tracking user engagement.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        book_id: Foreign key to books table
        started_at: When reading session began
        ended_at: When reading session ended (null if still reading)
        last_page_read: Last page the user viewed
        total_time_seconds: Total time spent reading
    """
    __tablename__ = "reading_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    last_page_read = Column(Integer, default=1, nullable=False)
    total_time_seconds = Column(Integer, default=0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="reading_sessions")
    book = relationship("Book", back_populates="reading_sessions")

    def __repr__(self):
        return f"<ReadingSession(id={self.id}, user_id={self.user_id}, book_id={self.book_id})>"
