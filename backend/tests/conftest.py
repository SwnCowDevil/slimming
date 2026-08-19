from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.service import WechatSession
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app


class FakeWechatGateway:
    app_id = "test-app"
    openid = "openid-123"
    unionid: str | None = None

    def exchange_code(self, code: str) -> WechatSession:
        if code == "invalid":
            raise ValueError("invalid code")
        return WechatSession(openid=self.openid, unionid=self.unionid)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url="sqlite+pysqlite:///:memory:",
        jwt_secret="test-secret-with-at-least-thirty-two-bytes",
        wechat_app_id="test-app",
        wechat_app_secret="test-secret",
        enable_dev_auth=False,
    )


@pytest.fixture
def wechat_gateway() -> FakeWechatGateway:
    return FakeWechatGateway()


@pytest.fixture
def client(settings: Settings, wechat_gateway: FakeWechatGateway) -> Iterator[TestClient]:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    app = create_app(settings=settings, wechat_gateway=wechat_gateway)

    def override_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client
