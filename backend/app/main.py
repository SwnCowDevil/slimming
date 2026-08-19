from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.auth.service import HttpWechatGateway, WechatGateway
from app.core.config import Settings, get_settings
from app.profiles.router import router as profiles_router
from app.foods.router import router as foods_router


def create_app(
    settings: Settings | None = None,
    wechat_gateway: WechatGateway | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(title="Slimming API", version="0.1.0")
    app.state.wechat_gateway = wechat_gateway or HttpWechatGateway(
        resolved_settings.wechat_app_id,
        resolved_settings.wechat_app_secret,
    )
    app.include_router(auth_router)
    app.include_router(profiles_router)
    app.include_router(foods_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "slimming-api"}

    return app


app = create_app()
