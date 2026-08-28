from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.auth.service import HttpWechatGateway, WechatGateway
from app.core.config import Settings, get_settings
from app.profiles.router import router as profiles_router
from app.foods.router import router as foods_router
from app.meals.router import router as meals_router
from app.weights.router import router as weights_router
from app.habits.router import router as habits_router
from app.analytics.router import router as analytics_router
from app.recipes.router import router as recipes_router
from app.ai_coach.router import router as ai_router
from app.dietitians.router import directory_router as dietitians_router
from app.dietitians.router import request_router as dietitian_requests_router
from app.media.router import router as media_router
from app.pregnancies.router import (
    router as pregnancies_router,
    schedule_router as meal_schedules_router,
    wellbeing_router,
)


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
    app.include_router(meals_router)
    app.include_router(weights_router)
    app.include_router(habits_router)
    app.include_router(analytics_router)
    app.include_router(recipes_router)
    app.include_router(ai_router)
    app.include_router(dietitians_router)
    app.include_router(dietitian_requests_router)
    app.include_router(media_router)
    app.include_router(pregnancies_router)
    app.include_router(meal_schedules_router)
    app.include_router(wellbeing_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "slimming-api"}

    return app


app = create_app()
