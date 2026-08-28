from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RecipeItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_food_id: str | None
    ingredient_name_zh: str
    original_measure: str
    grams: Decimal
    nutrition_source: str


class RecipeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    steps: list[str]
    minutes: int
    tags: list[str]
    image_url: str | None
    content_status: str
    content_version: str
    pregnancy_safety: str
    safety_summary: str
    allergen_codes: list[str]
    subtitle: str | None
    energy_kcal: Decimal | None
    protein_g: Decimal | None
    fat_g: Decimal | None
    carbohydrate_g: Decimal | None
    fiber_g: Decimal | None
    items: list[RecipeItemRead]
    source_type: str
    visibility: str
    nutrition_source: str
    nutrition_confidence: str
    is_favorite: bool = False


class ConfirmedRecipeItem(BaseModel):
    item_id: str = Field(min_length=1, max_length=36)
    ingredient_name_zh: str = Field(min_length=1, max_length=120)
    grams: Decimal = Field(gt=0, le=5000)


class RecipeRecordRequest(BaseModel):
    meal_date: date
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    confirmed_items: list[ConfirmedRecipeItem] | None = None


class RecipeRecordResponse(BaseModel):
    recipe_id: str
    meal_entry_ids: list[str]
