"""
Books API Routes

Public and admin endpoints for book management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date

from app.core.database import get_db
from app.api.deps import get_current_user, get_admin_user
from app.models.user import User
from app.models.book import Book
from app.models.reading_session import ReadingSession
from app.schemas.book import (
    BookCreate,
    BookUpdate,
    BookResponse,
    BookDetailResponse,
    BookAdminResponse,
    BookListResponse,
)
from app.services.cloudinary import (
    upload_book_file,
    upload_cover_image,
    delete_file,
    get_download_url,
)

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
    # Build query
    query = select(Book).where(Book.is_published == True)
    count_query = select(func.count(Book.id)).where(Book.is_published == True)
    
    if search:
        query = query.where(Book.title.ilike(f"%{search}%"))
        count_query = count_query.where(Book.title.ilike(f"%{search}%"))
    
    if featured_only:
        query = query.where(Book.is_featured == True)
        count_query = count_query.where(Book.is_featured == True)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get books with pagination
    offset = (page - 1) * per_page
    query = query.order_by(Book.created_at.desc()).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    books = result.scalars().all()
    
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
    query = (
        select(Book)
        .where(Book.is_published == True)
        .where(Book.is_featured == True)
        .order_by(Book.created_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{book_id}", response_model=BookDetailResponse)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single book by ID with reading statistics.
    """
    # Get book
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    if not book.is_published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Get reading stats
    stats_query = select(
        func.count(func.distinct(ReadingSession.user_id)).label("total_readers"),
        func.sum(ReadingSession.total_time_seconds).label("total_time")
    ).where(ReadingSession.book_id == book_id)
    
    stats_result = await db.execute(stats_query)
    stats = stats_result.first()
    
    response = BookDetailResponse.model_validate(book)
    response.total_readers = stats.total_readers or 0
    response.total_reading_time_hours = round((stats.total_time or 0) / 3600, 2)
    
    return response


@router.get("/{book_id}/read")
async def get_book_for_reading(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the book file URL for in-browser reading.
    Requires authentication. Does NOT provide download capability.
    """
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book or not book.is_published:
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
        
        db.add(book)
        await db.commit()
        await db.refresh(book)
        
        return book
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload book: {str(e)}"
        )


@router.put("/admin/{book_id}", response_model=BookAdminResponse)
async def update_book(
    book_id: int,
    book_data: BookUpdate,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update book details (Admin only).
    """
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Update fields
    update_data = book_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)
    
    await db.commit()
    await db.refresh(book)
    
    return book


@router.delete("/admin/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a book (Admin only).
    This also deletes the files from Cloudinary.
    """
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Delete files from Cloudinary
    await delete_file(book.file_public_id, "raw")
    if book.cover_public_id:
        await delete_file(book.cover_public_id, "image")
    
    # Delete from database
    await db.delete(book)
    await db.commit()


@router.get("/admin/{book_id}/download")
async def download_book(
    book_id: int,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get download URL for a book (Admin only).
    """
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    download_url = get_download_url(book.file_public_id)
    
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
    result = await db.execute(
        select(Book).order_by(Book.created_at.desc())
    )
    return result.scalars().all()
