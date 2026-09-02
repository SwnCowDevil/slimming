from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.profiles.models import BodyProfile
from app.profiles.schemas import BodyProfileInput, ProfileRead
from app.profiles.service import to_profile_read, upsert_profile


router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


@router.post("/onboarding", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
def onboarding(
    body: BodyProfileInput,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ProfileRead:
    return to_profile_read(upsert_profile(session, current_user.id, body))


@router.get("/me", response_model=ProfileRead)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ProfileRead:
    profile = session.scalar(select(BodyProfile).where(BodyProfile.user_id == current_user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="尚未完成建档")
    return to_profile_read(profile)

