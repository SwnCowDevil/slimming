import json

import httpx
import pytest

from app.ai_recipes.deepseek import DeepSeekRecipeProvider
from app.ai_recipes.provider import (
    AiProviderConfigurationError,
    AiProviderResponseError,
    AiProviderUnavailable,
)
from app.ai_recipes.schemas import RecipeGenerationRequest
from app.main import create_app


def _candidate_payload() -> dict:
    return {
        "title": "番茄鸡丁饭",
        "summary": "清淡家常的一餐",
        "meal_type": "dinner",
        "tags": ["high-protein", "home-style"],
        "servings": 1,
        "minutes": 25,
        "ingredients": [
            {
                "name_zh": "鸡胸肉",
                "quantity": 120,
                "unit": "克",
                "grams": 120,
                "energy_kcal_per_100g": 133,
                "protein_g_per_100g": 24,
                "fat_g_per_100g": 3,
                "carbohydrate_g_per_100g": 0,
                "fiber_g_per_100g": 0,
            }
        ],
        "steps": ["鸡肉彻底加热至全熟。"],
        "allergens": [],
        "nutrition_per_serving": {
            "energy_kcal": 320,
            "protein_g": 30,
            "fat_g": 8,
            "carbohydrate_g": 32,
            "fiber_g": 4,
        },
        "recommendation_reason": "满足清淡晚餐需求",
        "cooking_requirements": ["禽肉必须全熟"],
    }


def _request() -> RecipeGenerationRequest:
    return RecipeGenerationRequest(
        pregnancy_stage="second_trimester",
        allergens=["peanut"],
        avoidances=["raw_food"],
        filters={"meal_type": "dinner", "max_minutes": 30, "flavors": ["light"]},
        query="冰箱里有鸡蛋和番茄",
        excluded_fingerprints=[],
    )


def test_deepseek_provider_requests_json_and_returns_usage_metadata():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "model": "deepseek-v4-flash",
                "choices": [{"message": {"content": json.dumps({"recipes": [_candidate_payload()]}, ensure_ascii=False)}}],
                "usage": {"prompt_tokens": 123, "completion_tokens": 88},
            },
        )

    provider = DeepSeekRecipeProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        client=httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://api.deepseek.com",
        ),
    )

    result = provider.generate_recipes(_request())

    assert result.candidates[0].title == "番茄鸡丁饭"
    assert result.model == "deepseek-v4-flash"
    assert result.usage.input_tokens == 123
    assert result.usage.output_tokens == 88
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert captured["body"]["thinking"] == {"type": "disabled"}
    assert captured["body"]["max_tokens"] == 3000
    user_payload = json.loads(captured["body"]["messages"][1]["content"])
    assert user_payload["request"]["pregnancy_stage"] == "second_trimester"
    recipe_array_schema = user_payload["output_schema"]["properties"]["recipes"]
    assert recipe_array_schema["minItems"] == 3
    assert recipe_array_schema["maxItems"] == 3
    ingredient_schema = user_payload["output_schema"]["$defs"]["CandidateIngredient"]
    assert {"name_zh", "grams", "energy_kcal_per_100g"}.issubset(ingredient_schema["required"])
    recipe_schema = user_payload["output_schema"]["$defs"]["RecipeCandidate"]
    assert recipe_schema["properties"]["ingredients"]["maxItems"] == 8
    assert recipe_schema["properties"]["steps"]["maxItems"] == 5
    assert recipe_schema["properties"]["cooking_requirements"]["maxItems"] == 3


@pytest.mark.parametrize("status_code", [429, 500, 503])
def test_retryable_provider_status_is_reported_as_unavailable(status_code):
    provider = DeepSeekRecipeProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        client=httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(status_code)),
            base_url="https://api.deepseek.com",
        ),
    )

    with pytest.raises(AiProviderUnavailable):
        provider.generate_recipes(_request())


@pytest.mark.parametrize("status_code", [401, 402])
def test_credentials_and_payment_errors_are_configuration_errors(status_code):
    provider = DeepSeekRecipeProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        client=httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(status_code)),
            base_url="https://api.deepseek.com",
        ),
    )

    with pytest.raises(AiProviderConfigurationError):
        provider.generate_recipes(_request())


@pytest.mark.parametrize("content", ["", "not-json", '{"recipes": ['])
def test_invalid_provider_content_is_rejected(content):
    provider = DeepSeekRecipeProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
            ),
            base_url="https://api.deepseek.com",
        ),
    )

    with pytest.raises(AiProviderResponseError):
        provider.generate_recipes(_request())


def test_app_initializes_one_shared_recipe_provider(monkeypatch, settings):
    sentinel = object()
    settings.ai_recipe_enabled = True
    settings.ai_api_key = "test-provider-key"
    monkeypatch.setattr("app.main.get_ai_recipe_provider", lambda configured: sentinel)

    app = create_app(settings=settings)

    assert app.state.ai_recipe_provider is sentinel
