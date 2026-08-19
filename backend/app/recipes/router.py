from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.meals.schemas import MealEntryCreate
from app.meals.service import create_meal_entry
from app.recipes.models import Recipe
from app.recipes.schemas import RecipeRead, RecipeRecordRequest, RecipeRecordResponse


router = APIRouter(prefix="/api/v1/recipes", tags=["recipes"])


@router.get("", response_model=list[RecipeRead])
def list_recipes(
    _: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[Recipe]:
    return list(session.scalars(select(Recipe).options(selectinload(Recipe.items))).all())


@router.post("/{recipe_id}/record", response_model=RecipeRecordResponse)
def record_recipe(
    recipe_id: str,
    body: RecipeRecordRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=96),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> RecipeRecordResponse:
    recipe = session.scalar(
        select(Recipe).where(Recipe.id == recipe_id).options(selectinload(Recipe.items))
    )
    if recipe is None:
        raise HTTPException(status_code=404, detail="recipe not found")
    entries = []
    for index, item in enumerate(recipe.items):
        entry = create_meal_entry(
            session,
            current_user.id,
            MealEntryCreate(
                meal_date=body.meal_date,
                meal_type=body.meal_type,
                source_food_id=item.source_food_id,
                grams=item.grams,
            ),
            f"{idempotency_key}:{index}",
        )
        entries.append(entry.id)
    return RecipeRecordResponse(recipe_id=recipe.id, meal_entry_ids=entries)
