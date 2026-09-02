from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class WechatLoginRequest(BaseModel):
    code: str = Field(min_length=1, max_length=256)


class AuthSession(BaseModel):
    user_id: str
    access_token: str
    token_type: str = "bearer"


class WechatProfileUpdate(BaseModel):
    nickname: str = Field(min_length=1, max_length=80)
    avatar_url: HttpUrl | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nickname: str | None
    avatar_url: str | None


class DevAuthRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=80)

