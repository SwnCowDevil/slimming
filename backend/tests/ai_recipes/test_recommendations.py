from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.ai_recipes.models import AiRecommendationSession, AiRecipeRequestEvent
from app.ai_recipes.provider import AiProviderUnavailable
from app.ai_recipes.schemas import ProviderGenerationResult, ProviderUsage, RecipeCandidate
from app.ai_recipes.service import purge_expired_sessions
from app.auth.models import User
from app.db.session import get_session
from app.recipes.models import Recipe, RecipeItem


def _candidate(title: str) -> RecipeCandidate:
    return RecipeCandidate.model_validate(
        {
            "title": title,
            "summary": "清淡家常的一餐",
            "meal_type": "dinner",
            "tags": ["home-style"],
            "servings": 1,
            "minutes": 25,
            "ingredients": [
                {
                    "name_zh": f"{title}鸡胸肉",
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
            "steps": ["鸡肉彻底加热至中心完全熟透。"],
            "allergens": [],
            "nutrition_per_serving": {
                "energy_kcal": 160,
                "protein_g": 29,
                "fat_g": 3.6,
                "carbohydrate_g": 0,
                "fiber_g": 0,
            },
            "recommendation_reason": "符合清淡晚餐需求",
            "cooking_requirements": ["禽肉必须全熟"],
        }
    )


class FakeProvider:
    def __init__(self, batches: list[list[str]]) -> None:
        self.batches = list(batches)
        self.requests = []

    def generate_recipes(self, request):
        self.requests.append(request)
        titles = self.batches.pop(0)
        return ProviderGenerationResult(
            candidates=[_candidate(title) for title in titles],
            model="fake-deepseek",
            prompt_version="test-prompt-v1",
            latency_ms=12,
            usage=ProviderUsage(input_tokens=100, output_tokens=80),
        )


class UnavailableProvider:
    def generate_recipes(self, request):
        raise AiProviderUnavailable("test outage")


class OnceUnavailableProvider(FakeProvider):
    def __init__(self) -> None:
        super().__init__([["番茄鸡丁", "冬瓜鸡肉汤", "西兰花鸡肉饭"]])
        self.calls = 0

    def generate_recipes(self, request):
        self.calls += 1
        if self.calls == 1:
            raise AiProviderUnavailable("temporary outage")
        return super().generate_recipes(request)


class InconsistentThenValidProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate_recipes(self, request):
        self.calls += 1
        candidates = [_candidate(f"候选{self.calls}-{index}") for index in range(3)]
        if self.calls == 1:
            for candidate in candidates:
                candidate.nutrition_per_serving.energy_kcal = 1
        return ProviderGenerationResult(
            candidates=candidates,
            model="fake-deepseek",
            prompt_version="test-prompt-v1",
            latency_ms=5,
            usage=ProviderUsage(input_tokens=50, output_tokens=50),
        )


class InvalidResponseThenValidProvider(FakeProvider):
    def __init__(self) -> None:
        super().__init__([["番茄鸡丁", "冬瓜鸡肉汤", "西兰花鸡肉饭"]])
        self.calls = 0

    def generate_recipes(self, request):
        from app.ai_recipes.provider import AiProviderResponseError

        self.calls += 1
        if self.calls == 1:
            raise AiProviderResponseError("invalid JSON")
        return super().generate_recipes(request)


class PartialSafeProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate_recipes(self, request):
        self.calls += 1
        safe = _candidate("冬瓜鸡肉汤")
        too_slow = _candidate("慢炖鸡肉汤")
        too_slow.minutes = 60
        wrong_meal = _candidate("早餐鸡蛋")
        wrong_meal.meal_type = "breakfast"
        return ProviderGenerationResult(
            candidates=[safe, too_slow, wrong_meal],
            model="fake-deepseek",
            prompt_version="test-prompt-v1",
            latency_ms=5,
            usage=ProviderUsage(input_tokens=50, output_tokens=50),
        )


def _create_pregnancy(client, headers):
    response = client.post(
        "/api/v1/pregnancies",
        headers=headers,
        json={
            "due_date": (date.today() + timedelta(days=120)).isoformat(),
            "height_cm": 165,
            "current_weight_kg": 61,
            "activity_level": "light",
            "allergens": ["peanut"],
            "avoidances": ["raw_food"],
            "disliked_foods": ["香菜"],
        },
    )
    assert response.status_code == 201


def _add_reviewed_recipes(client, titles: list[str]) -> None:
    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    session.add_all(
        [Recipe(id=f"reviewed-{index}", title=title, visibility="platform") for index, title in enumerate(titles)]
    )
    session.commit()
    session.close()


def _recommend(client, headers, key="recommend-1"):
    return client.post(
        "/api/v1/ai/recipe-recommendations",
        headers={**headers, "Idempotency-Key": key},
        json={
            "filters": {"meal_type": "dinner", "max_minutes": 30, "flavors": ["light"]},
            "query": "冰箱里有鸡蛋和番茄",
        },
    )


def test_recommendation_uses_server_profile_and_returns_three_candidates(client, auth_headers):
    _create_pregnancy(client, auth_headers)
    provider = FakeProvider([["番茄鸡丁", "冬瓜鸡肉汤", "西兰花鸡肉饭"]])
    client.app.state.ai_recipe_provider = provider

    response = _recommend(client, auth_headers)

    assert response.status_code == 201
    payload = response.json()
    assert payload["mode"] == "ai"
    assert len(payload["candidates"]) == 3
    sent = provider.requests[0].model_dump()
    assert sent["pregnancy_stage"] == "second_trimester"
    assert sent["allergens"] == ["peanut"]
    assert "openid" not in sent
    assert "exact_due_date" not in sent


def test_next_batch_excludes_previously_displayed_fingerprints(client, auth_headers):
    _create_pregnancy(client, auth_headers)
    provider = FakeProvider(
        [
            ["番茄鸡丁", "冬瓜鸡肉汤", "西兰花鸡肉饭"],
            ["番茄鸡丁", "菌菇鸡肉煲", "南瓜鸡肉饭", "丝瓜鸡肉汤"],
        ]
    )
    client.app.state.ai_recipe_provider = provider
    first = _recommend(client, auth_headers).json()

    second = client.post(
        f"/api/v1/ai/recipe-recommendations/{first['session_id']}/next",
        headers={**auth_headers, "Idempotency-Key": "recommend-next-1"},
    )

    assert second.status_code == 200
    first_ids = {item["content_fingerprint"] for item in first["candidates"]}
    second_ids = {item["content_fingerprint"] for item in second.json()["candidates"]}
    assert first_ids.isdisjoint(second_ids)
    assert len(second_ids) == 3


def test_repeated_idempotency_key_does_not_call_provider_twice(client, auth_headers):
    _create_pregnancy(client, auth_headers)
    provider = FakeProvider([["番茄鸡丁", "冬瓜鸡肉汤", "西兰花鸡肉饭"]])
    client.app.state.ai_recipe_provider = provider

    first = _recommend(client, auth_headers, "same-key")
    second = _recommend(client, auth_headers, "same-key")

    assert first.json() == second.json()
    assert len(provider.requests) == 1


def test_disabled_provider_returns_reviewed_fallback(client, auth_headers):
    _create_pregnancy(client, auth_headers)
    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    session.add(Recipe(id="fallback-recipe", title="平台番茄汤", visibility="platform"))
    session.commit()
    session.close()

    response = _recommend(client, auth_headers)

    assert response.status_code == 201
    assert response.json()["mode"] == "fallback"
    assert [item["id"] for item in response.json()["candidates"]] == ["fallback-recipe"]


def test_hourly_user_limit_returns_429(client, auth_headers, settings):
    _create_pregnancy(client, auth_headers)
    settings.ai_recipe_user_limit_per_hour = 1
    provider = FakeProvider([["番茄鸡丁", "冬瓜鸡肉汤", "西兰花鸡肉饭"]])
    client.app.state.ai_recipe_provider = provider

    assert _recommend(client, auth_headers, "limit-1").status_code == 201
    assert _recommend(client, auth_headers, "limit-2").status_code == 429


def test_provider_outage_returns_platform_fallback(client, auth_headers):
    _create_pregnancy(client, auth_headers)
    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    session.add(Recipe(id="outage-fallback", title="平台鸡肉粥", visibility="platform"))
    session.commit()
    session.close()
    client.app.state.ai_recipe_provider = UnavailableProvider()

    response = _recommend(client, auth_headers, "outage-key")

    assert response.status_code == 201
    assert response.json()["mode"] == "fallback"
    assert response.json()["candidates"][0]["id"] == "outage-fallback"


def test_retryable_provider_outage_is_retried(client, auth_headers, settings):
    _create_pregnancy(client, auth_headers)
    settings.ai_max_retries = 1
    provider = OnceUnavailableProvider()
    client.app.state.ai_recipe_provider = provider

    response = _recommend(client, auth_headers, "retryable-outage")

    assert response.status_code == 201
    assert response.json()["mode"] == "ai"
    assert provider.calls == 2


def test_invalid_provider_json_is_retried(client, auth_headers, settings):
    _create_pregnancy(client, auth_headers)
    settings.ai_max_retries = 1
    provider = InvalidResponseThenValidProvider()
    client.app.state.ai_recipe_provider = provider

    response = _recommend(client, auth_headers, "invalid-json-retry")

    assert response.status_code == 201
    assert response.json()["mode"] == "ai"
    assert provider.calls == 2


def test_request_dislikes_and_hard_filters_are_enforced(client, auth_headers, settings):
    _create_pregnancy(client, auth_headers)
    _add_reviewed_recipes(client, ["平台南瓜粥", "平台蔬菜汤", "平台番茄饭"])
    settings.ai_max_retries = 1
    provider = FakeProvider(
        [
            ["香菜鸡丁", "超时鸡肉汤", "早餐鸡蛋"],
            ["冬瓜鸡肉汤", "西兰花鸡肉饭", "菌菇鸡肉煲"],
        ]
    )
    disliked = _candidate("香菜鸡丁")
    disliked.ingredients[0].name_zh = "香菜"
    too_slow = _candidate("超时鸡肉汤")
    too_slow.minutes = 60
    wrong_meal = _candidate("早餐鸡蛋")
    wrong_meal.meal_type = "breakfast"
    provider.generate_recipes = lambda request, calls=iter([
        ProviderGenerationResult(
            candidates=[disliked, too_slow, wrong_meal], model="fake", prompt_version="v1", latency_ms=1
        ),
        ProviderGenerationResult(
            candidates=[_candidate("冬瓜鸡肉汤"), _candidate("西兰花鸡肉饭"), _candidate("菌菇鸡肉煲")],
            model="fake", prompt_version="v1", latency_ms=1
        ),
    ]): next(calls)
    client.app.state.ai_recipe_provider = provider

    response = client.post(
        "/api/v1/ai/recipe-recommendations",
        headers={**auth_headers, "Idempotency-Key": "hard-filter"},
        json={
            "filters": {
                "meal_type": "dinner",
                "max_minutes": 30,
                "disliked_ingredients": ["香菜"],
            },
            "query": "清淡晚餐",
        },
    )

    assert response.status_code == 201
    assert {item["title"] for item in response.json()["candidates"]} == {
        "平台南瓜粥", "平台蔬菜汤", "平台番茄饭"
    }


def test_inconsistent_nutrition_candidate_is_rejected_and_supplemented(client, auth_headers, settings):
    _create_pregnancy(client, auth_headers)
    _add_reviewed_recipes(client, ["平台南瓜粥", "平台蔬菜汤", "平台番茄饭"])
    settings.ai_max_retries = 1
    provider = InconsistentThenValidProvider()
    client.app.state.ai_recipe_provider = provider

    response = _recommend(client, auth_headers, "nutrition-retry")

    assert response.status_code == 201
    assert len(response.json()["candidates"]) == 3
    assert provider.calls == 1


def test_partial_safe_batch_uses_one_provider_call_and_reviewed_recipes_to_reach_three(
    client, auth_headers, settings
):
    _create_pregnancy(client, auth_headers)
    settings.ai_max_retries = 2
    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    session.add_all(
        [
            Recipe(id="reviewed-a", title="平台番茄汤", visibility="platform"),
            Recipe(id="reviewed-b", title="平台蔬菜粥", visibility="platform"),
        ]
    )
    session.commit()
    session.close()
    provider = PartialSafeProvider()
    client.app.state.ai_recipe_provider = provider

    response = _recommend(client, auth_headers, "partial-safe-batch")

    assert response.status_code == 201
    assert response.json()["mode"] == "ai"
    assert len(response.json()["candidates"]) == 3
    assert provider.calls == 1
    assert {item.get("source_type", "ai") for item in response.json()["candidates"]} == {
        "ai",
        "platform",
    }


def test_generation_prompt_excludes_existing_platform_recipe(client, auth_headers):
    _create_pregnancy(client, auth_headers)
    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    recipe = Recipe(id="existing-platform", title="番茄鸡丁", visibility="platform")
    recipe.items.append(RecipeItem(ingredient_name_zh="番茄鸡丁鸡胸肉", grams=120, position=0))
    session.add(recipe)
    session.commit()
    session.close()
    provider = FakeProvider(
        [
            ["番茄鸡丁", "冬瓜鸡肉汤", "西兰花鸡肉饭"],
            ["菌菇鸡肉煲"],
        ]
    )
    client.app.state.ai_recipe_provider = provider

    response = _recommend(client, auth_headers, "catalog-dedupe")

    assert response.status_code == 201
    assert len(response.json()["candidates"]) == 3
    ai_titles = {
        item["title"] for item in response.json()["candidates"] if item.get("candidate_id")
    }
    assert ai_titles == {"冬瓜鸡肉汤", "西兰花鸡肉饭"}
    assert len(provider.requests) == 1
    assert provider.requests[0].excluded_fingerprints


def test_stale_incomplete_idempotency_reservation_can_recover(client, auth_headers):
    _create_pregnancy(client, auth_headers)
    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    user = session.scalar(select(User))
    stale = AiRecommendationSession(
        user_id=user.id,
        filters={},
        query_text="",
        displayed_fingerprints=[],
        candidates=[],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    session.add(stale)
    session.flush()
    session.add(
        AiRecipeRequestEvent(
            session_id=stale.id,
            user_id=user.id,
            request_kind="initial",
            request_ip_hash="stale-ip",
            idempotency_key="stale-key",
            response_payload={},
            created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
    )
    session.commit()
    session.close()
    client.app.state.ai_recipe_provider = FakeProvider(
        [["番茄鸡丁", "冬瓜鸡肉汤", "西兰花鸡肉饭"]]
    )

    response = _recommend(client, auth_headers, "stale-key")

    assert response.status_code == 201
    assert response.json()["mode"] == "ai"


def test_expired_session_cannot_request_next_batch(client, auth_headers):
    _create_pregnancy(client, auth_headers)
    provider = FakeProvider([["番茄鸡丁", "冬瓜鸡肉汤", "西兰花鸡肉饭"]])
    client.app.state.ai_recipe_provider = provider
    created = _recommend(client, auth_headers, "expiry-initial").json()
    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    stored = session.get(AiRecommendationSession, created["session_id"])
    stored.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    session.commit()
    session.close()

    response = client.post(
        f"/api/v1/ai/recipe-recommendations/{created['session_id']}/next",
        headers={**auth_headers, "Idempotency-Key": "expiry-next"},
    )

    assert response.status_code == 404


def test_cleanup_deletes_only_expired_sessions_and_cascades_events(db_session):
    user = User()
    db_session.add(user)
    db_session.flush()
    expired = AiRecommendationSession(
        user_id=user.id,
        filters={},
        query_text="",
        displayed_fingerprints=[],
        candidates=[],
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    active = AiRecommendationSession(
        user_id=user.id,
        filters={},
        query_text="",
        displayed_fingerprints=[],
        candidates=[],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db_session.add_all([expired, active])
    db_session.flush()
    event = AiRecipeRequestEvent(
        session_id=expired.id,
        user_id=user.id,
        request_kind="initial",
        request_ip_hash="cleanup-ip",
        idempotency_key="cleanup-key",
        response_payload={},
    )
    db_session.add(event)
    db_session.commit()
    event_id = event.id

    assert purge_expired_sessions(db_session) == 1
    assert db_session.get(AiRecommendationSession, active.id) is not None
    assert db_session.scalar(
        select(AiRecipeRequestEvent).where(AiRecipeRequestEvent.id == event_id)
    ) is None
