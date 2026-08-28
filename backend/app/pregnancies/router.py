from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.pregnancies.schemas import PregnancyCreate, PregnancyRead, PregnancyUpdate
from app.pregnancies.service import (
    create_episode,
    end_episode,
    require_active_episode,
    to_read,
    update_episode,
)


router = APIRouter(prefix="/api/v1/pregnancies", tags=["pregnancies"])


@router.post("", response_model=PregnancyRead, status_code=status.HTTP_201_CREATED)
def create_pregnancy(
    body: PregnancyCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> PregnancyRead:
    return to_read(session, create_episode(session, current_user, body), current_user)


@router.get("/current", response_model=PregnancyRead)
def current_pregnancy(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> PregnancyRead:
    return to_read(session, require_active_episode(session, current_user.id), current_user)


@router.patch("/current", response_model=PregnancyRead)
def patch_pregnancy(
    body: PregnancyUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> PregnancyRead:
    episode = require_active_episode(session, current_user.id)
    return to_read(session, update_episode(session, current_user, episode, body), current_user)


@router.post("/current/end", response_model=PregnancyRead)
def close_pregnancy(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> PregnancyRead:
    episode = end_episode(session, current_user, require_active_episode(session, current_user.id))
    return to_read(session, episode, current_user)
