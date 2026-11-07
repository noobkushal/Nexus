"""Application and Provider Settings Endpoints."""
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import settings
from app.providers.base import ProviderStatus
from app.providers.registry import provider_registry

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])


class SetProviderRequest(BaseModel):
    provider_name: str


@router.get("")
async def get_settings_summary() -> Dict[str, Any]:
    """Returns overview of system configuration and provider states."""
    statuses = await provider_registry.list_statuses()
    return {
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "host": settings.HOST,
        "port": settings.PORT,
        "log_level": settings.LOG_LEVEL,
        "active_provider": provider_registry.active_provider.name,
        "registered_providers": [s.model_dump() for s in statuses],
        "storage_directory": str(settings.STORAGE_DIR),
        "database": {
            "type": "postgresql" if settings.DATABASE_URL else "sqlite_in_memory",
            "url_configured": bool(settings.DATABASE_URL),
        },
    }


@router.post("/provider")
async def switch_active_provider(request: SetProviderRequest) -> Dict[str, Any]:
    """Switches default active AI provider (e.g. 'mock')."""
    success = provider_registry.set_active_provider(request.provider_name)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{request.provider_name}' is not registered.",
        )
    return {
        "success": True,
        "active_provider": provider_registry.active_provider.name,
        "is_mock": provider_registry.active_provider.is_mock,
    }
