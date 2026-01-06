# User Seeding Guide

This guide shows you how to add dummy users to your database.

## Method 1: Using the Seed Script (Recommended)

### Step 1: Prepare JSON File

The `dummy_users.json` file contains example users. You can modify it or create your own:

```json
[
  {
    "email": "user@example.com",
    "name": "User Name",
    "password": "password123"
  }
]
```

### Step 2: Run the Seed Script

```bash
# Using default dummy_users.json
python -m app.scripts.seed_users

# Or specify a custom JSON file
python -m app.scripts.seed_users path/to/your/users.json
```

## Method 2: Using the API Endpoint

### Using cURL

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "name": "John Doe",
    "password": "password123"
  }'
```

### Using Python requests

```python
import requests

url = "http://127.0.0.1:8000/api/v1/auth/register"
users = [
    {
        "email": "john.doe@example.com",
        "name": "John Doe",
        "password": "password123"
    },
    {
        "email": "jane.smith@example.com",
        "name": "Jane Smith",
        "password": "password123"
    }
]

for user in users:
    response = requests.post(url, json=user)
    if response.status_code == 201:
        print(f"✅ Created: {user['email']}")
    else:
        print(f"❌ Error: {user['email']} - {response.json()}")
```

### Using JavaScript/Fetch

```javascript
const users = [
  {
    email: "john.doe@example.com",
    name: "John Doe",
    password: "password123"
  }
];

for (const user of users) {
  fetch('http://127.0.0.1:8000/api/v1/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(user)
  })
  .then(response => response.json())
  .then(data => console.log('Created:', data))
  .catch(error => console.error('Error:', error));
}
```

## Method 3: Using Swagger UI

1. Start your server: `uvicorn app.main:app --reload`
2. Open browser: `http://127.0.0.1:8000/docs`
3. Find the `POST /api/v1/auth/register` endpoint
4. Click "Try it out"
5. Paste your JSON in the request body
6. Click "Execute"

## Example JSON for Multiple Users

```json
[
  {
    "email": "reader1@example.com",
    "name": "Reader One",
    "password": "securepass123"
  },
  {
    "email": "reader2@example.com",
    "name": "Reader Two",
    "password": "securepass123"
  },
  {
    "email": "reader3@example.com",
    "name": "Reader Three",
    "password": "securepass123"
  }
]
```

## Notes

- Email must be unique (will skip if already exists)
- Password must be at least 6 characters
- Name must be 2-100 characters
- All users are created with `USER` role by default
- Users are created as active by default

