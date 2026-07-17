from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_name: str = "PharmaLink"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    bot_token: str = Field("", alias="BOT_TOKEN")
    database_url: str = Field(
        "postgresql+asyncpg://pharmalink:pharmalink@postgres:5432/pharmalink", alias="DATABASE_URL"
    )
    redis_url: str = Field("redis://redis:6379/0", alias="REDIS_URL")
    jwt_secret: str = Field("change-me", alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    erp_provider: str = Field("mock", alias="ERP_PROVIDER")
    erp_enabled: bool = Field(False, alias="ERP_ENABLED")
    erp_url: str = Field("", alias="ERP_URL")
    erp_login: str = Field("", alias="ERP_LOGIN")
    erp_password: str = Field("", alias="ERP_PASSWORD")
    sync_interval_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
