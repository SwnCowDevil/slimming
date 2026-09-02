import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_default_secrets():
    with pytest.raises(ValidationError):
        Settings(environment="production")


def test_production_rejects_example_placeholders():
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            jwt_secret="replace-with-at-least-32-random-characters",
            wechat_app_id="wx-your-app-id",
            wechat_app_secret="replace-with-wechat-app-secret",
            admin_import_key="replace-with-a-separate-random-key",
        )


def test_production_accepts_complete_secure_configuration():
    settings = Settings(
        environment="production",
        jwt_secret="j" * 32,
        wechat_app_id="wx-production",
        wechat_app_secret="wechat-secret",
        admin_import_key="i" * 24,
        enable_dev_auth=False,
    )
    assert settings.environment == "production"


def test_production_rejects_enabled_ai_recipes_without_provider_key():
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            jwt_secret="j" * 32,
            wechat_app_id="wx-production",
            wechat_app_secret="wechat-secret",
            admin_import_key="i" * 24,
            enable_dev_auth=False,
            ai_recipe_enabled=True,
            ai_api_key="",
        )


def test_production_allows_ai_recipes_to_remain_disabled_without_key():
    settings = Settings(
        environment="production",
        jwt_secret="j" * 32,
        wechat_app_id="wx-production",
        wechat_app_secret="wechat-secret",
        admin_import_key="i" * 24,
        enable_dev_auth=False,
        ai_recipe_enabled=False,
        ai_api_key="",
    )
    assert settings.ai_recipe_enabled is False


def test_production_rejects_lookalike_deepseek_hostname():
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            jwt_secret="j" * 32,
            wechat_app_id="wx-production",
            wechat_app_secret="wechat-secret",
            admin_import_key="i" * 24,
            ai_recipe_enabled=True,
            ai_api_key="provider-key",
            ai_base_url="https://api.deepseek.com.evil.example",
        )
