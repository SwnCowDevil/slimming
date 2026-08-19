from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SLIMMING_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/slimming.db"
    environment: Literal["development", "test", "production"] = "development"
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
    admin_import_key: str = ""

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.environment != "production":
            return self
        if len(self.jwt_secret) < 32 or self.jwt_secret == "development-only-change-me" or self.jwt_secret.startswith("replace-"):
            raise ValueError("production JWT secret must be a non-default value of at least 32 characters")
        if not self.wechat_app_id or not self.wechat_app_secret or self.wechat_app_id == "wx-your-app-id" or self.wechat_app_secret.startswith("replace-"):
            raise ValueError("production WeChat credentials are required")
        if self.enable_dev_auth:
            raise ValueError("development authentication must be disabled in production")
        if len(self.admin_import_key) < 24 or self.admin_import_key.startswith("replace-"):
            raise ValueError("production admin import key must be at least 24 characters")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
