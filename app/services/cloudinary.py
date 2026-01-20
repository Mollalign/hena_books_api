"""
Cloudinary Service

Handles file uploads (book PDFs and cover images) to Cloudinary.
"""

import cloudinary
import cloudinary.uploader
from typing import Optional, Tuple
from fastapi import UploadFile
import logging

from app.core.config import settings
from app.core.exceptions import FileTooLargeError, FileUploadError

logger = logging.getLogger(__name__)

# Cloudinary free tier limit is 10MB for raw files
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # 10MB


def configure_cloudinary():
    """Configure Cloudinary with credentials from settings."""
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )


async def upload_book_file(file: UploadFile) -> Tuple[str, str]:
    """
    Upload a book PDF to Cloudinary.
    
    Args:
        file: The uploaded PDF file
        
    Returns:
        Tuple of (secure_url, public_id)
        
    Raises:
        FileTooLargeError: If file exceeds 10MB
        FileUploadError: If upload fails
    """
    configure_cloudinary()
    
    try:
        # Read file content
        content = await file.read()
        
        # Check file size BEFORE uploading
        file_size = len(content)
        if file_size > MAX_FILE_SIZE_BYTES:
            file_size_mb = round(file_size / (1024 * 1024), 2)
            logger.warning(f"File too large: {file_size_mb}MB (max: {MAX_FILE_SIZE_MB}MB)")
            raise FileTooLargeError(max_size_mb=MAX_FILE_SIZE_MB)
        
        # Upload to Cloudinary as raw file (for PDFs)
        result = cloudinary.uploader.upload(
            content,
            resource_type="raw",
            folder="hena_books/pdfs",
            public_id=file.filename.rsplit('.', 1)[0] if file.filename else None,
            overwrite=True,
        )
        
        return result["secure_url"], result["public_id"]
    except FileTooLargeError:
        raise  # Re-raise our custom exception
    except Exception as e:
        logger.error(f"Failed to upload book file: {e}")
        raise FileUploadError(f"Failed to upload PDF: {str(e)}")


async def upload_cover_image(file: UploadFile) -> Tuple[str, str]:
    """
    Upload a book cover image to Cloudinary.
    
    Args:
        file: The uploaded image file
        
    Returns:
        Tuple of (secure_url, public_id)
    """
    configure_cloudinary()
    
    try:
        content = await file.read()
        
        # Upload as image with transformations
        result = cloudinary.uploader.upload(
            content,
            resource_type="image",
            folder="hena_books/covers",
            transformation=[
                {"width": 400, "height": 600, "crop": "fill"},
                {"quality": "auto"},
                {"fetch_format": "auto"}
            ],
            overwrite=True,
        )
        
        return result["secure_url"], result["public_id"]
    except Exception as e:
        logger.error(f"Failed to upload cover image: {e}")
        raise


async def delete_file(public_id: str, resource_type: str = "raw") -> bool:
    """
    Delete a file from Cloudinary.
    
    Args:
        public_id: The Cloudinary public ID
        resource_type: "raw" for PDFs, "image" for covers
        
    Returns:
        True if successful, False otherwise
    """
    configure_cloudinary()
    
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return result.get("result") == "ok"
    except Exception as e:
        logger.error(f"Failed to delete file {public_id}: {e}")
        return False


def get_download_url(public_id: str) -> Optional[str]:
    """
    Generate a download URL for a book file.
    Only admins should be able to use this.
    
    Args:
        public_id: The Cloudinary public ID
        
    Returns:
        Download URL or None
    """
    configure_cloudinary()
    
    try:
        # Generate URL with attachment flag for download
        url = cloudinary.utils.cloudinary_url(
            public_id,
            resource_type="raw",
            flags="attachment",
            secure=True
        )
        return url[0] if url else None
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        return None
