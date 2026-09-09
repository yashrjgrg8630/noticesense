import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Calculate project root dynamically (backend/core/ → backend/ → project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .env is at the project root – use absolute path so it always resolves correctly
_ENV_FILE = os.path.join(PROJECT_ROOT, ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App Settings
    APP_NAME: str = "NoticeSense"
    PROJECT_VERSION: str = "0.3.0"

    # Gemini API (used when LLM_BACKEND=gemini)
    GEMINI_API_KEY: str = ""

    # LLM Backend — "gemini" or "ollama"
    LLM_BACKEND: str = "gemini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3:4b"

    # Path configurations
    TESSERACT_CMD: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    POPPLER_PATH: str = os.path.join(PROJECT_ROOT, ".poppler", "poppler-24.08.0", "Library", "bin")

    # Storage
    UPLOAD_DIR: str = "data/uploads"


# Single shared instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
