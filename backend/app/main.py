from contextlib import asynccontextmanager

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
from app.recipes.router import admin_router as recipe_admin_router, router as recipes_router
from app.ai_coach.router import router as ai_router
from app.dietitians.router import directory_router as dietitians_router
from app.dietitians.router import request_router as dietitian_requests_router
from app.media.router import router as media_router
from app.pregnancies.router import (
    router as pregnancies_router,
    schedule_router as meal_schedules_router,
    wellbeing_router,
)
from app.family.router import router as family_router
from app.meal_plans.router import router as meal_plans_router
from app.ai_recipes.router import candidate_router as ai_recipe_candidates_router, router as ai_recipes_router
from app.ai_recipes.provider import AiProviderConfigurationError, get_ai_recipe_provider


def create_app(
    settings: Settings | None = None,
    wechat_gateway: WechatGateway | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        yield
        provider = application.state.ai_recipe_provider
        close = getattr(provider, "close", None)
        if callable(close):
            close()

    app = FastAPI(title="Slimming API", version="0.1.0", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.ai_recipe_provider = None
    if resolved_settings.ai_recipe_enabled:
        try:
            app.state.ai_recipe_provider = get_ai_recipe_provider(resolved_settings)
        except AiProviderConfigurationError:
            app.state.ai_recipe_provider = None
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
    app.include_router(recipe_admin_router)
    app.include_router(ai_router)
    app.include_router(dietitians_router)
    app.include_router(dietitian_requests_router)
    app.include_router(media_router)
    app.include_router(pregnancies_router)
    app.include_router(meal_schedules_router)
    app.include_router(wellbeing_router)
    app.include_router(family_router)
    app.include_router(meal_plans_router)
    app.include_router(ai_recipes_router)
    app.include_router(ai_recipe_candidates_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "slimming-api"}

    return app


app = create_app()
