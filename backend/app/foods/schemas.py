from decimal import Decimal

from pydantic import BaseModel, Field


class ImportReport(BaseModel):
    imported: int = 0
    updated: int = 0
    unchanged: int = 0


class FoodHit(BaseModel):
    id: str
    source_food_id: str
    name: str
    energy_kcal_100g: Decimal


class FoodDetail(FoodHit):
    provider: str
    source_url: str
    foodex2_code: str | None
    aliases_zh: list[str]
    household_measures: list[dict]
    protein_g_100g: Decimal
    fat_g_100g: Decimal
    carbohydrate_g_100g: Decimal
    fiber_g_100g: Decimal
    salt_g_100g: Decimal
    dataset_version: str


class FoodSearchResponse(BaseModel):
    items: list[FoodHit]
    catalog_ready: bool


class ImportRequest(BaseModel):
    path: str = Field(min_length=1)
    version: str = Field(min_length=1, max_length=128)
    dry_run: bool = True
