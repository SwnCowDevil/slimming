from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AiContext(BaseModel):
    pregnancy: bool = False
    eating_disorder_risk: bool = False
    serious_symptoms: bool = False
    medication_or_disease: bool = False


class SafetyResult(BaseModel):
    action: Literal["allow", "allow_limited", "refer_professional", "emergency_guidance"]
    reason: str | None = None


class AiDraftCreate(BaseModel):
    kind: Literal["meal_candidate", "today_tip", "weekly_explanation"]
    meal_date: date | None = None
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] | None = None
    source_food_id: str | None = None
    grams: Decimal | None = Field(default=None, gt=0, le=5000)
    context: AiContext = Field(default_factory=AiContext)
    input_data_range: dict = Field(default_factory=dict)


class AiDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str
    status: str
    candidate: dict
    model_name: str
    prompt_version: str
    safety_action: str
    policy_version: str
    response_text: str | None
    meal_entry_id: str | None


class PregnancyAiRequest(BaseModel):
    context: AiContext = Field(default_factory=lambda: AiContext(pregnancy=True))
    period: Literal[7, 30, 90] = 7
    current_recipe_id: str | None = None


class ReflectionGenerationResult(BaseModel):
    response_text: str = Field(min_length=1, max_length=500)
    model: str = Field(min_length=1, max_length=128)
    prompt_version: str = Field(min_length=1, max_length=64)


class ReflectionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    focus_fact_indexes: list[int] = Field(default_factory=list, max_length=2)
    next_step: Literal[
        "keep_recording",
        "complete_meal_context",
        "diversify_food_categories",
    ]
