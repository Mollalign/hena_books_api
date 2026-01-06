"""
Admin Seeder Script

Run this script to create the initial admin user.
Usage: python -m app.scripts.seed_admin
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import AsyncSessionLocal, init_db
from app.services.auth import AuthService


async def seed_admin():
    """Create the admin user."""
    print("Starting admin seeder...")
    
    # Initialize database tables
    await init_db()
    print("Database tables created.")
    
    # Admin credentials - CHANGE THESE!
    admin_email = os.getenv("ADMIN_EMAIL", "admin@henabooks.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123456")
    admin_name = os.getenv("ADMIN_NAME", "Henok (Admin)")
    
    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)
        admin = await auth_service.create_admin_user(
            email=admin_email,
            password=admin_password,
            name=admin_name
        )
        print(f"Admin user created/verified: {admin.email}")
    
    print("Admin seeder completed!")
    print("\n⚠️  IMPORTANT: Change the default password immediately!")
    print(f"   Email: {admin_email}")
    print(f"   Password: {admin_password}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
