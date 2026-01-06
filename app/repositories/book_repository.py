"""
Book Repository

Data access layer for Book model.
All book-related database operations.
"""

from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import date

from app.repositories.base import BaseRepository
from app.models.book import Book


class BookRepository(BaseRepository[Book]):
    """Repository for Book model."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Book, db)
    
    async def get_by_id(self, book_id: int) -> Optional[Book]:
        """Get a book by ID."""
        result = await self.db.execute(
            select(Book).where(Book.id == book_id)
        )
        return result.scalar_one_or_none()
    
    async def get_published_by_id(self, book_id: int) -> Optional[Book]:
        """Get a published book by ID."""
        result = await self.db.execute(
            select(Book).where(
                and_(Book.id == book_id, Book.is_published == True)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_books(self, skip: int = 0, limit: int = 100) -> List[Book]:
        """Get all books ordered by creation date."""
        result = await self.db.execute(
            select(Book)
            .order_by(Book.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_published_books(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        featured_only: bool = False
    ) -> Tuple[List[Book], int]:
        """
        Get published books with pagination and filters.
        
        Returns:
            Tuple of (books list, total count)
        """
        # Build base query
        query = select(Book).where(Book.is_published == True)
        count_query = select(func.count(Book.id)).where(Book.is_published == True)
        
        # Apply filters
        if search:
            search_filter = Book.title.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if featured_only:
            query = query.where(Book.is_featured == True)
            count_query = count_query.where(Book.is_featured == True)
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get books with pagination
        query = query.order_by(Book.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        books = list(result.scalars().all())
        
        return books, total
    
    async def get_featured_books(self, limit: int = 5) -> List[Book]:
        """Get featured books for landing page."""
        result = await self.db.execute(
            select(Book)
            .where(and_(Book.is_published == True, Book.is_featured == True))
            .order_by(Book.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def create_book(
        self,
        title: str,
        file_url: str,
        file_public_id: str,
        description: Optional[str] = None,
        cover_url: Optional[str] = None,
        cover_public_id: Optional[str] = None,
        page_count: Optional[int] = None,
        published_date: Optional[date] = None,
        is_featured: bool = False,
        is_published: bool = True
    ) -> Book:
        """Create a new book."""
        book = Book(
            title=title,
            description=description,
            cover_url=cover_url,
            cover_public_id=cover_public_id,
            file_url=file_url,
            file_public_id=file_public_id,
            page_count=page_count,
            published_date=published_date,
            is_featured=is_featured,
            is_published=is_published
        )
        self.db.add(book)
        await self.db.commit()
        await self.db.refresh(book)
        return book
    
    async def update_book(self, book_id: int, **kwargs) -> Optional[Book]:
        """Update book fields."""
        return await self.update(book_id, **kwargs)
    
    async def delete_book(self, book_id: int) -> bool:
        """Delete a book by ID."""
        return await self.delete(book_id)

