"""
Book Repository

Data access layer for Book model.
Handles all book-related database operations.
"""

from typing import Optional, List, Tuple
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.repositories.base import BaseRepository
from app.models.book import Book, BookCategory


class BookRepository(BaseRepository[Book]):
    """Repository for Book model database operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Book, db)
    
    # =========================================================================
    # READ OPERATIONS
    # =========================================================================
    
    async def get_by_id(self, book_id: UUID) -> Optional[Book]:
        """Get a book by ID."""
        result = await self.db.execute(
            select(Book).where(Book.id == book_id)
        )
        return result.scalar_one_or_none()
    
    async def get_published_by_id(self, book_id: UUID) -> Optional[Book]:
        """Get a published book by ID."""
        result = await self.db.execute(
            select(Book).where(
                and_(Book.id == book_id, Book.is_published == True)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_all_books(self, skip: int = 0, limit: int = 100) -> List[Book]:
        """Get all books including unpublished (admin only)."""
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
        limit: int = 12,
        search: Optional[str] = None,
        category: Optional[BookCategory] = None,
        featured_only: bool = False
    ) -> Tuple[List[Book], int]:
        """
        Get published books with pagination and filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Search term for title or author
            category: Filter by category
            featured_only: Only return featured books
        
        Returns:
            Tuple of (books list, total count)
        """
        # Build base query for published books
        base_condition = Book.is_published == True
        
        # Build filter conditions
        conditions = [base_condition]
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    Book.title.ilike(search_term),
                    Book.author.ilike(search_term),
                    Book.description.ilike(search_term)
                )
            )
        
        if category:
            conditions.append(Book.category == category)
        
        if featured_only:
            conditions.append(Book.is_featured == True)
        
        # Combined condition
        combined_condition = and_(*conditions)
        
        # Count query
        count_result = await self.db.execute(
            select(func.count(Book.id)).where(combined_condition)
        )
        total = count_result.scalar() or 0
        
        # Data query with pagination
        result = await self.db.execute(
            select(Book)
            .where(combined_condition)
            .order_by(Book.is_featured.desc(), Book.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        books = list(result.scalars().all())
        
        return books, total
    
    async def get_featured_books(self, limit: int = 6) -> List[Book]:
        """Get featured books for landing page."""
        result = await self.db.execute(
            select(Book)
            .where(and_(Book.is_published == True, Book.is_featured == True))
            .order_by(Book.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_books_by_category(
        self,
        category: BookCategory,
        limit: int = 10
    ) -> List[Book]:
        """Get published books by category."""
        result = await self.db.execute(
            select(Book)
            .where(and_(Book.is_published == True, Book.category == category))
            .order_by(Book.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def count_by_category(self) -> dict:
        """Get count of published books per category."""
        result = await self.db.execute(
            select(Book.category, func.count(Book.id))
            .where(Book.is_published == True)
            .group_by(Book.category)
        )
        return {row[0]: row[1] for row in result.all()}
    
    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================
    
    async def create_book(
        self,
        title: str,
        file_url: str,
        file_public_id: str,
        author: Optional[str] = None,
        description: Optional[str] = None,
        category: BookCategory = BookCategory.OTHER,
        scripture_focus: Optional[str] = None,
        cover_url: Optional[str] = None,
        cover_public_id: Optional[str] = None,
        page_count: Optional[int] = None,
        published_date: Optional[date] = None,
        is_featured: bool = False,
        is_published: bool = True
    ) -> Book:
        """Create a new book record."""
        book = Book(
            title=title,
            author=author,
            description=description,
            category=category,
            scripture_focus=scripture_focus,
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
    
    async def update_book(self, book_id: UUID, **kwargs) -> Optional[Book]:
        """Update book fields."""
        # Filter out None values to avoid overwriting with None
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        if not update_data:
            return await self.get_by_id(book_id)
        return await self.update(book_id, **update_data)
    
    async def delete_book(self, book_id: UUID) -> bool:
        """Delete a book by ID."""
        return await self.delete(book_id)

    async def toggle_featured(self, book_id: UUID) -> Optional[Book]:
        """Toggle the featured status of a book."""
        book = await self.get_by_id(book_id)
        if not book:
            return None
        return await self.update(book_id, is_featured=not book.is_featured)
    
    async def toggle_published(self, book_id: UUID) -> Optional[Book]:
        """Toggle the published status of a book."""
        book = await self.get_by_id(book_id)
        if not book:
            return None
        return await self.update(book_id, is_published=not book.is_published)
