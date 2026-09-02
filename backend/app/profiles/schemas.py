from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Goal = Literal["lose", "maintain", "improve"]
Sex = Literal["female", "male"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active"]


class BodyProfileInput(BaseModel):
    goal: Goal
    sex: Sex
    age: int = Field(ge=18, le=100)
    height_cm: Decimal = Field(ge=120, le=230)
    current_weight_kg: Decimal = Field(ge=30, le=300)
    target_weight_kg: Decimal = Field(ge=30, le=300)
    activity_level: ActivityLevel
    dietary_preferences: list[str] = Field(default_factory=list, max_length=20)
    allergens: list[str] = Field(default_factory=list, max_length=20)
    eating_out_frequency: Literal["rarely", "sometimes", "often"]

    @model_validator(mode="after")
    def validate_target_direction(self) -> "BodyProfileInput":
        if self.goal == "lose" and self.target_weight_kg >= self.current_weight_kg:
            raise ValueError("减重目标体重必须低于当前体重")
        return self


class NutritionTargets(BaseModel):
    bmi: Decimal
    bmr: Decimal
    minimum_kcal: int
    maximum_kcal: int
    daily_kcal: int
    protein_g: int
    carbohydrate_g: int
    fat_g: int


class ProfileRead(BaseModel):
    id: str
    user_id: str
    goal: str
    sex: str
    age: int
    height_cm: float
    current_weight_kg: float
    target_weight_kg: float
    activity_level: str
    dietary_preferences: list[str]
    allergens: list[str]
    eating_out_frequency: str
    bmi: float
    bmr: float
    minimum_kcal: int
    maximum_kcal: int
    daily_kcal: int
    protein_g: int
    carbohydrate_g: int
    fat_g: int

