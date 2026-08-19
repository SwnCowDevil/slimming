from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SLIMMING_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/slimming.db"
    jwt_secret: str = "development-only-change-me"
    jwt_ttl_seconds: int = 60 * 60 * 24 * 7
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    enable_dev_auth: bool = False
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = ""
    ai_api_key: str = ""
    media_root: Path = Path("./data/media")
    tka_import_root: Path = Path("./data/imports")


@lru_cache
def get_settings() -> Settings:
    return Settings()

