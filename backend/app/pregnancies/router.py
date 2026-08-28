from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.pregnancies.schemas import (
    MealScheduleCreate,
    MealScheduleRead,
    MealScheduleUpdate,
    PregnancyCreate,
    PregnancyRead,
    PregnancyUpdate,
    WellbeingRead,
    WellbeingWrite,
)
from app.pregnancies.service import (
    create_schedule,
    create_episode,
    end_episode,
    get_wellbeing,
    list_schedules,
    put_wellbeing,
    require_active_episode,
    to_schedule_read,
    to_read,
    to_wellbeing_read,
    update_schedule,
    update_episode,
)


router = APIRouter(prefix="/api/v1/pregnancies", tags=["pregnancies"])
schedule_router = APIRouter(prefix="/api/v1/meal-schedules", tags=["meal-schedules"])
wellbeing_router = APIRouter(prefix="/api/v1/wellbeing", tags=["wellbeing"])


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


@schedule_router.get("", response_model=list[MealScheduleRead])
def get_meal_schedules(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[MealScheduleRead]:
    return [to_schedule_read(item) for item in list_schedules(session, current_user.id)]


@schedule_router.post("", response_model=MealScheduleRead, status_code=status.HTTP_201_CREATED)
def post_meal_schedule(
    body: MealScheduleCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> MealScheduleRead:
    return to_schedule_read(create_schedule(session, current_user.id, body))


@schedule_router.patch("/{schedule_id}", response_model=MealScheduleRead)
def patch_meal_schedule(
    schedule_id: str,
    body: MealScheduleUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> MealScheduleRead:
    return to_schedule_read(update_schedule(session, current_user.id, schedule_id, body))


@wellbeing_router.get("/{log_date}", response_model=WellbeingRead)
def read_wellbeing(
    log_date: date,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> WellbeingRead:
    return to_wellbeing_read(get_wellbeing(session, current_user.id, log_date), log_date)


@wellbeing_router.put("/{log_date}", response_model=WellbeingRead)
def write_wellbeing(
    log_date: date,
    body: WellbeingWrite,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> WellbeingRead:
    return to_wellbeing_read(
        put_wellbeing(session, current_user.id, log_date, body), log_date
    )
