from typing import Protocol

from app.ai_recipes.schemas import ProviderGenerationResult, RecipeGenerationRequest
from app.core.config import Settings


class AiProviderError(RuntimeError):
    """Base error safe for service-level mapping."""


class AiProviderUnavailable(AiProviderError):
    """Retryable provider availability or rate-limit error."""


class AiProviderConfigurationError(AiProviderError):
    """Missing or rejected provider configuration."""


class AiProviderResponseError(AiProviderError):
    """Provider returned content that violates the JSON contract."""


class AiRecipeProvider(Protocol):
    def generate_recipes(self, request: RecipeGenerationRequest) -> ProviderGenerationResult: ...


def get_ai_recipe_provider(settings: Settings) -> AiRecipeProvider:
    if settings.ai_provider != "deepseek" or not settings.ai_api_key:
        raise AiProviderConfigurationError("AI recipe provider is not configured")
    from app.ai_recipes.deepseek import DeepSeekRecipeProvider

    return DeepSeekRecipeProvider(
        api_key=settings.ai_api_key,
        model=settings.ai_model,
        base_url=settings.ai_base_url,
        timeout_seconds=settings.ai_timeout_seconds,
    )
