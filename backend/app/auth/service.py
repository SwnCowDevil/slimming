from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User, WechatIdentity
from app.core.config import Settings, get_settings
from app.db.session import get_session


@dataclass(frozen=True)
class WechatSession:
    openid: str
    unionid: str | None = None


class WechatGateway(Protocol):
    app_id: str

    def exchange_code(self, code: str) -> WechatSession: ...


class HttpWechatGateway:
    endpoint = "https://api.weixin.qq.com/sns/jscode2session"

    def __init__(self, app_id: str, app_secret: str) -> None:
        self.app_id = app_id
        self.app_secret = app_secret

    def exchange_code(self, code: str) -> WechatSession:
        response = httpx.get(
            self.endpoint,
            params={
                "appid": self.app_id,
                "secret": self.app_secret,
                "js_code": code,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        if "openid" not in payload:
            raise ValueError("wechat exchange rejected")
        return WechatSession(openid=payload["openid"], unionid=payload.get("unionid"))


def get_wechat_gateway(request: Request) -> WechatGateway:
    return request.app.state.wechat_gateway


def find_or_create_wechat_user(
    session: Session,
    app_id: str,
    wechat_session: WechatSession,
) -> User:
    identity = session.scalar(
        select(WechatIdentity).where(
            WechatIdentity.app_id == app_id,
            WechatIdentity.openid == wechat_session.openid,
        )
    )
    if identity is not None:
        return identity.user

    user = User()
    session.add(user)
    session.flush()
    session.add(
        WechatIdentity(
            user_id=user.id,
            app_id=app_id,
            openid=wechat_session.openid,
            unionid=wechat_session.unionid,
        )
    )
    session.commit()
    session.refresh(user)
    return user


def issue_access_token(user_id: str, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": user_id, "iat": now, "exp": now + timedelta(seconds=settings.jwt_ttl_seconds)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态已失效") from exc
    user = session.get(User, payload.get("sub"))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态已失效")
    return user

