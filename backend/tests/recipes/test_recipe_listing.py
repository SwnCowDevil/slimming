from datetime import date, timedelta
from pathlib import Path

from app.db.session import get_session
from app.recipes.models import Recipe, RecipeItem


FIXTURE = Path(__file__).parents[1] / "foods" / "fixtures" / "tka_sample.json"


def seed_recipes(client, headers):
    client.post(
        "/api/v1/admin/foods/import",
        headers=headers,
        json={"path": str(FIXTURE), "version": "fixture-recipes", "dry_run": False},
    )
    session_iterator = client.app.dependency_overrides[get_session]()
    session = next(session_iterator)
    safe = Recipe(
        id="safe-quick",
        title="安全快手餐",
        description="适合日常搭配",
        minutes=12,
        tags=["high-protein", "quick"],
        content_status="published",
        content_version="review-2",
        pregnancy_safety="safe",
        safety_summary="食材信息已复核",
        allergen_codes=[],
        subtitle="12 分钟 · 食材已复核",
    )
    safe.items.append(RecipeItem(source_food_id="8535", grams=100))
    allergen = Recipe(
        id="peanut-recipe",
        title="含花生餐",
        minutes=10,
        tags=["quick"],
        content_status="published",
        pregnancy_safety="safe",
        safety_summary="含花生",
        allergen_codes=["peanut"],
    )
    allergen.items.append(RecipeItem(source_food_id="8535", grams=50))
    draft = Recipe(
        id="draft-recipe",
        title="未发布餐",
        minutes=8,
        tags=["high-protein"],
        content_status="draft",
    )
    draft.items.append(RecipeItem(source_food_id="8535", grams=100))
    session.add_all([safe, allergen, draft])
    session.commit()
    session.close()


def test_recipe_listing_is_reviewed_filtered_and_nutrition_snapshotted(
    client, auth_headers
):
    client.post(
        "/api/v1/pregnancies",
        headers=auth_headers,
        json={
            "due_date": (date.today() + timedelta(days=120)).isoformat(),
            "height_cm": 165,
            "current_weight_kg": 61,
            "activity_level": "light",
            "allergens": ["peanut"],
        },
    )
    seed_recipes(client, auth_headers)

    response = client.get(
        "/api/v1/recipes?max_minutes=15&high_protein=true&limit=10&offset=0",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == ["safe-quick"]
    item = response.json()[0]
    assert item["energy_kcal"] == "162.00"
    assert item["protein_g"] == "0.20"
    assert item["subtitle"] == "12 分钟 · 食材已复核"
    assert item["safety_summary"] == "食材信息已复核"
    assert item["content_version"] == "review-2"


def test_recipe_listing_pagination_is_stable(client, auth_headers):
    seed_recipes(client, auth_headers)

    first = client.get("/api/v1/recipes?limit=1&offset=0", headers=auth_headers).json()
    second = client.get("/api/v1/recipes?limit=1&offset=1", headers=auth_headers).json()

    assert [item["id"] for item in first] == ["peanut-recipe"]
    assert [item["id"] for item in second] == ["safe-quick"]
