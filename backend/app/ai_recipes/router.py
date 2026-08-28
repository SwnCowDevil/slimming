from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.ai_recipes.provider import AiProviderConfigurationError, AiRecipeProvider, get_ai_recipe_provider
from app.ai_recipes.schemas import RecommendationBatch, RecommendationCreateRequest
from app.ai_recipes.service import create_recommendation_session, next_recommendation_batch
from app.auth.models import User
from app.auth.service import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_session


router = APIRouter(prefix="/api/v1/ai/recipe-recommendations", tags=["ai-recipes"])


def _provider(request: Request, settings: Settings) -> AiRecipeProvider | None:
    injected = getattr(request.app.state, "ai_recipe_provider", None)
    if injected is not None:
        return injected
    if not settings.ai_recipe_enabled:
        return None
    try:
        return get_ai_recipe_provider(settings)
    except AiProviderConfigurationError:
        return None


@router.post("", response_model=RecommendationBatch, status_code=status.HTTP_201_CREATED)
def recommend_recipes(
    body: RecommendationCreateRequest,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RecommendationBatch:
    client_ip = request.client.host if request.client is not None else "unknown"
    return create_recommendation_session(
        session,
        current_user,
        body,
        idempotency_key,
        client_ip,
        settings,
        _provider(request, settings),
    )


@router.post("/{session_id}/next", response_model=RecommendationBatch)
def next_recipes(
    session_id: str,
    request: Request,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=128),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RecommendationBatch:
    client_ip = request.client.host if request.client is not None else "unknown"
    return next_recommendation_batch(
        session,
        current_user,
        session_id,
        idempotency_key,
        client_ip,
        settings,
        _provider(request, settings),
    )
