"""
Application configuration loaded from environment variables.

Uses pydantic-settings for validation and .env loading.
All sensitive/configurable values should be defined here.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Values can be overridden via .env file or environment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Project
    project_name: str = "Sustainability & SDG Reporting Hub"
    environment: str = "development"
    debug: bool = False

    # API
    api_v1_prefix: str = "/api/v1"

    # PostgreSQL — individual fields (used to build DATABASE_URL if not set)
    postgres_server: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "sustainability_hub"
    postgres_user: str = "hub_user"
    postgres_password: str = ""

    # Optional: full database URL (if set, overrides individual postgres_* fields)
    database_url: Optional[str] = None

    # JWT / Auth (Step 3)
    secret_key: str = "change-me-in-production-use-long-random-secret"
    access_token_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"

    # CORS: comma-separated origins (e.g. https://app.vercel.app); if empty, localhost origins are used
    cors_origins: str = ""

    # First admin bootstrap (seed_admin.py)
    first_admin_name: str = "System Admin"
    first_admin_email: str = "admin@example.com"
    first_admin_password: str = "ChangeMe123!"

    # File upload (Step 9 — evidence)
    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 10
    allowed_evidence_extensions: str = "pdf,xlsx,xls,csv,jpg,jpeg,png,doc,docx"

    # LLM / AI (Step 11 — report section generation)
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None  # Optional override for API base URL

    @property
    def allowed_evidence_extensions_list(self) -> list[str]:
        """Allowed evidence file extensions (lowercase, no dots)."""
        return [x.strip().lstrip(".").lower() for x in self.allowed_evidence_extensions.split(",") if x.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        """Max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def sqlmodel_database_url(self) -> str:
        """
        URL for SQLModel (sync driver). Used by Alembic and session creation.
        Builds from postgres_* if database_url is not set.
        """
        if self.database_url:
            # Ensure we use sync driver for SQLModel/Alembic
            url = self.database_url
            if url.startswith("postgresql+asyncpg"):
                url = url.replace("postgresql+asyncpg", "postgresql", 1)
            return url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance. Use this in the app instead of creating new Settings."""
    return Settings()
