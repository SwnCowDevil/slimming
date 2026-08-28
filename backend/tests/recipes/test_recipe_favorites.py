from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.ai_recipes.models import AiRecommendationSession, AiRecipeRequestEvent
from app.auth.models import User, WechatIdentity
from app.db.session import get_session
from app.recipes.models import Recipe, RecipeFavorite, RecipeItem


def test_recipe_models_support_private_favorites_and_request_events(db_session):
    user = User()
    db_session.add(user)
    db_session.flush()

    recipe = Recipe(
        title="番茄鸡蛋汤",
        source_type="ai",
        visibility="private",
        owner_user_id=user.id,
        content_fingerprint="fp-owner-recipe",
        nutrition_source="mixed",
        nutrition_confidence="medium",
        prompt_version="recipe-v1",
        safety_rule_version="pregnancy-recipe-v1",
    )
    recipe.items.append(
        RecipeItem(
            ingredient_name_zh="番茄",
            original_measure="1个",
            grams=180,
            source_food_id=None,
            nutrition_source="ai_estimated",
            estimated_energy_kcal_per_100g=18,
        )
    )
    recipe.favorites.append(RecipeFavorite(user_id=user.id))

    recommendation_session = AiRecommendationSession(
        user_id=user.id,
        filters={"meal_type": "dinner"},
        query_text="清淡晚餐",
        displayed_fingerprints=[],
        candidates=[],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add_all([recipe, recommendation_session])
    db_session.flush()
    request_event = AiRecipeRequestEvent(
        session_id=recommendation_session.id,
        user_id=user.id,
        request_kind="initial",
        request_ip_hash="ip-hash",
        idempotency_key="initial-request",
        response_payload={"mode": "ai", "candidates": []},
        provider_call_count=1,
    )
    db_session.add(request_event)
    db_session.commit()

    assert recipe.owner_user_id == user.id
    assert recipe.items[0].source_food_id is None
    assert recipe.items[0].estimated_energy_kcal_per_100g == 18
    assert recipe.favorites[0].user_id == user.id
    assert request_event.session_id == recommendation_session.id


def _database_session(client):
    session_iterator = client.app.dependency_overrides[get_session]()
    return next(session_iterator)


def _current_user_id(client) -> str:
    session = _database_session(client)
    try:
        return session.scalar(select(WechatIdentity.user_id).where(WechatIdentity.openid == "openid-123"))
    finally:
        session.close()


def test_search_returns_platform_and_current_users_private_recipe_only(client, auth_headers):
    current_user_id = _current_user_id(client)
    session = _database_session(client)
    other_user = User()
    session.add(other_user)
    session.flush()
    session.add_all(
        [
            Recipe(id="platform-tomato", title="平台番茄汤", source_type="platform", visibility="platform"),
            Recipe(
                id="my-tomato",
                title="我的鸡蛋面",
                source_type="ai",
                visibility="private",
                owner_user_id=current_user_id,
                original_query="想吃番茄面",
            ),
            Recipe(
                id="other-tomato",
                title="别人的番茄面",
                source_type="ai",
                visibility="private",
                owner_user_id=other_user.id,
            ),
        ]
    )
    session.commit()
    session.close()

    response = client.get("/api/v1/recipes?query=番茄&scope=all", headers=auth_headers)

    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == {"platform-tomato", "my-tomato"}


def test_platform_favorite_can_be_added_listed_and_removed(client, auth_headers):
    session = _database_session(client)
    session.add(Recipe(id="platform-favorite", title="平台食谱", source_type="platform", visibility="platform"))
    session.commit()
    session.close()

    saved = client.post("/api/v1/recipes/platform-favorite/favorite", headers=auth_headers)
    listed = client.get("/api/v1/recipes?scope=favorites", headers=auth_headers)
    removed = client.delete("/api/v1/recipes/platform-favorite/favorite", headers=auth_headers)

    assert saved.status_code == 200
    assert saved.json()["is_favorite"] is True
    assert [item["id"] for item in listed.json()] == ["platform-favorite"]
    assert removed.status_code == 204


def test_other_users_private_recipe_is_not_addressable(client, auth_headers):
    session = _database_session(client)
    other_user = User()
    session.add(other_user)
    session.flush()
    session.add(
        Recipe(
            id="other-private",
            title="他人的私人食谱",
            source_type="ai",
            visibility="private",
            owner_user_id=other_user.id,
        )
    )
    session.commit()
    session.close()

    own_session = _database_session(client)
    own_session.add(
        Recipe(
            id="my-private-detail",
            title="我的私人食谱",
            source_type="ai",
            visibility="private",
            owner_user_id=_current_user_id(client),
        )
    )
    own_session.commit()
    own_session.close()

    assert client.get("/api/v1/recipes/my-private-detail", headers=auth_headers).status_code == 200
    assert client.get("/api/v1/recipes/other-private", headers=auth_headers).status_code == 404
    assert client.post("/api/v1/recipes/other-private/favorite", headers=auth_headers).status_code == 404
    assert client.post(
        "/api/v1/recipes/other-private/record",
        headers={**auth_headers, "Idempotency-Key": "forbidden-private"},
        json={"meal_date": "2026-08-28", "meal_type": "dinner"},
    ).status_code == 404
