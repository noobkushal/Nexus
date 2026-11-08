"""Database Engine, Session Management, and Lifecycle."""
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings
from app.core.logging import logger

Base = declarative_base()


def get_database_url() -> str:
    """Returns configured PostgreSQL URL or falls back to local sandboxed SQLite."""
    if settings.DATABASE_URL:
        return settings.DATABASE_URL

    # Default to local SQLite inside sandboxed storage
    storage_dir = Path(settings.STORAGE_DIR).resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)
    db_file = storage_dir / "nexus_local.db"
    return f"sqlite:///{db_file.as_posix()}"


# Setup engine with thread-safety for SQLite
db_url = get_database_url()
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes all database tables safely without requiring PostgreSQL."""
    try:
        from app.db import models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        # Lightweight additive migration for databases created before auth fields existed.
        existing_columns = {column["name"] for column in inspect(engine).get_columns("users")}
        auth_columns = {
            "password_hash": "VARCHAR(255)",
            "is_active": "BOOLEAN NOT NULL DEFAULT TRUE",
            "token_version": "INTEGER NOT NULL DEFAULT 0",
        }
        with engine.begin() as connection:
            for column_name, column_ddl in auth_columns.items():
                if column_name not in existing_columns:
                    connection.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_ddl}"))
        logger.info(f"Database schema initialized using: {engine.url.drivername}")
    except Exception as e:
        logger.error(f"Database initialization error: {e}", exc_info=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for thread-safe database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
