from pathlib import Path

from sqlalchemy import select

from app.auth.models import WechatIdentity
from app.db.session import get_session
from app.meals.models import MealEntry
from app.recipes.models import Recipe, RecipeFavorite, RecipeItem


def _database_session(client):
    return next(client.app.dependency_overrides[get_session]())


def _current_user_id(client) -> str:
    session = _database_session(client)
    try:
        return session.scalar(select(WechatIdentity.user_id).where(WechatIdentity.openid == "openid-123"))
    finally:
        session.close()


def test_recipe_one_click_recording_is_idempotent(client, auth_headers):
    fixture = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"
    client.post(
        "/api/v1/admin/foods/import",
        headers=auth_headers,
        json={"path": str(fixture), "version": "fixture-2026-08", "dry_run": False},
    )
    recipe = Recipe(id="recipe-1", title="Quick bowl", minutes=12, tags=["high-protein"])
    recipe.items.append(RecipeItem(source_food_id="8535", grams=150))
    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    session.add(recipe)
    session.commit()
    session.close()

    payload = {"meal_date": "2026-08-19", "meal_type": "lunch"}
    first = client.post(
        "/api/v1/recipes/recipe-1/record",
        headers={**auth_headers, "Idempotency-Key": "recipe-record"},
        json=payload,
    )
    second = client.post(
        "/api/v1/recipes/recipe-1/record",
        headers={**auth_headers, "Idempotency-Key": "recipe-record"},
        json=payload,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["meal_entry_ids"] == second.json()["meal_entry_ids"]
    assert len(client.get("/api/v1/meals?date=2026-08-19", headers=auth_headers).json()["items"]) == 1


def test_recipe_recording_rolls_back_all_items_when_one_food_is_missing(client, auth_headers):
    fixture = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"
    client.post(
        "/api/v1/admin/foods/import",
        headers=auth_headers,
        json={"path": str(fixture), "version": "fixture-2026-08", "dry_run": False},
    )
    recipe = Recipe(id="recipe-atomic", title="Atomic bowl", minutes=12, tags=[])
    recipe.items.extend([
        RecipeItem(source_food_id="8535", grams=100),
        RecipeItem(source_food_id="missing-food", grams=100),
    ])
    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    session.add(recipe)
    session.commit()
    session.close()

    response = client.post(
        "/api/v1/recipes/recipe-atomic/record",
        headers={**auth_headers, "Idempotency-Key": "atomic-record"},
        json={"meal_date": "2026-08-19", "meal_type": "lunch"},
    )

    assert response.status_code == 404
    assert client.get("/api/v1/meals?date=2026-08-19", headers=auth_headers).json()["items"] == []


def _seed_estimated_private_recipe(client) -> tuple[str, str]:
    user_id = _current_user_id(client)
    session = _database_session(client)
    recipe = Recipe(
        id="private-estimated",
        title="AI 南瓜鸡肉饭",
        source_type="ai",
        visibility="private",
        owner_user_id=user_id,
        nutrition_source="ai_estimated",
        nutrition_confidence="low",
        prompt_version="test-prompt-v1",
        content_fingerprint="private-estimated-fp",
    )
    item = RecipeItem(
        ingredient_name_zh="南瓜鸡肉混合食材",
        original_measure="1份",
        grams=180,
        nutrition_source="ai_estimated",
        estimated_energy_kcal_per_100g=120,
        estimated_protein_g_per_100g=12,
        estimated_fat_g_per_100g=3,
        estimated_carbohydrate_g_per_100g=15,
        estimated_fiber_g_per_100g=2,
    )
    recipe.items.append(item)
    recipe.favorites.append(RecipeFavorite(user_id=user_id))
    session.add(recipe)
    session.commit()
    recipe_id = recipe.id
    item_id = item.id
    session.close()
    return recipe_id, item_id


def test_estimated_recipe_requires_confirmed_items_before_recording(client, auth_headers):
    recipe_id, _ = _seed_estimated_private_recipe(client)

    response = client.post(
        f"/api/v1/recipes/{recipe_id}/record",
        headers={**auth_headers, "Idempotency-Key": "estimated-unconfirmed"},
        json={"meal_date": "2026-08-28", "meal_type": "dinner"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["action"] == "confirm_ingredients"


def test_confirmed_estimated_recipe_records_immutable_snapshot(client, auth_headers):
    recipe_id, item_id = _seed_estimated_private_recipe(client)

    response = client.post(
        f"/api/v1/recipes/{recipe_id}/record",
        headers={**auth_headers, "Idempotency-Key": "estimated-confirmed"},
        json={
            "meal_date": "2026-08-28",
            "meal_type": "dinner",
            "confirmed_items": [{
                "item_id": item_id,
                "ingredient_name_zh": "南瓜鸡肉混合食材",
                "grams": 200,
            }],
        },
    )

    assert response.status_code == 200
    session = _database_session(client)
    entry = session.get(MealEntry, response.json()["meal_entry_ids"][0])
    assert entry.food_id is None
    assert entry.source_recipe_id == recipe_id
    assert entry.provider == "ai_estimated"
    assert entry.nutrition_source == "ai_estimated"
    assert float(entry.energy_kcal) == 240
    session.close()


def test_unfavorite_private_recipe_archives_it_and_preserves_meal_history(client, auth_headers):
    recipe_id, item_id = _seed_estimated_private_recipe(client)
    recorded = client.post(
        f"/api/v1/recipes/{recipe_id}/record",
        headers={**auth_headers, "Idempotency-Key": "archive-history"},
        json={
            "meal_date": "2026-08-28",
            "meal_type": "dinner",
            "confirmed_items": [{
                "item_id": item_id,
                "ingredient_name_zh": "南瓜鸡肉混合食材",
                "grams": 180,
            }],
        },
    )

    removed = client.delete(f"/api/v1/recipes/{recipe_id}/favorite", headers=auth_headers)

    assert recorded.status_code == 200
    assert removed.status_code == 204
    session = _database_session(client)
    assert session.get(Recipe, recipe_id).content_status == "archived"
    assert session.get(MealEntry, recorded.json()["meal_entry_ids"][0]) is not None
    session.close()
