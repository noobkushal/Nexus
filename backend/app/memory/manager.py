"""Memory and Persistence Abstraction Layer."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings
from app.core.logging import logger

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryRecordModel(Base):
    __tablename__ = "nexus_memories"

    id = Column(String(36), primary_key=True)
    category = Column(String(50), nullable=False, default="general")
    key = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    importance = Column(Integer, default=1)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class MemoryItem(BaseModel):
    id: str
    category: str
    key: str
    content: str
    importance: int = 1
    created_at: datetime = Field(default_factory=utc_now)


class MemoryManager:
    """Manages working and persistent memory with database-agnostic fallback."""

    def __init__(self):
        self._in_memory_records: Dict[str, MemoryItem] = {}
        self._db_enabled = False
        self._init_storage()

    def _init_storage(self):
        try:
            if settings.DATABASE_URL:
                self.engine = create_engine(settings.DATABASE_URL)
                Base.metadata.create_all(self.engine)
                self.SessionLocal = sessionmaker(bind=self.engine)
                self._db_enabled = True
                logger.info(f"Database memory backend connected: {settings.DATABASE_URL.split('@')[-1]}")
            else:
                # Local SQLite in-memory fallback
                self.engine = create_engine("sqlite:///:memory:", echo=False)
                Base.metadata.create_all(self.engine)
                self.SessionLocal = sessionmaker(bind=self.engine)
                self._db_enabled = True
                logger.info("Memory backend initialized with lightweight in-memory SQLite store.")
        except Exception as exc:
            logger.warning(f"Database initialization failed ({exc}). Using in-memory dictionary store.")
            self._db_enabled = False

        self._seed_default_memories()

    def _seed_default_memories(self):
        seeds = [
            ("profile", "user_identity", "Primary user: Developer & Architect."),
            ("system", "platform_mode", "NEXUS operating in local-first standalone foundation mode."),
            ("preferences", "theme", "Dark mode aesthetic with high-contrast information density."),
        ]
        for cat, key, val in seeds:
            self.store_memory(category=cat, key=key, content=val, importance=2)

    def store_memory(self, category: str, key: str, content: str, importance: int = 1) -> MemoryItem:
        mem_id = f"{category}:{key}"
        item = MemoryItem(
            id=mem_id,
            category=category,
            key=key,
            content=content,
            importance=importance,
            created_at=utc_now(),
        )
        self._in_memory_records[mem_id] = item

        if self._db_enabled:
            try:
                session = self.SessionLocal()
                existing = session.query(MemoryRecordModel).filter_by(id=mem_id).first()
                if existing:
                    existing.content = content
                    existing.importance = importance
                    existing.updated_at = utc_now()
                else:
                    rec = MemoryRecordModel(
                        id=mem_id,
                        category=category,
                        key=key,
                        content=content,
                        importance=importance,
                    )
                    session.add(rec)
                session.commit()
                session.close()
            except Exception as e:
                logger.debug(f"DB memory write skipped: {e}")

        return item

    def get_memory(self, category: str, key: str) -> Optional[MemoryItem]:
        mem_id = f"{category}:{key}"
        return self._in_memory_records.get(mem_id)

    def list_memories(self, category: Optional[str] = None) -> List[MemoryItem]:
        items = list(self._in_memory_records.values())
        if category:
            items = [i for i in items if i.category == category]
        return sorted(items, key=lambda x: x.importance, reverse=True)


memory_manager = MemoryManager()
