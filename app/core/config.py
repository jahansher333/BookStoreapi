from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated settings loaded from environment variables and `.env`."""
    # Pydantic Settings maps these fields to environment variables.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Bookstore Inventory API"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    api_key: SecretStr | None = None

    # Normal API traffic uses the pooled application connection.
    database_url: PostgresDsn
    # Alembic can use a separate direct connection for migrations.
    migration_database_url: PostgresDsn | None = None

    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 300
    db_connect_timeout: int = 10


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
"""Environment-backed application settings."""
