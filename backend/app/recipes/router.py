from pathlib import Path
from secrets import compare_digest
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.meals.schemas import MealEntryCreate
from app.meals.service import create_estimated_meal_entry, create_meal_entry
from app.foods.tka_provider import TkaProvider
from app.foods.schemas import ImportReport, ImportRequest
from app.core.config import Settings, get_settings
from app.recipes.importer import PlatformRecipeImporter
from app.recipes.models import Recipe
from app.recipes.schemas import RecipeRead, RecipeRecordRequest, RecipeRecordResponse
from app.recipes.service import (
    favorite_recipe,
    get_visible_recipe,
    list_visible_recipes,
    remove_favorite,
)


router = APIRouter(prefix="/api/v1/recipes", tags=["recipes"])
admin_router = APIRouter(prefix="/api/v1/admin/recipes", tags=["recipe-admin"])


@admin_router.post("/import", response_model=ImportReport)
def import_platform_recipes(
    body: ImportRequest,
    admin_import_key: str = Header(default="", alias="X-Admin-Import-Key"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> ImportReport:
    if not settings.admin_import_key or not compare_digest(admin_import_key, settings.admin_import_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无食谱库管理权限")
    root = settings.tka_import_root.resolve()
    path = Path(body.path).resolve()
    if path != root and root not in path.parents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="导入文件不在允许目录")
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="导入文件不存在")
    return PlatformRecipeImporter(session).import_file(path, body.version, dry_run=body.dry_run)


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
    needs_confirmation = recipe.nutrition_source in {"mixed", "ai_estimated"}
    if needs_confirmation and not body.confirmed_items:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "action": "confirm_ingredients",
                "message": "请确认食材名称和重量后再记录",
            },
        )
    confirmed = {item.item_id: item for item in (body.confirmed_items or [])}
    if body.confirmed_items and (
        len(confirmed) != len(body.confirmed_items)
        or set(confirmed) != {item.id for item in recipe.items}
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"action": "confirm_ingredients", "message": "确认的食材与食谱不一致"},
        )
    entries = []
    tka = TkaProvider(session)
    try:
        for index, item in enumerate(recipe.items):
            confirmation = confirmed.get(item.id)
            grams = confirmation.grams if confirmation is not None else item.grams
            ingredient_name = (
                confirmation.ingredient_name_zh if confirmation is not None else item.ingredient_name_zh
            )
            matched_food = tka.match_exact(ingredient_name) if confirmation is not None else None
            source_food_id = matched_food.source_food_id if matched_food is not None else item.source_food_id
            if source_food_id is not None:
                entry = create_meal_entry(
                    session,
                    current_user.id,
                    MealEntryCreate(
                        meal_date=body.meal_date,
                        meal_type=body.meal_type,
                        source_food_id=source_food_id,
                        grams=grams,
                    ),
                    f"{idempotency_key}:{index}",
                    commit=False,
                )
                entry.source_recipe_id = recipe.id
            else:
                entry = create_estimated_meal_entry(
                    session,
                    current_user.id,
                    recipe,
                    item,
                    grams,
                    body.meal_date,
                    body.meal_type,
                    f"{idempotency_key}:{index}",
                    ingredient_name_zh=ingredient_name,
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
