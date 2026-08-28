from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.foods.models import Food
from app.pregnancies.service import get_active_episode
from app.recipes.models import Recipe


ZERO = Decimal("0")


def refresh_nutrition_snapshot(session: Session, recipe: Recipe) -> None:
    totals = {
        "energy_kcal": ZERO,
        "protein_g": ZERO,
        "fat_g": ZERO,
        "carbohydrate_g": ZERO,
        "fiber_g": ZERO,
    }
    for item in recipe.items:
        food = session.scalar(
            select(Food).where(
                Food.provider == "tka",
                Food.source_food_id == item.source_food_id,
            )
        )
        if food is None:
            continue
        ratio = item.grams / Decimal("100")
        totals["energy_kcal"] += food.energy_kcal_100g * ratio
        totals["protein_g"] += food.protein_g_100g * ratio
        totals["fat_g"] += food.fat_g_100g * ratio
        totals["carbohydrate_g"] += food.carbohydrate_g_100g * ratio
        totals["fiber_g"] += food.fiber_g_100g * ratio
    for field, value in totals.items():
        setattr(recipe, field, value.quantize(Decimal("0.01")))


def list_reviewed_recipes(
    session: Session,
    user_id: str,
    max_minutes: int | None = None,
    tag: str | None = None,
    high_protein: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> list[Recipe]:
    recipes = list(
        session.scalars(
            select(Recipe)
            .where(
                Recipe.content_status == "published",
                Recipe.pregnancy_safety != "avoid",
            )
            .options(selectinload(Recipe.items))
            .order_by(Recipe.title, Recipe.id)
        ).all()
    )
    episode = get_active_episode(session, user_id)
    user_allergens = (
        set(episode.preferences.allergens)
        if episode is not None and episode.preferences is not None
        else set()
    )
    filtered = []
    for recipe in recipes:
        if user_allergens.intersection(recipe.allergen_codes or []):
            continue
        if max_minutes is not None and recipe.minutes > max_minutes:
            continue
        if tag is not None and tag not in (recipe.tags or []):
            continue
        if high_protein and "high-protein" not in (recipe.tags or []):
            continue
        refresh_nutrition_snapshot(session, recipe)
        filtered.append(recipe)
    session.commit()
    return filtered[offset : offset + limit]
