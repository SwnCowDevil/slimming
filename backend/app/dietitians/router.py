from pydantic import BaseModel, ConfigDict, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.dietitians.models import Dietitian, DietitianRequest


class DietitianRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    display_name: str
    specialties: list[str]
    credentials: str
    bio: str
    avatar_url: str | None


class MatchingRequestCreate(BaseModel):
    dietitian_id: str
    goal: str = Field(min_length=1, max_length=120)
    note: str = Field(default="", max_length=1000)


class MatchingRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    dietitian_id: str
    goal: str
    note: str
    status: str


directory_router = APIRouter(prefix="/api/v1/dietitians", tags=["dietitians"])
request_router = APIRouter(prefix="/api/v1/dietitian-requests", tags=["dietitians"])


@directory_router.get("", response_model=list[DietitianRead])
def list_dietitians(
    _: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[Dietitian]:
    return list(session.scalars(select(Dietitian)).all())


@request_router.post("", response_model=MatchingRequestRead, status_code=201)
def submit_request(
    body: MatchingRequestCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DietitianRequest:
    if session.get(Dietitian, body.dietitian_id) is None:
        raise HTTPException(status_code=404, detail="dietitian not found")
    request = DietitianRequest(user_id=current_user.id, **body.model_dump())
    session.add(request)
    session.commit()
    session.refresh(request)
    return request
