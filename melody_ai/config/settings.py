from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_name: str = "MELODY AI"
    environment: str = "production"
    bot_token: SecretStr = Field(default=SecretStr(""), validation_alias="BOT_TOKEN")
    database_url: str = "postgresql+asyncpg://melody:melody@postgres:5432/melody"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: SecretStr = Field(default=SecretStr("change-me"), validation_alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    spotify_client_id: str | None = None
    spotify_client_secret: SecretStr | None = None
    deezer_base_url: str = "https://api.deezer.com"
    audd_api_token: SecretStr | None = None
    admin_ids: str = ""

    @property
    def admin_id_set(self) -> set[int]:
        return {int(v) for v in self.admin_ids.split(",") if v.strip().isdigit()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
