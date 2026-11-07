"""Health and System Status Endpoints."""
from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter
from app.core.config import settings
from app.providers.registry import provider_registry
from app.tools.ollama import OllamaClient

router = APIRouter(tags=["Health"])


@router.get("/health")
@router.get("/api/v1/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint confirming backend availability and component states."""
    active_provider = provider_registry.active_provider
    provider_status = await active_provider.check_status()

    return {
        "status": "operational",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ai_provider": {
            "name": provider_status.name,
            "is_mock": provider_status.is_mock,
            "is_available": provider_status.is_available,
            "details": provider_status.details,
        },
        "database": {
            "type": "postgresql" if settings.DATABASE_URL else "sqlite_in_memory",
            "is_available": True,
        },
        "automation": {
            "n8n_connected": bool(settings.N8N_WEBHOOK_URL),
            "mode": "standalone_interface",
        },
        "dependencies": {
            "ollama_required": False,
            "external_apis_required": False,
            "postgres_required": False,
            "n8n_required": False,
        },
    }


@router.get("/model-status")
@router.get("/api/v1/model-status")
async def model_status_check() -> Dict[str, Any]:
    """Inspects optional local Ollama connectivity and target model presence non-blockingly."""
    client = OllamaClient()
    conn_info = await client.check_connectivity()
    return {
        "target_model": settings.OLLAMA_MODEL,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "connectivity": conn_info,
        "active_system_provider": provider_registry.active_provider.name,
        "note": "NEXUS foundation is independent of Ollama; this endpoint is for optional local hardware diagnostic.",
    }
