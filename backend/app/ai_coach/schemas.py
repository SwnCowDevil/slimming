from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AiContext(BaseModel):
    pregnancy: bool = False
    eating_disorder_risk: bool = False
    serious_symptoms: bool = False


class SafetyResult(BaseModel):
    action: Literal["allow", "refer_professional"]
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
    meal_entry_id: str | None
