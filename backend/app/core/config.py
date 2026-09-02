from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

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
    ai_provider: Literal["deepseek"] = "deepseek"
    ai_base_url: str = "https://api.deepseek.com"
    ai_model: str = "deepseek-v4-flash"
    ai_api_key: str = ""
    ai_recipe_enabled: bool = False
    ai_timeout_seconds: float = 25.0
    ai_max_retries: int = 0
    ai_recipe_session_ttl_hours: int = 24
    ai_recipe_user_limit_per_hour: int = 20
    ai_recipe_ip_limit_per_hour: int = 60
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
        if self.ai_recipe_enabled:
            if not self.ai_api_key:
                raise ValueError("production AI recipe API key is required when the feature is enabled")
            parsed_ai_url = urlparse(self.ai_base_url)
            if parsed_ai_url.scheme != "https" or parsed_ai_url.hostname != "api.deepseek.com":
                raise ValueError("production AI recipes must use the official DeepSeek API")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
