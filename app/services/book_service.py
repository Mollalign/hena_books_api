"""
Book Service

Business logic layer for book operations.
Handles book management, file uploads, and business rules.
"""

from typing import Optional, Tuple, List
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.repositories.book_repository import BookRepository
from app.models.book import Book, BookCategory
from app.core.exceptions import (
    BookNotFoundError,
    InvalidFileTypeError,
    FileUploadError,
)
from app.services.cloudinary import (
    upload_book_file,
    upload_cover_image,
    delete_file,
    get_download_url,
)


class BookService:
    """
    Service for book business logic.
    
    Handles:
    - Book CRUD operations
    - File upload/delete via Cloudinary
    - Business validation rules
    """
    
    ALLOWED_BOOK_EXTENSIONS = {'.pdf'}
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    
    def __init__(self, db: AsyncSession):
        self.repo = BookRepository(db)
    
    # =========================================================================
    # READ OPERATIONS
    # =========================================================================
    
    async def get_book_by_id(self, book_id: UUID) -> Optional[Book]:
        """Get a book by ID (includes unpublished)."""
        return await self.repo.get_by_id(book_id)
    
    async def get_published_book_by_id(self, book_id: UUID) -> Book:
        """
        Get a published book by ID.
        
        Raises:
            BookNotFoundError: If book not found or not published
        """
        book = await self.repo.get_published_by_id(book_id)
        if not book:
            raise BookNotFoundError()
        return book
    
    async def get_all_books(self) -> List[Book]:
        """Get all books including unpublished (admin only)."""
        return await self.repo.get_all_books()
    
    async def get_published_books(
        self,
        page: int = 1,
        per_page: int = 12,
        search: Optional[str] = None,
        category: Optional[BookCategory] = None,
        featured_only: bool = False
    ) -> Tuple[List[Book], int]:
        """
        Get published books with pagination and filters.
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            search: Search term for title/author
            category: Filter by category
            featured_only: Only featured books
            
        Returns:
            Tuple of (books list, total count)
        """
        skip = (page - 1) * per_page
        return await self.repo.get_published_books(
            skip=skip,
            limit=per_page,
            search=search,
            category=category,
            featured_only=featured_only
        )
    
    async def get_featured_books(self, limit: int = 6) -> List[Book]:
        """Get featured books for landing page."""
        return await self.repo.get_featured_books(limit=limit)
    
    async def get_books_by_category(
        self,
        category: BookCategory,
        limit: int = 10
    ) -> List[Book]:
        """Get published books by category."""
        return await self.repo.get_books_by_category(category, limit)
    
    async def get_category_counts(self) -> dict:
        """Get count of books per category."""
        return await self.repo.count_by_category()
    
    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================
    
    async def create_book(
        self,
        title: str,
        book_file: UploadFile,
        author: Optional[str] = None,
        description: Optional[str] = None,
        category: BookCategory = BookCategory.OTHER,
        scripture_focus: Optional[str] = None,
        page_count: Optional[int] = None,
        published_date: Optional[date] = None,
        is_featured: bool = False,
        is_published: bool = True,
        cover_file: Optional[UploadFile] = None
    ) -> Book:
        """
        Create a new book with file uploads.
        
        Args:
            title: Book title
            book_file: PDF file (required)
            author: Book author
            description: Book description
            category: Book category
            scripture_focus: Primary scripture reference
            page_count: Total pages
            published_date: Original publication date
            is_featured: Show on homepage
            is_published: Visible to public
            cover_file: Cover image (optional)
            
        Raises:
            InvalidFileTypeError: If file type is not allowed
            FileUploadError: If file upload fails
        """
        # Validate book file type
        self._validate_file_type(book_file.filename, self.ALLOWED_BOOK_EXTENSIONS)
        
        # Validate cover file type if provided
        if cover_file and cover_file.filename:
            self._validate_file_type(cover_file.filename, self.ALLOWED_IMAGE_EXTENSIONS)
        
        try:
            # Upload book PDF
            file_url, file_public_id = await upload_book_file(book_file)
            
            # Upload cover image if provided
            cover_url = None
            cover_public_id = None
            if cover_file:
                cover_url, cover_public_id = await upload_cover_image(cover_file)
            
            # Create book record
            return await self.repo.create_book(
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
        except InvalidFileTypeError:
            raise
        except Exception as e:
            raise FileUploadError(f"Failed to upload book: {str(e)}")
    
    async def update_book(self, book_id: UUID, **update_data) -> Book:
        """
        Update book details.
        
        Raises:
            BookNotFoundError: If book not found
        """
        book = await self.repo.update_book(book_id, **update_data)
        if not book:
            raise BookNotFoundError()
        return book
    
    async def delete_book(self, book_id: UUID) -> bool:
        """
        Delete a book and its files from Cloudinary.
        
        Raises:
            BookNotFoundError: If book not found
        """
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundError()
        
        # Delete files from Cloudinary (don't fail if this fails)
        try:
            await delete_file(book.file_public_id, "raw")
            if book.cover_public_id:
                await delete_file(book.cover_public_id, "image")
        except Exception:
            pass  # Log but don't fail deletion
        
        return await self.repo.delete_book(book_id)
    
    async def toggle_featured(self, book_id: UUID) -> Book:
        """
        Toggle the featured status of a book.
        
        Raises:
            BookNotFoundError: If book not found
        """
        book = await self.repo.toggle_featured(book_id)
        if not book:
            raise BookNotFoundError()
        return book
    
    async def toggle_published(self, book_id: UUID) -> Book:
        """
        Toggle the published status of a book.
        
        Raises:
            BookNotFoundError: If book not found
        """
        book = await self.repo.toggle_published(book_id)
        if not book:
            raise BookNotFoundError()
        return book
    
    # =========================================================================
    # FILE OPERATIONS
    # =========================================================================
    
    async def get_download_url(self, book_id: UUID) -> str:
        """
        Get download URL for a book (admin only).
        
        Raises:
            BookNotFoundError: If book not found
        """
        book = await self.repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundError()
        
        url = get_download_url(book.file_public_id)
        if not url:
            raise FileUploadError("Failed to generate download URL")
        return url
    
    # =========================================================================
    # VALIDATION HELPERS
    # =========================================================================
    
    def _validate_file_type(self, filename: Optional[str], allowed: set) -> None:
        """
        Validate file type by extension.
        
        Raises:
            InvalidFileTypeError: If file type is not allowed
        """
        if not filename:
            raise InvalidFileTypeError(", ".join(allowed))
        
        ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in allowed:
            raise InvalidFileTypeError(", ".join(allowed))
