from datetime import datetime

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
