from decimal import Decimal

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.foods.models import Food
from app.pregnancies.service import get_active_episode
from app.recipes.models import Recipe, RecipeFavorite


ZERO = Decimal("0")


def refresh_nutrition_snapshot(session: Session, recipe: Recipe) -> None:
    if recipe.nutrition_source != "tka":
        return
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


def visible_recipe_clause(user_id: str):
    return and_(
        Recipe.content_status == "published",
        or_(
            Recipe.visibility == "platform",
            and_(Recipe.visibility == "private", Recipe.owner_user_id == user_id),
        ),
    )


def _matches_query(recipe: Recipe, query: str) -> bool:
    needle = query.strip().casefold()
    if not needle:
        return True
    values = [
        recipe.title,
        recipe.description,
        recipe.original_query or "",
        " ".join(recipe.tags or []),
        " ".join(item.ingredient_name_zh for item in recipe.items),
    ]
    return any(needle in value.casefold() for value in values)


def list_visible_recipes(
    session: Session,
    user_id: str,
    query: str | None = None,
    scope: str = "all",
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
                visible_recipe_clause(user_id),
                Recipe.pregnancy_safety != "avoid",
            )
            .options(selectinload(Recipe.items), selectinload(Recipe.favorites))
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
        favorite = next((item for item in recipe.favorites if item.user_id == user_id), None)
        recipe.is_favorite = favorite is not None
        if scope == "platform" and recipe.visibility != "platform":
            continue
        if scope == "favorites" and favorite is None:
            continue
        if query is not None and not _matches_query(recipe, query):
            continue
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


def list_reviewed_recipes(
    session: Session,
    user_id: str,
    max_minutes: int | None = None,
    tag: str | None = None,
    high_protein: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> list[Recipe]:
    return list_visible_recipes(
        session,
        user_id,
        max_minutes=max_minutes,
        tag=tag,
        high_protein=high_protein,
        limit=limit,
        offset=offset,
    )


def get_visible_recipe(session: Session, user_id: str, recipe_id: str) -> Recipe | None:
    recipe = session.scalar(
        select(Recipe)
        .where(Recipe.id == recipe_id, visible_recipe_clause(user_id))
        .options(selectinload(Recipe.items), selectinload(Recipe.favorites))
    )
    if recipe is not None:
        recipe.is_favorite = any(item.user_id == user_id for item in recipe.favorites)
        refresh_nutrition_snapshot(session, recipe)
    return recipe


def favorite_recipe(session: Session, user_id: str, recipe_id: str) -> Recipe | None:
    recipe = get_visible_recipe(session, user_id, recipe_id)
    if recipe is None:
        return None
    if not recipe.is_favorite:
        session.add(RecipeFavorite(user_id=user_id, recipe_id=recipe.id))
        session.commit()
    recipe.is_favorite = True
    return recipe


def remove_favorite(session: Session, user_id: str, recipe_id: str) -> bool:
    recipe = get_visible_recipe(session, user_id, recipe_id)
    if recipe is None:
        return False
    favorite = session.scalar(
        select(RecipeFavorite).where(
            RecipeFavorite.user_id == user_id,
            RecipeFavorite.recipe_id == recipe_id,
        )
    )
    if favorite is not None:
        session.delete(favorite)
    if recipe.visibility == "private" and recipe.owner_user_id == user_id:
        recipe.content_status = "archived"
    session.commit()
    return True
