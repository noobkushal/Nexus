"""NEXUS AI — Main FastAPI Application Entry Point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.agents import router as agents_router
from app.api.approvals import router as approvals_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.memory import router as memory_router
from app.api.settings import router as settings_router
from app.api.storage import router as storage_router
from app.api.tasks import router as tasks_router
from app.api.workflows import router as workflows_router
from app.core.config import settings
from app.core.logging import logger
from app.providers.registry import provider_registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager handling startup and shutdown."""
    logger.info("==================================================")
    logger.info(f"Starting {settings.PROJECT_NAME} v0.1.0")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")
    logger.info(f"Active AI Provider: {provider_registry.active_provider.name} (is_mock={provider_registry.active_provider.is_mock})")
    logger.info("Storage Directory: %s", settings.STORAGE_DIR)
    logger.info("All external dependencies (Ollama, PostgreSQL, n8n) are OPTIONAL.")
    logger.info("==================================================")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME} cleanly.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Modular, local-first, multi-agent personal AI automation platform.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred in NEXUS backend.",
            "path": str(request.url.path),
        },
    )


# Mount API Routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(tasks_router)
app.include_router(agents_router)
app.include_router(approvals_router)
app.include_router(storage_router)
app.include_router(settings_router)
app.include_router(workflows_router)
app.include_router(memory_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "mode": "standalone_offline",
    }
