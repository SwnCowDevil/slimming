import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.schemas import (
    AuthSession,
    DevAuthRequest,
    UserRead,
    WechatLoginRequest,
    WechatProfileUpdate,
)
from app.auth.service import (
    WechatGateway,
    find_or_create_wechat_user,
    get_current_user,
    get_wechat_gateway,
    issue_access_token,
)
from app.core.config import Settings, get_settings
from app.db.session import get_session


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/wechat", response_model=AuthSession)
def login_with_wechat(
    body: WechatLoginRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
    gateway: WechatGateway = Depends(get_wechat_gateway),
) -> AuthSession:
    try:
        wechat_session = gateway.exchange_code(body.code)
    except (httpx.HTTPError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="微信登录失败，请重试") from None
    user = find_or_create_wechat_user(session, gateway.app_id, wechat_session)
    return AuthSession(user_id=user.id, access_token=issue_access_token(user.id, settings))


@router.post("/dev", response_model=AuthSession)
def dev_auth(
    body: DevAuthRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuthSession:
    if not settings.enable_dev_auth:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    user = session.get(User, body.user_id)
    if user is None:
        user = User(id=body.user_id)
        session.add(user)
        session.commit()
    return AuthSession(user_id=user.id, access_token=issue_access_token(user.id, settings))


@router.patch("/me/wechat-profile", response_model=UserRead)
def update_wechat_profile(
    body: WechatProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> User:
    current_user.nickname = body.nickname
    current_user.avatar_url = str(body.avatar_url) if body.avatar_url else None
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user
