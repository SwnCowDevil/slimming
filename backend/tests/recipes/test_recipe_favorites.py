from datetime import datetime, timedelta, timezone

from app.ai_recipes.models import AiRecommendationSession, AiRecipeRequestEvent
from app.auth.models import User
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
