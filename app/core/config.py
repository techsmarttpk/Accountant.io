"""Application configuration.

All runtime configuration is centralized here and sourced from environment
variables / a local .env file. Nothing in this codebase should hardcode a
secret, a file path, or an environment-specific value outside of this module.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App metadata -----------------------------------------------------
    app_name: str = "Accountant.io"
    environment: str = Field(default="development")  # development | staging | production
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # --- Server -------------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Database -------------------------------------------------------------
    # Async SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@host:5432/dbname
    # Defaults to a local SQLite file so the service is runnable with zero
    # external setup; production deployments MUST override this via env var.
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{PROJECT_ROOT / 'data' / 'accountant.db'}"
    )
    database_echo: bool = False

    # --- Security -------------------------------------------------------------
    # Shared-secret API key required on every inbound request from the bot
    # (or any other first-party client) to the backend. Rotate via env var,
    # never via source code.
    internal_api_key: SecretStr = Field(default=SecretStr("changeme-set-in-env"))

    # --- Telegram -------------------------------------------------------------
    telegram_bot_token: SecretStr | None = Field(default=None)
    backend_base_url: str = Field(default="http://localhost:8000")

    # --- File storage -------------------------------------------------------------
    storage_dir: Path = Field(default=PROJECT_ROOT / "data" / "uploads")
    max_upload_size_mb: int = 15

    # --- RAG -------------------------------------------------------------
    knowledge_base_dir: Path = Field(default=PROJECT_ROOT / "data" / "knowledge_base")
    rag_top_k: int = 3
    rag_min_score: float = 0.05

    # --- Speech-to-text -------------------------------------------------------------
    stt_provider: str = "google_web"  # google_web (dev/free) | whisper (production)

    # --- Logging -------------------------------------------------------------
    log_level: str = "INFO"
    log_json: bool = True

    @field_validator("environment")
    @classmethod
    def _validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got {v!r}")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor — safe to call repeatedly (e.g. as a FastAPI dependency)."""
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    settings.storage_dir.joinpath("documents").mkdir(parents=True, exist_ok=True)
    settings.storage_dir.joinpath("audio").mkdir(parents=True, exist_ok=True)
    return settings
