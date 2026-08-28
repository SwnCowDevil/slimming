import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
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
from app.media.models import MediaUpload


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


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    storage_keys = session.scalars(
        select(MediaUpload.storage_key).where(MediaUpload.user_id == current_user.id)
    ).all()
    media_root = settings.media_root.resolve()
    for storage_key in storage_keys:
        destination = (media_root / storage_key).resolve()
        if media_root in destination.parents:
            destination.unlink(missing_ok=True)

    session.delete(current_user)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
