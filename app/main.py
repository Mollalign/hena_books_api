"""
Hena Books API - Main Application Entry Point

A FastAPI application for managing Christian/Biblical books.
Provides REST API for book management, user authentication, and reading analytics.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import check_db_connection
from app.core.exceptions import HenaException
from app.api.v1.router import api_router
from app.middleware.logging import LoggingMiddleware


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# =============================================================================
# LIFESPAN MANAGER
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Startup:
    - Verify database connection
    - Log application info
    
    Shutdown:
    - Clean up resources
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info("=" * 60)
    
    # Check database connection
    try:
        is_healthy = await check_db_connection()
        if is_healthy:
            logger.info("✓ Database connection established")
        else:
            logger.warning("✗ Database connection check failed")
    except Exception as e:
        logger.error(f"✗ Database connection error: {e}")
    
    # Log configuration status
    if settings.cloudinary_configured:
        logger.info("✓ Cloudinary configured")
    else:
        logger.warning("✗ Cloudinary not configured - file uploads disabled")
    
    if settings.smtp_configured:
        logger.info("✓ SMTP configured")
    else:
        logger.warning("✗ SMTP not configured - email features disabled")
    
    logger.info("-" * 60)
    
    yield
    
    # Shutdown
    logger.info("-" * 60)
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    logger.info("=" * 60)


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="""
## Hena Books API

A platform for sharing and reading Christian/Biblical books.

### Features

* **Authentication** - JWT-based auth with access and refresh tokens
* **Books** - Upload, manage, and read PDF books
* **Categories** - Organize books by Biblical topics
* **Analytics** - Track reading sessions and statistics
* **Admin** - Full management dashboard

### Categories

Books are organized into the following categories:
- Biblical Studies
- Theology
- Devotional
- Christian Living
- Prayer & Worship
- Church History
- Apologetics
- And more...

### Authentication

Use the `/auth/login` endpoint to get a JWT token, then include it in the
`Authorization` header as `Bearer <token>` for protected endpoints.
        """,
        version=settings.VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        contact={
            "name": "Hena Books",
            "email": "contact@henabooks.com",
        },
        license_info={
            "name": "MIT",
        }
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    
    # Add logging middleware in debug mode
    if settings.DEBUG:
        app.add_middleware(LoggingMiddleware)
    
    # Register routes
    app.include_router(api_router)
    
    return app


# Create the application instance
app = create_application()


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(HenaException)
async def hena_exception_handler(request: Request, exc: HenaException):
    """Handle all custom Hena exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )


# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.PROJECT_DESCRIPTION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    try:
        db_healthy = await check_db_connection()
        return {
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected" if db_healthy else "disconnected",
            "version": settings.VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "error",
                "error": str(e) if settings.DEBUG else "Database connection failed"
            }
        )


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness probe for Kubernetes/container orchestration.
    """
    db_ready = await check_db_connection()
    
    if not db_ready:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "reason": "Database not ready"}
        )
    
    return {"ready": True}
