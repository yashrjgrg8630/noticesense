from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "ai_provider": settings.ai_provider,
        "ai_model": settings.gemini_model if settings.ai_provider == "gemini" else settings.ollama_model,
    }
