"""
Book Service

Business logic layer for book operations.
Handles book management and file operations.
"""

from typing import Optional, Tuple, List
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException, status

from app.repositories.book_repository import BookRepository
from app.models.book import Book
from app.services.cloudinary import (
    upload_book_file,
    upload_cover_image,
    delete_file,
    get_download_url,
)


class BookService:
    """Service for book business logic."""
    
    def __init__(self, db: AsyncSession):
        self.book_repo = BookRepository(db)
    
    async def get_book_by_id(self, book_id: UUID) -> Optional[Book]:
        """Get a book by ID."""
        return await self.book_repo.get_by_id(book_id)
    
    async def get_published_book_by_id(self, book_id: UUID) -> Optional[Book]:
        """Get a published book by ID."""
        return await self.book_repo.get_published_by_id(book_id)
    
    async def get_all_books(self, skip: int = 0, limit: int = 100) -> List[Book]:
        """Get all books (including unpublished)."""
        return await self.book_repo.get_all_books(skip=skip, limit=limit)
    
    async def get_published_books(
        self,
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None,
        featured_only: bool = False
    ) -> Tuple[List[Book], int]:
        """Get published books with pagination and filters."""
        skip = (page - 1) * per_page
        return await self.book_repo.get_published_books(
            skip=skip,
            limit=per_page,
            search=search,
            featured_only=featured_only
        )
    
    async def get_featured_books(self, limit: int = 5) -> List[Book]:
        """Get featured books."""
        return await self.book_repo.get_featured_books(limit=limit)
    
    async def create_book(
        self,
        title: str,
        book_file: UploadFile,
        description: Optional[str] = None,
        page_count: Optional[int] = None,
        published_date: Optional[date] = None,
        is_featured: bool = False,
        is_published: bool = True,
        cover_file: Optional[UploadFile] = None
    ) -> Book:
        """Create a new book with file uploads."""
        # Validate file type
        if not book_file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Book file must be a PDF"
            )
        
        try:
            # Upload book file
            file_url, file_public_id = await upload_book_file(book_file)
            
            # Upload cover if provided
            cover_url = None
            cover_public_id = None
            if cover_file:
                cover_url, cover_public_id = await upload_cover_image(cover_file)
            
            # Create book record
            return await self.book_repo.create_book(
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
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload book: {str(e)}"
            )
    
    async def update_book(
        self,
        book_id: UUID,
        **update_data
    ) -> Optional[Book]:
        """Update book details."""
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        return await self.book_repo.update_book(book_id, **update_data)
    
    async def delete_book(self, book_id: UUID) -> bool:
        """Delete a book and its files."""
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            return False
        
        # Delete files from Cloudinary
        await delete_file(book.file_public_id, "raw")
        if book.cover_public_id:
            await delete_file(book.cover_public_id, "image")
        
        # Delete from database
        return await self.book_repo.delete_book(book_id)
    
    async def get_download_url_for_book(self, book_id: UUID) -> Optional[str]:
        """Get download URL for a book."""
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            return None
        
        return get_download_url(book.file_public_id)

