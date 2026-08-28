from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.meals.schemas import MealEntryCreate
from app.meals.service import create_meal_entry
from app.recipes.models import Recipe
from app.recipes.schemas import RecipeRead, RecipeRecordRequest, RecipeRecordResponse
from app.recipes.service import (
    favorite_recipe,
    get_visible_recipe,
    list_visible_recipes,
    remove_favorite,
)


router = APIRouter(prefix="/api/v1/recipes", tags=["recipes"])


@router.get("", response_model=list[RecipeRead])
def list_recipes(
    query: str | None = Query(default=None, max_length=80),
    scope: Literal["all", "platform", "favorites"] = Query(default="all"),
    max_minutes: int | None = Query(default=None, ge=1, le=240),
    tag: str | None = Query(default=None, min_length=1, max_length=40),
    high_protein: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[Recipe]:
    return list_visible_recipes(
        session,
        current_user.id,
        query=query,
        scope=scope,
        max_minutes=max_minutes,
        tag=tag,
        high_protein=high_protein,
        limit=limit,
        offset=offset,
    )


@router.get("/{recipe_id}", response_model=RecipeRead)
def get_recipe(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Recipe:
    recipe = get_visible_recipe(session, current_user.id, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="recipe not found")
    return recipe


@router.post("/{recipe_id}/favorite", response_model=RecipeRead)
def add_recipe_favorite(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Recipe:
    recipe = favorite_recipe(session, current_user.id, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="recipe not found")
    return recipe


@router.delete("/{recipe_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe_favorite(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
    if not remove_favorite(session, current_user.id, recipe_id):
        raise HTTPException(status_code=404, detail="recipe not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{recipe_id}/record", response_model=RecipeRecordResponse)
def record_recipe(
    recipe_id: str,
    body: RecipeRecordRequest,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=96),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> RecipeRecordResponse:
    recipe = get_visible_recipe(session, current_user.id, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="recipe not found")
    entries = []
    try:
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
                commit=False,
            )
            entries.append(entry)
        session.commit()
    except Exception:
        session.rollback()
        raise
    for entry in entries:
        session.refresh(entry)
    return RecipeRecordResponse(recipe_id=recipe.id, meal_entry_ids=[entry.id for entry in entries])
