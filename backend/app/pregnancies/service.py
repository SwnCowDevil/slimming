from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.models import User
from app.pregnancies.models import (
    DailyWellbeingLog,
    MealSchedule,
    PregnancyEpisode,
    PregnancyPreference,
)
from app.pregnancies.schemas import (
    GestationRead,
    MealScheduleCreate,
    MealScheduleRead,
    MealScheduleUpdate,
    PregnancyCreate,
    PregnancyPreferenceRead,
    PregnancyRead,
    PregnancyUpdate,
    WellbeingRead,
    WellbeingWrite,
)
from app.weights.models import WeightEntry


DEFAULT_MEAL_SCHEDULES = (
    ("breakfast", "早餐", "08:00", 0),
    ("snack_am", "上午加餐", "10:30", 1),
    ("lunch", "午餐", "12:30", 2),
    ("snack_pm", "下午加餐", "15:30", 3),
    ("dinner", "晚餐", "18:30", 4),
)


def derive_gestation(due_date: date, today: date | None = None) -> GestationRead:
    current = today or date.today()
    total_days = 280 - (due_date - current).days
    return GestationRead(week=total_days // 7, day=total_days % 7, total_days=total_days)


def get_active_episode(session: Session, user_id: str) -> PregnancyEpisode | None:
    return session.scalar(
        select(PregnancyEpisode)
        .where(PregnancyEpisode.user_id == user_id, PregnancyEpisode.status == "active")
        .options(selectinload(PregnancyEpisode.preferences), selectinload(PregnancyEpisode.meal_schedules))
    )


def require_active_episode(session: Session, user_id: str) -> PregnancyEpisode:
    episode = get_active_episode(session, user_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="尚未建立进行中的孕期档案")
    return episode


def latest_weight(session: Session, user_id: str) -> Decimal | None:
    return session.scalar(
        select(WeightEntry.weight_kg)
        .where(WeightEntry.user_id == user_id)
        .order_by(WeightEntry.recorded_date.desc())
        .limit(1)
    )


def to_read(session: Session, episode: PregnancyEpisode, user: User) -> PregnancyRead:
    preference = episode.preferences
    weight = latest_weight(session, user.id)
    return PregnancyRead(
        id=episode.id,
        user_id=episode.user_id,
        due_date=episode.due_date,
        due_date_source=episode.due_date_source,
        status=episode.status,
        timezone=episode.timezone,
        started_at=episode.started_at,
        ended_at=episode.ended_at,
        product_mode=user.product_mode,
        gestation=derive_gestation(episode.due_date),
        preferences=PregnancyPreferenceRead(
            height_cm=float(preference.height_cm),
            pre_pregnancy_weight_kg=(
                float(preference.pre_pregnancy_weight_kg)
                if preference.pre_pregnancy_weight_kg is not None
                else None
            ),
            current_weight_kg=float(weight) if weight is not None else None,
            activity_level=preference.activity_level,
            dietary_preferences=preference.dietary_preferences,
            allergens=preference.allergens,
            avoidances=preference.avoidances,
            disliked_foods=preference.disliked_foods,
        ),
    )


def create_episode(session: Session, user: User, body: PregnancyCreate) -> PregnancyEpisode:
    if get_active_episode(session, user.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已存在进行中的孕期档案")
    episode = PregnancyEpisode(
        user_id=user.id,
        due_date=body.due_date,
        due_date_source=body.due_date_source,
        timezone=body.timezone,
    )
    episode.preferences = PregnancyPreference(
        height_cm=body.height_cm,
        pre_pregnancy_weight_kg=body.pre_pregnancy_weight_kg,
        activity_level=body.activity_level,
        dietary_preferences=body.dietary_preferences,
        allergens=body.allergens,
        avoidances=body.avoidances,
        disliked_foods=body.disliked_foods,
    )
    episode.meal_schedules = [
        MealSchedule(code=code, display_name=name, scheduled_time=scheduled, position=position)
        for code, name, scheduled, position in DEFAULT_MEAL_SCHEDULES
    ]
    existing_weight = session.scalar(
        select(WeightEntry).where(
            WeightEntry.user_id == user.id, WeightEntry.recorded_date == date.today()
        )
    )
    if existing_weight is None:
        session.add(
            WeightEntry(
                user_id=user.id,
                recorded_date=date.today(),
                weight_kg=body.current_weight_kg,
            )
        )
    else:
        existing_weight.weight_kg = body.current_weight_kg
    user.product_mode = "pregnancy"
    session.add_all([episode, user])
    session.commit()
    return require_active_episode(session, user.id)


def update_episode(
    session: Session, user: User, episode: PregnancyEpisode, body: PregnancyUpdate
) -> PregnancyEpisode:
    payload = body.model_dump(exclude_unset=True)
    if "due_date" in payload:
        episode.due_date = payload.pop("due_date")
    if "due_date_source" in payload:
        episode.due_date_source = payload.pop("due_date_source")
    current_weight = payload.pop("current_weight_kg", None)
    preference = episode.preferences
    for name, value in payload.items():
        setattr(preference, name, value)
    if current_weight is not None:
        weight = session.scalar(
            select(WeightEntry).where(
                WeightEntry.user_id == user.id, WeightEntry.recorded_date == date.today()
            )
        )
        if weight is None:
            weight = WeightEntry(user_id=user.id, recorded_date=date.today())
        weight.weight_kg = current_weight
        session.add(weight)
    session.add_all([episode, preference])
    session.commit()
    return require_active_episode(session, user.id)


def end_episode(session: Session, user: User, episode: PregnancyEpisode) -> PregnancyEpisode:
    episode.status = "ended"
    episode.ended_at = datetime.now(timezone.utc)
    session.add(episode)
    session.commit()
    session.refresh(episode)
    return episode


def to_schedule_read(schedule: MealSchedule) -> MealScheduleRead:
    return MealScheduleRead(
        id=schedule.id,
        code=schedule.code,
        display_name=schedule.display_name,
        scheduled_time=schedule.scheduled_time,
        position=schedule.position,
        enabled=schedule.enabled,
    )


def list_schedules(session: Session, user_id: str) -> list[MealSchedule]:
    episode = require_active_episode(session, user_id)
    return list(
        session.scalars(
            select(MealSchedule)
            .where(MealSchedule.pregnancy_episode_id == episode.id)
            .order_by(MealSchedule.position, MealSchedule.id)
        ).all()
    )


def create_schedule(
    session: Session, user_id: str, body: MealScheduleCreate
) -> MealSchedule:
    episode = require_active_episode(session, user_id)
    occupied = session.scalar(
        select(MealSchedule).where(
            MealSchedule.pregnancy_episode_id == episode.id,
            MealSchedule.position == body.position,
        )
    )
    if occupied is not None:
        raise HTTPException(status_code=409, detail="该排序位置已被占用")
    schedule = MealSchedule(
        pregnancy_episode_id=episode.id,
        code=f"custom_{str(uuid4()).replace('-', '')[:12]}",
        display_name=body.display_name,
        scheduled_time=body.scheduled_time,
        position=body.position,
    )
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


def update_schedule(
    session: Session, user_id: str, schedule_id: str, body: MealScheduleUpdate
) -> MealSchedule:
    episode = require_active_episode(session, user_id)
    schedule = session.scalar(
        select(MealSchedule).where(
            MealSchedule.id == schedule_id,
            MealSchedule.pregnancy_episode_id == episode.id,
        )
    )
    if schedule is None:
        raise HTTPException(status_code=404, detail="餐次不存在")
    payload = body.model_dump(exclude_unset=True)
    if "position" in payload and payload["position"] != schedule.position:
        occupied = session.scalar(
            select(MealSchedule).where(
                MealSchedule.pregnancy_episode_id == episode.id,
                MealSchedule.position == payload["position"],
            )
        )
        if occupied is not None:
            raise HTTPException(status_code=409, detail="该排序位置已被占用")
    for name, value in payload.items():
        setattr(schedule, name, value)
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


def get_wellbeing(
    session: Session, user_id: str, log_date: date
) -> DailyWellbeingLog | None:
    episode = require_active_episode(session, user_id)
    return session.scalar(
        select(DailyWellbeingLog).where(
            DailyWellbeingLog.pregnancy_episode_id == episode.id,
            DailyWellbeingLog.log_date == log_date,
        )
    )


def put_wellbeing(
    session: Session, user_id: str, log_date: date, body: WellbeingWrite
) -> DailyWellbeingLog:
    episode = require_active_episode(session, user_id)
    item = session.scalar(
        select(DailyWellbeingLog).where(
            DailyWellbeingLog.pregnancy_episode_id == episode.id,
            DailyWellbeingLog.log_date == log_date,
        )
    )
    if item is None:
        item = DailyWellbeingLog(
            pregnancy_episode_id=episode.id, user_id=user_id, log_date=log_date
        )
    item.feeling_codes = list(dict.fromkeys(body.feeling_codes))
    item.note = body.note
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def to_wellbeing_read(item: DailyWellbeingLog | None, log_date: date) -> WellbeingRead:
    if item is None:
        return WellbeingRead(
            id=None, log_date=log_date, feeling_codes=[], note=None, updated_at=None
        )
    return WellbeingRead(
        id=item.id,
        log_date=item.log_date,
        feeling_codes=item.feeling_codes,
        note=item.note,
        updated_at=item.updated_at,
    )
