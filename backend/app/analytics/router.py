from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.schemas import AnalyticsSummary
from app.analytics.service import build_summary
from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def summary(
    period: int = Query(default=7),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AnalyticsSummary:
    if period not in {7, 30, 90}:
        raise HTTPException(status_code=422, detail="period must be 7, 30, or 90 days")
    return build_summary(session, current_user.id, period, end_date or date.today())
