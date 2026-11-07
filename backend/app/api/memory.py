"""Memory and Profile API Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from app.memory.manager import MemoryItem, memory_manager

router = APIRouter(prefix="/api/v1/memory", tags=["Memory"])


class MemoryCreateRequest(BaseModel):
    category: str = Field(..., max_length=50)
    key: str = Field(..., max_length=100)
    content: str = Field(..., max_length=5000)
    importance: int = Field(1, ge=1, le=5)


@router.get("", response_model=List[MemoryItem])
async def list_memories(
    category: Optional[str] = Query(None, description="Filter by category (e.g. 'profile', 'preferences')"),
) -> List[MemoryItem]:
    """Retrieves stored memory items with optional category filtering."""
    return memory_manager.list_memories(category=category)


@router.post("", response_model=MemoryItem)
async def store_memory(req: MemoryCreateRequest) -> MemoryItem:
    """Stores a new memory record."""
    return memory_manager.store_memory(
        category=req.category,
        key=req.key,
        content=req.content,
        importance=req.importance,
    )
