"""
Books API Routes

Public and admin endpoints for book management.
Provides CRUD operations and file handling for Christian/Biblical books.
"""

from typing import Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import BookNotFoundError, ExternalServiceError
from app.api.deps import get_current_user, get_admin_user
from app.models.user import User
from app.models.book import BookCategory
from app.schemas.book import (
    BookResponse,
    BookDetailResponse,
    BookAdminResponse,
    BookListResponse,
    BookUpdate,
)
from app.services.book_service import BookService
from app.repositories.reading_session_repository import ReadingSessionRepository


router = APIRouter(prefix="/books", tags=["Books"])


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@router.get("", response_model=BookListResponse)
async def list_books(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(12, ge=1, le=50, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by title or author"),
    category: Optional[BookCategory] = Query(None, description="Filter by category"),
    featured_only: bool = Query(False, description="Only featured books"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all published books with pagination and filters.
    
    - **page**: Page number (default: 1)
    - **per_page**: Items per page (default: 12, max: 50)
    - **search**: Search by title or author
    - **category**: Filter by category (Biblical Studies, Theology, etc.)
    - **featured_only**: Only return featured books
    """
    book_service = BookService(db)
    books, total = await book_service.get_published_books(
        page=page,
        per_page=per_page,
        search=search,
        category=category,
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
    limit: int = Query(6, ge=1, le=12, description="Number of featured books"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get featured books for the landing page.
    """
    book_service = BookService(db)
    return await book_service.get_featured_books(limit=limit)


@router.get("/categories")
async def get_categories():
    """
    Get all available book categories.
    """
    return {
        "categories": [
            {"value": cat.name, "label": cat.value}
            for cat in BookCategory
        ]
    }


@router.get("/categories/{category}", response_model=list[BookResponse])
async def get_books_by_category(
    category: BookCategory,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get published books by category.
    """
    book_service = BookService(db)
    return await book_service.get_books_by_category(category, limit)


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
    
    # Get published book (raises BookNotFoundError if not found)
    book = await book_service.get_published_book_by_id(book_id)
    
    # Get reading stats
    stats = await session_repo.get_book_statistics(book_id)
    
    # Build response
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
    
    return {
        "book_id": str(book.id),
        "title": book.title,
        "author": book.author,
        "file_url": book.file_url,
        "page_count": book.page_count
    }


@router.get("/{book_id}/read/file")
async def get_book_file(
    book_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Proxy endpoint to stream PDF file from Cloudinary.
    
    This avoids CORS issues when loading PDFs in the browser.
    """
    from fastapi.responses import StreamingResponse
    from urllib.parse import quote
    import aiohttp
    
    book_service = BookService(db)
    book = await book_service.get_published_book_by_id(book_id)
    
    async def stream_pdf():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(book.file_url) as response:
                    response.raise_for_status()
                    async for chunk in response.content.iter_chunked(8192):
                        yield chunk
        except Exception as e:
            raise ExternalServiceError("Cloudinary", f"Failed to fetch PDF: {str(e)}")
    
    # Properly encode filename for Content-Disposition header
    # Use RFC 5987 encoding for non-ASCII characters
    safe_filename = f"{book.title}.pdf"
    # ASCII fallback for older clients
    ascii_filename = "book.pdf"
    # UTF-8 encoded filename using RFC 5987 format
    encoded_filename = quote(safe_filename, safe='')
    
    return StreamingResponse(
        stream_pdf(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{ascii_filename}\"; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600",
        }
    )


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

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


@router.post("/admin/upload", response_model=BookAdminResponse, status_code=201)
async def upload_book(
    title: str = Form(..., description="Book title"),
    author: Optional[str] = Form(None, description="Book author"),
    description: Optional[str] = Form(None, description="Book description"),
    category: str = Form("OTHER", description="Book category (enum name)"),
    scripture_focus: Optional[str] = Form(None, description="Primary scripture reference"),
    page_count: Optional[int] = Form(None, description="Total pages"),
    published_date: Optional[date] = Form(None, description="Publication date"),
    is_featured: bool = Form(False, description="Feature on homepage"),
    is_published: bool = Form(True, description="Visible to public"),
    book_file: UploadFile = File(..., description="PDF file"),
    cover_file: Optional[UploadFile] = File(None, description="Cover image"),
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a new book (Admin only).
    
    - **book_file**: PDF file (required)
    - **cover_file**: Cover image (optional, will be resized to 400x600)
    - **category**: One of the Christian book categories (use enum name like BIBLICAL_STUDIES)
    - **scripture_focus**: Primary scripture reference (e.g., "Romans 8:28-39")
    """
    # Convert category string to enum (accepts both name and value)
    try:
        book_category = BookCategory[category]  # Try by name first (e.g., "BIBLICAL_STUDIES")
    except KeyError:
        try:
            book_category = BookCategory(category)  # Try by value (e.g., "Biblical Studies")
        except ValueError:
            book_category = BookCategory.OTHER  # Default to OTHER if invalid
    
    # Handle empty cover file (treat as None if no filename or empty)
    actual_cover_file = cover_file if cover_file and cover_file.filename else None
    
    book_service = BookService(db)
    return await book_service.create_book(
        title=title,
        author=author,
        description=description,
        category=book_category,
        scripture_focus=scripture_focus,
        page_count=page_count,
        published_date=published_date,
        is_featured=is_featured,
        is_published=is_published,
        book_file=book_file,
        cover_file=actual_cover_file
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
    return await book_service.update_book(book_id, **update_data)
    

@router.patch("/admin/{book_id}/toggle-featured", response_model=BookAdminResponse)
async def toggle_book_featured(
    book_id: UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle book's featured status (Admin only).
    """
    book_service = BookService(db)
    return await book_service.toggle_featured(book_id)


@router.patch("/admin/{book_id}/toggle-published", response_model=BookAdminResponse)
async def toggle_book_published(
    book_id: UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Toggle book's published status (Admin only).
    """
    book_service = BookService(db)
    return await book_service.toggle_published(book_id)


@router.delete("/admin/{book_id}", status_code=204)
async def delete_book(
    book_id: UUID,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a book and its files (Admin only).
    """
    book_service = BookService(db)
    await book_service.delete_book(book_id)


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
        raise BookNotFoundError()
    
    download_url = await book_service.get_download_url(book_id)
    
    return {
        "title": book.title,
        "download_url": download_url
    }
