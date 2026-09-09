from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "NoticeSense"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://noticesense:noticesense@db:5432/noticesense"
    redis_url: str = "redis://redis:6379/0"

    # AI provider
    ai_provider: Literal["ollama", "gemini"] = "ollama"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1"

    # Uploads
    upload_dir: str = "/data/uploads"
    max_upload_size_mb: int = 20

    # OCR
    ocr_language: str = "eng"

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    # Synchronous DB URL for Alembic / Celery contexts that need psycopg2.
    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "").replace("postgresql://", "postgresql+psycopg2://")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
