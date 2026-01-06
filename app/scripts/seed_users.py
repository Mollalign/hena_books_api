"""
User Seeder Script

Seed the database with dummy users from JSON file.
Usage: python -m app.scripts.seed_users
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import AsyncSessionLocal
from app.services.auth import AuthService


async def seed_users(json_file_path: str = None):
    """Seed users from JSON file."""
    print("Starting user seeder...")
    
    # Default to dummy_users.json in project root
    if json_file_path is None:
        project_root = Path(__file__).parent.parent.parent
        json_file_path = project_root / "dummy_users.json"
    
    # Check if file exists
    if not os.path.exists(json_file_path):
        print(f"Error: JSON file not found at {json_file_path}")
        print("Please create a JSON file with user data or specify the path.")
        return
    
    # Load JSON data
    try:
        with open(json_file_path, 'r') as f:
            users_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    if not isinstance(users_data, list):
        print("Error: JSON file must contain an array of user objects")
        return
    
    print(f"Found {len(users_data)} users to create...")
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)
        
        for user_data in users_data:
            try:
                # Validate required fields
                if not all(key in user_data for key in ['email', 'name', 'password']):
                    print(f"⚠️  Skipping invalid user data: {user_data}")
                    skipped_count += 1
                    continue
                
                email = user_data['email']
                name = user_data['name']
                password = user_data['password']
                
                # Check if user already exists
                existing_user = await auth_service.get_user_by_email(email)
                if existing_user:
                    print(f"⏭️  User already exists: {email}")
                    skipped_count += 1
                    continue
                
                # Create user
                user = await auth_service.create_user(
                    email=email,
                    password=password,
                    name=name
                )
                
                print(f"✅ Created user: {user.email} ({user.name})")
                created_count += 1
                
            except Exception as e:
                print(f"❌ Error creating user {user_data.get('email', 'unknown')}: {e}")
                error_count += 1
    
    print("\n" + "="*50)
    print("Seeding Summary:")
    print(f"  ✅ Created: {created_count}")
    print(f"  ⏭️  Skipped: {skipped_count}")
    print(f"  ❌ Errors: {error_count}")
    print("="*50)
    print("\nUser seeder completed!")


if __name__ == "__main__":
    # Allow passing JSON file path as argument
    json_path = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(seed_users(json_path))

