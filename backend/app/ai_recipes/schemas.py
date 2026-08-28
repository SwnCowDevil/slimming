from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RecipeRecommendationFilters(StrictModel):
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] | None = None
    max_minutes: Literal[15, 30, 60] | None = None
    flavors: list[Literal["light", "sweet-sour", "mild-spicy", "home-style"]] = Field(
        default_factory=list, max_length=4
    )
    recipe_types: list[Literal["high-protein", "vegetarian", "soup", "staple"]] = Field(
        default_factory=list, max_length=4
    )
    available_ingredients: list[str] = Field(default_factory=list, max_length=20)
    disliked_ingredients: list[str] = Field(default_factory=list, max_length=20)


class RecipeGenerationRequest(StrictModel):
    pregnancy_stage: Literal["first_trimester", "second_trimester", "third_trimester"]
    allergens: list[str] = Field(default_factory=list, max_length=20)
    avoidances: list[str] = Field(default_factory=list, max_length=20)
    filters: RecipeRecommendationFilters = Field(default_factory=RecipeRecommendationFilters)
    query: str = Field(default="", max_length=300)
    excluded_fingerprints: list[str] = Field(default_factory=list, max_length=100)


class CandidateIngredient(StrictModel):
    name_zh: str = Field(min_length=1, max_length=40)
    quantity: float = Field(gt=0, le=5000)
    unit: str = Field(min_length=1, max_length=16)
    grams: float = Field(gt=0, le=5000)
    energy_kcal_per_100g: float = Field(ge=0, le=1000)
    protein_g_per_100g: float = Field(ge=0, le=100)
    fat_g_per_100g: float = Field(ge=0, le=100)
    carbohydrate_g_per_100g: float = Field(ge=0, le=100)
    fiber_g_per_100g: float = Field(ge=0, le=100)
    source_food_id: str | None = None
    nutrition_source: Literal["tka", "ai_estimated"] = "ai_estimated"


class CandidateNutrition(StrictModel):
    energy_kcal: float = Field(ge=0, le=2500)
    protein_g: float = Field(ge=0, le=300)
    fat_g: float = Field(ge=0, le=300)
    carbohydrate_g: float = Field(ge=0, le=500)
    fiber_g: float = Field(ge=0, le=100)


class RecipeCandidate(StrictModel):
    candidate_id: str | None = None
    title: str = Field(min_length=1, max_length=80)
    summary: str = Field(min_length=1, max_length=240)
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    tags: list[str] = Field(default_factory=list, max_length=8)
    servings: int = Field(ge=1, le=2)
    minutes: int = Field(ge=1, le=120)
    ingredients: list[CandidateIngredient] = Field(min_length=1, max_length=30)
    steps: list[str] = Field(min_length=1, max_length=20)
    allergens: list[str] = Field(default_factory=list, max_length=20)
    nutrition_per_serving: CandidateNutrition
    recommendation_reason: str = Field(min_length=1, max_length=240)
    cooking_requirements: list[str] = Field(default_factory=list, max_length=10)
    nutrition_source: Literal["tka", "mixed", "ai_estimated"] = "ai_estimated"
    nutrition_confidence: Literal["high", "medium", "low"] = "low"
    content_fingerprint: str | None = None


class ProviderUsage(StrictModel):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)


class ProviderGenerationResult(StrictModel):
    candidates: list[RecipeCandidate]
    model: str
    prompt_version: str
    latency_ms: int = Field(ge=0)
    usage: ProviderUsage = Field(default_factory=ProviderUsage)


class ProviderRecipeEnvelope(StrictModel):
    recipes: list[RecipeCandidate] = Field(min_length=1, max_length=8)
