from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


ActivityLevel = Literal["sedentary", "light", "moderate", "active"]


class PregnancyCreate(BaseModel):
    due_date: date
    due_date_source: Literal["user_entered", "clinician_adjusted"] = "user_entered"
    height_cm: Decimal = Field(ge=120, le=230)
    pre_pregnancy_weight_kg: Decimal | None = Field(default=None, ge=30, le=300)
    current_weight_kg: Decimal = Field(ge=30, le=300)
    activity_level: ActivityLevel
    dietary_preferences: list[str] = Field(default_factory=list, max_length=20)
    allergens: list[str] = Field(default_factory=list, max_length=20)
    avoidances: list[str] = Field(default_factory=list, max_length=20)
    disliked_foods: list[str] = Field(default_factory=list, max_length=20)
    timezone: str = Field(default="Asia/Shanghai", min_length=1, max_length=64)

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: date) -> date:
        delta = (value - date.today()).days
        if delta < -14 or delta > 294:
            raise ValueError("预产期不在可支持的孕期范围内")
        return value


class PregnancyUpdate(BaseModel):
    due_date: date | None = None
    due_date_source: Literal["user_entered", "clinician_adjusted"] | None = None
    height_cm: Decimal | None = Field(default=None, ge=120, le=230)
    pre_pregnancy_weight_kg: Decimal | None = Field(default=None, ge=30, le=300)
    current_weight_kg: Decimal | None = Field(default=None, ge=30, le=300)
    activity_level: ActivityLevel | None = None
    dietary_preferences: list[str] | None = Field(default=None, max_length=20)
    allergens: list[str] | None = Field(default=None, max_length=20)
    avoidances: list[str] | None = Field(default=None, max_length=20)
    disliked_foods: list[str] | None = Field(default=None, max_length=20)

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: date | None) -> date | None:
        if value is None:
            return value
        delta = (value - date.today()).days
        if delta < -14 or delta > 294:
            raise ValueError("预产期不在可支持的孕期范围内")
        return value


class GestationRead(BaseModel):
    week: int
    day: int
    total_days: int


class PregnancyPreferenceRead(BaseModel):
    height_cm: float
    pre_pregnancy_weight_kg: float | None
    current_weight_kg: float | None
    activity_level: str
    dietary_preferences: list[str]
    allergens: list[str]
    avoidances: list[str]
    disliked_foods: list[str]


class PregnancyRead(BaseModel):
    id: str
    user_id: str
    due_date: date
    due_date_source: str
    status: str
    timezone: str
    started_at: datetime
    ended_at: datetime | None
    product_mode: str
    gestation: GestationRead
    preferences: PregnancyPreferenceRead
