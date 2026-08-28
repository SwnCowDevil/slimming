from app.ai_recipes.schemas import CandidateNutrition, RecipeCandidate
from app.foods.tka_provider import TkaProvider
from sqlalchemy.orm import Session


def _validate_model_estimate(candidate: RecipeCandidate) -> None:
    nutrition = candidate.nutrition_per_serving
    macro_kcal = nutrition.protein_g * 4 + nutrition.carbohydrate_g * 4 + nutrition.fat_g * 9
    if macro_kcal > nutrition.energy_kcal * 1.35 + 50:
        raise ValueError("营养估算中的宏量营养素与热量不一致")


def enrich_candidate_nutrition(session: Session, candidate: RecipeCandidate) -> RecipeCandidate:
    _validate_model_estimate(candidate)
    enriched = candidate.model_copy(deep=True)
    provider = TkaProvider(session)
    matched = 0
    totals = {
        "energy_kcal": 0.0,
        "protein_g": 0.0,
        "fat_g": 0.0,
        "carbohydrate_g": 0.0,
        "fiber_g": 0.0,
    }

    for ingredient in enriched.ingredients:
        food = provider.match_exact(ingredient.name_zh)
        if food is not None:
            matched += 1
            ingredient.source_food_id = food.source_food_id
            ingredient.nutrition_source = "tka"
            ingredient.energy_kcal_per_100g = float(food.energy_kcal_100g)
            ingredient.protein_g_per_100g = float(food.protein_g_100g)
            ingredient.fat_g_per_100g = float(food.fat_g_100g)
            ingredient.carbohydrate_g_per_100g = float(food.carbohydrate_g_100g)
            ingredient.fiber_g_per_100g = float(food.fiber_g_100g)
        ratio = ingredient.grams / 100 / enriched.servings
        totals["energy_kcal"] += ingredient.energy_kcal_per_100g * ratio
        totals["protein_g"] += ingredient.protein_g_per_100g * ratio
        totals["fat_g"] += ingredient.fat_g_per_100g * ratio
        totals["carbohydrate_g"] += ingredient.carbohydrate_g_per_100g * ratio
        totals["fiber_g"] += ingredient.fiber_g_per_100g * ratio

    if matched == len(enriched.ingredients):
        enriched.nutrition_source = "tka"
        enriched.nutrition_confidence = "high"
    elif matched:
        enriched.nutrition_source = "mixed"
        enriched.nutrition_confidence = "medium"
    else:
        enriched.nutrition_source = "ai_estimated"
        enriched.nutrition_confidence = "low"

    enriched.nutrition_per_serving = CandidateNutrition(
        **{name: round(value, 2) for name, value in totals.items()}
    )
    return enriched
