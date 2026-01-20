# Hena Books API

A FastAPI-based REST API for managing and reading Christian/Biblical books.

## 📚 Features

- **Authentication** - JWT-based auth with access and refresh tokens
- **Books Management** - Upload, manage, and serve PDF books
- **Categories** - Organize books by Biblical topics (Theology, Devotional, etc.)
- **Reading Sessions** - Track user reading progress and analytics
- **Admin Dashboard** - Platform statistics and user management

## 🏗️ Architecture

```
app/
├── api/                    # API routes
│   ├── deps.py            # Dependency injection
│   └── v1/                # API version 1
│       ├── auth.py        # Authentication endpoints
│       ├── books.py       # Book endpoints
│       ├── users.py       # User endpoints
│       ├── analytics.py   # Analytics endpoints
│       └── router.py      # Route aggregation
├── core/                   # Core configuration
│   ├── config.py          # Settings management
│   ├── database.py        # Database setup
│   ├── security.py        # JWT & password hashing
│   └── exceptions.py      # Custom exceptions
├── models/                 # SQLAlchemy models
│   ├── base.py            # Base model with timestamps
│   ├── user.py            # User model
│   ├── book.py            # Book model with categories
│   ├── reading_session.py # Reading tracking
│   └── password_reset.py  # Password reset tokens
├── repositories/           # Data access layer
│   ├── base.py            # Generic CRUD operations
│   ├── user_repository.py
│   ├── book_repository.py
│   └── reading_session_repository.py
├── schemas/                # Pydantic schemas
│   ├── auth.py            # Auth request/response
│   ├── user.py            # User schemas
│   ├── book.py            # Book schemas
│   └── analytics.py       # Analytics schemas
├── services/               # Business logic layer
│   ├── auth.py            # Authentication logic
│   ├── book_service.py    # Book management
│   ├── cloudinary.py      # File upload service
│   └── analytics.py       # Analytics calculations
├── middleware/             # Custom middleware
│   └── logging.py         # Request logging
├── utils/                  # Utilities
│   └── email.py           # Email sending
└── main.py                 # Application entry point
```

## 📖 Book Categories

Books are organized into the following categories:

| Category | Description |
|----------|-------------|
| Biblical Studies | In-depth study of Scripture |
| Theology | Systematic theology and doctrine |
| Devotional | Daily devotionals and meditations |
| Christian Living | Practical Christian life |
| Prayer & Worship | Prayer guides and worship |
| Church History | History of Christianity |
| Apologetics | Defense of the faith |
| Family & Marriage | Family-focused content |
| Youth & Children | Content for young readers |
| Missions & Evangelism | Outreach and missions |
| Spiritual Growth | Growth in faith |
| Biography & Testimony | Christian biographies |
| Commentary | Bible commentaries |
| Reference | Reference materials |

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL (or Neon PostgreSQL)
- Cloudinary account (for file storage)

### Installation

1. **Clone the repository**
```bash
cd hena_books_api
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run migrations**
```bash
alembic upgrade head
```

6. **Start the server**
```bash
uvicorn app.main:app --reload
```

## ⚙️ Configuration

Create a `.env` file with:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# Security
SECRET_KEY=your-secret-key-here
DEBUG=true

# CORS
CORS_ORIGINS=http://localhost:3000

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Email (optional)
SMTP_EMAIL=your@email.com
SMTP_PASSWORD=your-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/forgot-password` | Request reset code |
| POST | `/api/v1/auth/reset-password` | Reset password |

### Books (Public)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/books` | List books with filters |
| GET | `/api/v1/books/featured` | Get featured books |
| GET | `/api/v1/books/categories` | Get all categories |
| GET | `/api/v1/books/{id}` | Get book details |
| GET | `/api/v1/books/{id}/read` | Get book for reading |

### Books (Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/books/admin/all` | List all books |
| POST | `/api/v1/books/admin/upload` | Upload new book |
| PUT | `/api/v1/books/admin/{id}` | Update book |
| DELETE | `/api/v1/books/admin/{id}` | Delete book |
| PATCH | `/api/v1/books/admin/{id}/toggle-featured` | Toggle featured |
| PATCH | `/api/v1/books/admin/{id}/toggle-published` | Toggle published |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/reading/start` | Start reading session |
| PUT | `/api/v1/reading/{id}/update` | Update progress |
| POST | `/api/v1/reading/{id}/end` | End session |
| GET | `/api/v1/admin/analytics/overview` | Platform stats |

## 🔐 Authentication

The API uses JWT tokens:

1. **Access Token** - Valid for 60 minutes
2. **Refresh Token** - Valid for 7 days

Include the access token in requests:
```
Authorization: Bearer <access_token>
```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app
```

## 📦 Deployment

### Docker

```bash
docker build -t hena-books-api .
docker run -p 8000:8000 --env-file .env hena-books-api
```

### Production Settings

```env
DEBUG=false
LOG_LEVEL=WARNING
```

## 📄 License

MIT License - See LICENSE file for details.

---

Built with ❤️ for sharing Biblical knowledge.
