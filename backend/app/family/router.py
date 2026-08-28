from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_current_user
from app.db.session import get_session
from app.family.schemas import (
    InvitationAccept,
    InvitationRead,
    FamilyTaskCreate,
    FamilyTaskList,
    FamilyTaskRead,
    FamilyTaskUpdate,
    MembershipList,
    MembershipRead,
    PermissionUpdate,
)
from app.family.service import (
    accept_invitation,
    create_family_task,
    create_invitation,
    list_family_tasks,
    list_memberships,
    revoke_membership,
    update_family_task,
    update_permissions,
)


router = APIRouter(prefix="/api/v1/family", tags=["family"])


@router.post("/invitations", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
def issue_invitation(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> InvitationRead:
    invitation, token = create_invitation(session, current_user.id)
    return InvitationRead(id=invitation.id, token=token, expires_at=invitation.expires_at)


@router.post("/invitations/accept", response_model=MembershipRead)
def accept_family_invitation(
    body: InvitationAccept,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return accept_invitation(session, current_user.id, body.token)


@router.get("/members", response_model=MembershipList)
def get_members(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> MembershipList:
    return MembershipList(items=list_memberships(session, current_user.id))


@router.patch("/members/{membership_id}/permissions", response_model=MembershipRead)
def change_permissions(
    membership_id: str,
    body: PermissionUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return update_permissions(
        session, current_user.id, membership_id, body.permission_scopes
    )


@router.delete("/members/{membership_id}", response_model=MembershipRead)
def revoke_family_member(
    membership_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return revoke_membership(session, current_user.id, membership_id)


@router.get("/tasks", response_model=FamilyTaskList)
def get_family_tasks(
    task_date: date = Query(alias="date"),
    subject_user_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> FamilyTaskList:
    return FamilyTaskList(
        items=list_family_tasks(
            session, current_user.id, task_date, subject_user_id
        )
    )


@router.post("/tasks", response_model=FamilyTaskRead, status_code=status.HTTP_201_CREATED)
def add_family_task(
    body: FamilyTaskCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return create_family_task(session, current_user.id, body)


@router.patch("/tasks/{task_id}", response_model=FamilyTaskRead)
def patch_family_task(
    task_id: str,
    body: FamilyTaskUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return update_family_task(session, current_user.id, task_id, body)
