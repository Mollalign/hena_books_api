"""
Books API Routes

Public and admin endpoints for book management.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.core.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.models.user import User
from app.schemas.book import (
    BookCreate,
    BookUpdate,
    BookResponse,
    BookDetailResponse,
    BookAdminResponse,
    BookListResponse,
)
from app.services.book_service import BookService
from app.services.reading_session_service import ReadingSessionService
from app.repositories.reading_session_repository import ReadingSessionRepository

router = APIRouter(prefix="/books", tags=["Books"])


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@router.get("", response_model=BookListResponse)
async def list_books(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    search: Optional[str] = None,
    featured_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    List all published books with pagination.
    
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 10, max: 50)
    - **search**: Search by title
    - **featured_only**: Only return featured books
    """
    book_service = BookService(db)
    books, total = await book_service.get_published_books(
        page=page,
        per_page=per_page,
        search=search,
        featured_only=featured_only
    )
    
    return BookListResponse(
        books=books,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/featured", response_model=list[BookResponse])
async def get_featured_books(
    limit: int = Query(5, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """
    Get featured books for the landing page.
    """
    book_service = BookService(db)
    return await book_service.get_featured_books(limit=limit)


@router.get("/{book_id}", response_model=BookDetailResponse)
async def get_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single book by ID with reading statistics.
    """
    book_service = BookService(db)
    session_repo = ReadingSessionRepository(db)
    
    # Get book
    book = await book_service.get_published_book_by_id(book_id)
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Get reading stats
    stats = await session_repo.get_book_statistics(book_id)
    
    response = BookDetailResponse.model_validate(book)
    response.total_readers = stats["total_readers"]
    response.total_reading_time_hours = round(stats["total_time"] / 3600, 2)
    
    return response


@router.get("/{book_id}/read")
async def get_book_for_reading(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the book file URL for in-browser reading.
    Requires authentication. Does NOT provide download capability.
    """
    book_service = BookService(db)
    book = await book_service.get_published_book_by_id(book_id)
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    return {
        "book_id": book.id,
        "title": book.title,
        "file_url": book.file_url,
        "page_count": book.page_count
    }


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.post("/admin/upload", response_model=BookAdminResponse, status_code=status.HTTP_201_CREATED)
async def upload_book(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    page_count: Optional[int] = Form(None),
    published_date: Optional[date] = Form(None),
    is_featured: bool = Form(False),
    is_published: bool = Form(True),
    book_file: UploadFile = File(...),
    cover_file: Optional[UploadFile] = File(None),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a new book (Admin only).
    
    - **book_file**: PDF file (required)
    - **cover_file**: Cover image (optional, will be resized to 400x600)
    """
    book_service = BookService(db)
    return await book_service.create_book(
        title=title,
        description=description,
        page_count=page_count,
        published_date=published_date,
        is_featured=is_featured,
        is_published=is_published,
        book_file=book_file,
        cover_file=cover_file
    )


@router.put("/admin/{book_id}", response_model=BookAdminResponse)
async def update_book(
    book_id: UUID,
    book_data: BookUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update book details (Admin only).
    """
    book_service = BookService(db)
    update_data = book_data.model_dump(exclude_unset=True)
    book = await book_service.update_book(book_id, **update_data)
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    return book


@router.delete("/admin/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a book (Admin only).
    This also deletes the files from Cloudinary.
    """
    book_service = BookService(db)
    deleted = await book_service.delete_book(book_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )


@router.get("/admin/{book_id}/download")
async def download_book(
    book_id: UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get download URL for a book (Admin only).
    """
    book_service = BookService(db)
    book = await book_service.get_book_by_id(book_id)
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    download_url = await book_service.get_download_url_for_book(book_id)
    
    if not download_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )
    
    return {
        "title": book.title,
        "download_url": download_url
    }


@router.get("/admin/all", response_model=list[BookAdminResponse])
async def list_all_books_admin(
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all books including unpublished (Admin only).
    """
    book_service = BookService(db)
    return await book_service.get_all_books()
