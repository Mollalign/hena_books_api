from logging.config import fileConfig
import asyncio
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from alembic import context

# Import Base and all models for autogenerate support
from app.core.database import Base
from app.models.user import User
from app.models.book import Book
from app.models.reading_session import ReadingSession
from app.models.password_reset import PasswordReset

# Import settings for database URL
from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata for autogenerate support
target_metadata = Base.metadata

# Override sqlalchemy.url with settings from app
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Convert asyncpg URL to psycopg2 for Alembic (synchronous)
    # Alembic needs a synchronous driver
    database_url = str(settings.DATABASE_URL)
    if database_url.startswith("postgresql+asyncpg://"):
        # Replace asyncpg with psycopg2 for Alembic
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    # Create synchronous engine for Alembic
    connectable = engine_from_config(
        {"sqlalchemy.url": database_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
