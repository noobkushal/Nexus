"""Centralized Application Configuration."""
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent
DEFAULT_STORAGE_DIR = ROOT_DIR / "storage"


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # General
    PROJECT_NAME: str = "NEXUS AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Provider-neutral AI configuration
    # Mock remains the safe default; real providers are opt-in.
    DEFAULT_PROVIDER: str = "mock"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3.5:4b"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0
    OPENAI_COMPAT_BASE_URL: Optional[str] = None
    OPENAI_COMPAT_API_KEY: Optional[str] = None
    OPENAI_COMPAT_MODEL: Optional[str] = None
    OPENAI_COMPAT_TIMEOUT_SECONDS: float = 45.0

    # Database Configuration (Optional - falls back to SQLite in-memory/local file)
    DATABASE_URL: Optional[str] = None

    # Authentication: set both secrets through the environment before enabling login.
    AUTH_SECRET_KEY: Optional[str] = None
    AUTH_BOOTSTRAP_SECRET: Optional[str] = None
    ACCESS_TOKEN_TTL_MINUTES: int = 20

    # Storage Paths
    STORAGE_DIR: Path = DEFAULT_STORAGE_DIR

    # Automation (n8n placeholders)
    N8N_WEBHOOK_URL: Optional[str] = None

    # Security & CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
