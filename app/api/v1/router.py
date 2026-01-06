"""
API v1 Router

Combines all API routes into a single router.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.books import router as books_router
from app.api.v1.users import router as users_router
from app.api.v1.analytics import router as analytics_router

api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(books_router)
api_router.include_router(users_router)
api_router.include_router(analytics_router)
