import pytest

from app.ai_recipes.nutrition import enrich_candidate_nutrition
from app.ai_recipes.schemas import RecipeCandidate
from app.foods.models import Food, FoodAlias
from app.foods.tka_provider import TkaProvider


def _seed_tomato(db_session):
    food = Food(
        provider="tka",
        source_food_id="tomato-1",
        source_url="https://tka.nutridata.ee/example/tomato-1",
        name_en="Tomato",
        name_et="Tomat",
        synonyms=["garden tomato"],
        energy_kcal_100g=18,
        protein_g_100g=0.9,
        fat_g_100g=0.2,
        carbohydrate_g_100g=3.9,
        fiber_g_100g=1.2,
        salt_g_100g=0,
        dataset_version="test-tka",
        raw_sha256="tomato-hash",
    )
    food.aliases.append(FoodAlias(locale="zh-CN", name="番茄"))
    db_session.add(food)
    db_session.commit()
    return food


def _candidate(include_unknown: bool = False) -> RecipeCandidate:
    ingredients = [
        {
            "name_zh": "番茄",
            "quantity": 200,
            "unit": "克",
            "grams": 200,
            "energy_kcal_per_100g": 99,
            "protein_g_per_100g": 9,
            "fat_g_per_100g": 9,
            "carbohydrate_g_per_100g": 9,
            "fiber_g_per_100g": 9,
        }
    ]
    if include_unknown:
        ingredients.append(
            {
                "name_zh": "自制谷物粒",
                "quantity": 100,
                "unit": "克",
                "grams": 100,
                "energy_kcal_per_100g": 100,
                "protein_g_per_100g": 5,
                "fat_g_per_100g": 2,
                "carbohydrate_g_per_100g": 18,
                "fiber_g_per_100g": 3,
            }
        )
    return RecipeCandidate.model_validate(
        {
            "title": "番茄谷物碗",
            "summary": "家常主食",
            "meal_type": "lunch",
            "tags": ["home-style"],
            "servings": 2,
            "minutes": 20,
            "ingredients": ingredients,
            "steps": ["所有食材彻底加热。"],
            "allergens": [],
            "nutrition_per_serving": {
                "energy_kcal": 500,
                "protein_g": 20,
                "fat_g": 15,
                "carbohydrate_g": 60,
                "fiber_g": 10,
            },
            "recommendation_reason": "简单易做",
            "cooking_requirements": [],
        }
    )


def test_exact_tka_match_replaces_ai_estimate_and_marks_high_confidence(db_session):
    _seed_tomato(db_session)

    enriched = enrich_candidate_nutrition(db_session, _candidate())

    assert enriched.nutrition_source == "tka"
    assert enriched.nutrition_confidence == "high"
    assert enriched.ingredients[0].source_food_id == "tomato-1"
    assert enriched.ingredients[0].energy_kcal_per_100g == 18
    assert enriched.nutrition_per_serving.energy_kcal == 18


def test_partial_match_preserves_estimate_only_for_unmatched_item(db_session):
    _seed_tomato(db_session)

    enriched = enrich_candidate_nutrition(db_session, _candidate(include_unknown=True))

    assert enriched.nutrition_source == "mixed"
    assert enriched.nutrition_confidence == "medium"
    assert {item.nutrition_source for item in enriched.ingredients} == {"tka", "ai_estimated"}
    assert enriched.nutrition_per_serving.energy_kcal == 68


def test_tka_matching_does_not_use_broad_substrings(db_session):
    _seed_tomato(db_session)

    assert TkaProvider(db_session).match_exact("番茄酱") is None


def test_implausible_macro_energy_is_rejected(db_session):
    candidate = _candidate(include_unknown=True)
    candidate.nutrition_per_serving.energy_kcal = 50
    candidate.nutrition_per_serving.protein_g = 100

    with pytest.raises(ValueError, match="营养估算"):
        enrich_candidate_nutrition(db_session, candidate)
