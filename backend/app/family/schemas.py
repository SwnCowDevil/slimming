from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ALLOWED_PERMISSION_SCOPES = {
    "pregnancy:read",
    "meal:read",
    "meal_entry:write_for_owner",
    "meal_plan:write_for_owner",
    "family_task:write",
}


class InvitationRead(BaseModel):
    id: str
    token: str
    expires_at: datetime


class InvitationAccept(BaseModel):
    token: str = Field(min_length=16, max_length=256)


class PermissionUpdate(BaseModel):
    permission_scopes: list[str] = Field(min_length=1, max_length=10)


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pregnancy_episode_id: str
    owner_user_id: str
    member_user_id: str
    role: str
    status: str
    permission_scopes: list[str]
    joined_at: datetime
    revoked_at: datetime | None


class MembershipList(BaseModel):
    items: list[MembershipRead]


class FamilyTaskCreate(BaseModel):
    task_date: date
    task_type: Literal["shopping", "cooking", "other"]
    title: str = Field(min_length=1, max_length=160)
    content: dict = Field(default_factory=dict)
    assignee_user_id: str | None = None
    subject_user_id: str | None = None


class FamilyTaskUpdate(BaseModel):
    status: Literal["pending", "in_progress", "completed", "cancelled"] | None = None
    assignee_user_id: str | None = None
    title: str | None = Field(default=None, min_length=1, max_length=160)


class FamilyTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pregnancy_episode_id: str
    subject_user_id: str
    task_date: date
    task_type: str
    title: str
    content: dict
    assignee_user_id: str | None
    status: str
    created_by_user_id: str
    completed_by_user_id: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class FamilyTaskList(BaseModel):
    items: list[FamilyTaskRead]
