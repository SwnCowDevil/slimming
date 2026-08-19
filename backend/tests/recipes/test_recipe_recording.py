from pathlib import Path

from app.db.session import get_session
from app.recipes.models import Recipe, RecipeItem


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
