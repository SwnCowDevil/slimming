import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.family.models import ConsentEvent, FamilyInvitation, FamilyMembership, FamilyTask
from app.family.schemas import FamilyTaskCreate, FamilyTaskUpdate
from app.family.schemas import ALLOWED_PERMISSION_SCOPES
from app.pregnancies.models import PregnancyEpisode
from app.pregnancies.service import get_active_episode, require_active_episode


DEFAULT_PARTNER_SCOPES = ["pregnancy:read", "meal:read"]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def add_event(
    session: Session,
    episode_id: str,
    actor_user_id: str,
    event_type: str,
    membership_id: str | None = None,
    payload: dict | None = None,
) -> None:
    session.add(
        ConsentEvent(
            pregnancy_episode_id=episode_id,
            actor_user_id=actor_user_id,
            membership_id=membership_id,
            event_type=event_type,
            event_payload=payload or {},
        )
    )


def create_invitation(
    session: Session, owner_user_id: str
) -> tuple[FamilyInvitation, str]:
    episode = require_active_episode(session, owner_user_id)
    token = secrets.token_urlsafe(32)
    invitation = FamilyInvitation(
        pregnancy_episode_id=episode.id,
        invited_by_user_id=owner_user_id,
        token_hash=token_digest(token),
        expires_at=now_utc() + timedelta(hours=24),
    )
    session.add(invitation)
    session.flush()
    add_event(session, episode.id, owner_user_id, "invitation_created")
    session.commit()
    session.refresh(invitation)
    return invitation, token


def accept_invitation(
    session: Session, actor_user_id: str, token: str
) -> FamilyMembership:
    invitation = session.scalar(
        select(FamilyInvitation).where(FamilyInvitation.token_hash == token_digest(token))
    )
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="邀请无效")
    if invitation.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邀请已被使用")
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now_utc():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="邀请已过期")
    if invitation.invited_by_user_id == actor_user_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="不能接受自己的邀请")
    episode = session.get(PregnancyEpisode, invitation.pregnancy_episode_id)
    if episode is None or episode.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="对应孕期已结束")
    existing = session.scalar(
        select(FamilyMembership).where(
            FamilyMembership.pregnancy_episode_id == episode.id,
            FamilyMembership.member_user_id == actor_user_id,
        )
    )
    if existing is not None and existing.status == "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已经加入该家庭")
    if existing is None:
        membership = FamilyMembership(
            pregnancy_episode_id=episode.id,
            owner_user_id=episode.user_id,
            member_user_id=actor_user_id,
            permission_scopes=list(DEFAULT_PARTNER_SCOPES),
        )
    else:
        membership = existing
        membership.status = "active"
        membership.revoked_at = None
        membership.permission_scopes = list(DEFAULT_PARTNER_SCOPES)
    session.add(membership)
    session.flush()
    invitation.accepted_by_user_id = actor_user_id
    invitation.accepted_at = now_utc()
    add_event(
        session,
        episode.id,
        actor_user_id,
        "invitation_accepted",
        membership.id,
        {"permission_scopes": list(DEFAULT_PARTNER_SCOPES)},
    )
    session.commit()
    session.refresh(membership)
    return membership


def list_memberships(session: Session, actor_user_id: str) -> list[FamilyMembership]:
    return list(
        session.scalars(
            select(FamilyMembership)
            .where(
                or_(
                    FamilyMembership.owner_user_id == actor_user_id,
                    FamilyMembership.member_user_id == actor_user_id,
                )
            )
            .order_by(FamilyMembership.joined_at)
        ).all()
    )


def require_owner_membership(
    session: Session, actor_user_id: str, membership_id: str
) -> FamilyMembership:
    membership = session.get(FamilyMembership, membership_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="家庭成员不存在")
    if membership.owner_user_id != actor_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有数据所有者可以修改授权")
    return membership


def update_permissions(
    session: Session,
    actor_user_id: str,
    membership_id: str,
    scopes: list[str],
) -> FamilyMembership:
    unknown = set(scopes) - ALLOWED_PERMISSION_SCOPES
    if unknown:
        raise HTTPException(status_code=422, detail=f"未知权限：{', '.join(sorted(unknown))}")
    membership = require_owner_membership(session, actor_user_id, membership_id)
    if membership.status != "active":
        raise HTTPException(status_code=409, detail="成员关系已撤销")
    membership.permission_scopes = list(dict.fromkeys(scopes))
    add_event(
        session,
        membership.pregnancy_episode_id,
        actor_user_id,
        "permissions_changed",
        membership.id,
        {"permission_scopes": membership.permission_scopes},
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


def revoke_membership(
    session: Session, actor_user_id: str, membership_id: str
) -> FamilyMembership:
    membership = require_owner_membership(session, actor_user_id, membership_id)
    if membership.status != "revoked":
        membership.status = "revoked"
        membership.revoked_at = now_utc()
        add_event(
            session,
            membership.pregnancy_episode_id,
            actor_user_id,
            "membership_revoked",
            membership.id,
        )
        session.add(membership)
        session.commit()
        session.refresh(membership)
    return membership


def authorize_subject(
    session: Session,
    actor_user_id: str,
    subject_user_id: str,
    scope: str,
) -> PregnancyEpisode:
    if actor_user_id == subject_user_id:
        return require_active_episode(session, subject_user_id)
    episode = get_active_episode(session, subject_user_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有可访问的孕期档案")
    membership = session.scalar(
        select(FamilyMembership).where(
            FamilyMembership.pregnancy_episode_id == episode.id,
            FamilyMembership.owner_user_id == subject_user_id,
            FamilyMembership.member_user_id == actor_user_id,
            FamilyMembership.status == "active",
        )
    )
    if membership is None or scope not in membership.permission_scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="未获得所需的家庭权限")
    return episode


def create_family_task(
    session: Session, actor_user_id: str, body: FamilyTaskCreate
) -> FamilyTask:
    subject_user_id = body.subject_user_id or actor_user_id
    if subject_user_id == actor_user_id:
        episode = require_active_episode(session, subject_user_id)
    else:
        episode = authorize_subject(
            session,
            actor_user_id=actor_user_id,
            subject_user_id=subject_user_id,
            scope="family_task:write",
        )
    task = FamilyTask(
        pregnancy_episode_id=episode.id,
        subject_user_id=subject_user_id,
        task_date=body.task_date,
        task_type=body.task_type,
        title=body.title,
        content=body.content,
        assignee_user_id=body.assignee_user_id,
        created_by_user_id=actor_user_id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def list_family_tasks(
    session: Session,
    actor_user_id: str,
    task_date,
    subject_user_id: str | None = None,
) -> list[FamilyTask]:
    subject_id = subject_user_id or actor_user_id
    if subject_id == actor_user_id:
        episode = require_active_episode(session, subject_id)
    else:
        episode = authorize_subject(
            session,
            actor_user_id=actor_user_id,
            subject_user_id=subject_id,
            scope="pregnancy:read",
        )
    return list(
        session.scalars(
            select(FamilyTask)
            .where(
                FamilyTask.pregnancy_episode_id == episode.id,
                FamilyTask.task_date == task_date,
            )
            .order_by(FamilyTask.created_at)
        ).all()
    )


def update_family_task(
    session: Session,
    actor_user_id: str,
    task_id: str,
    body: FamilyTaskUpdate,
) -> FamilyTask:
    task = session.get(FamilyTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="家庭任务不存在")
    if actor_user_id != task.subject_user_id:
        authorize_subject(
            session,
            actor_user_id=actor_user_id,
            subject_user_id=task.subject_user_id,
            scope="family_task:write",
        )
    payload = body.model_dump(exclude_unset=True)
    for name, value in payload.items():
        setattr(task, name, value)
    if task.status == "completed":
        task.completed_by_user_id = actor_user_id
        task.completed_at = now_utc()
    elif "status" in payload:
        task.completed_by_user_id = None
        task.completed_at = None
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
