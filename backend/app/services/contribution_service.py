"""
Contribution service: list, get, create, update, submit, approve, reject.
"""

from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.models.contribution import Contribution
from app.models.enums import ContributionStatus, ReportingCycleStatus, UserRole
from app.models.user import User
from app.schemas.contribution import ContributionCreate, ContributionUpdate
from app.services.reporting_cycle_service import get_reporting_cycle_by_id
from app.core.pagination import PAGINATION_LIMIT_DEFAULT, PAGINATION_SKIP_DEFAULT


def get_contribution_by_id(session: Session, contribution_id: UUID) -> Contribution | None:
    """Return contribution by id or None."""
    return session.get(Contribution, contribution_id)


def get_contribution_by_id_with_relations(
    session: Session, contribution_id: UUID
) -> Contribution | None:
    """Return contribution by id with department and reporting_cycle loaded, or None. Use when building ContributionRead after a commit to avoid lazy-load issues."""
    stmt = (
        select(Contribution)
        .where(Contribution.id == contribution_id)
        .options(
            selectinload(Contribution.department),
            selectinload(Contribution.reporting_cycle),
        )
    )
    return session.exec(stmt).first()


def _user_can_access_contribution(user: User, contribution: Contribution) -> bool:
    """Admin and viewer can access any; coordinator only their department."""
    if user.role == UserRole.ADMIN or user.role == UserRole.VIEWER:
        return True
    if user.role == UserRole.DEPARTMENT_COORDINATOR and user.department_id is not None:
        return contribution.department_id == user.department_id
    return False


def _user_can_edit_contribution(user: User, contribution: Contribution, cycle_open: bool) -> bool:
    """Admin can always edit. Coordinator can edit own department's if not APPROVED and cycle open (or we allow edit in closed for admin only)."""
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.DEPARTMENT_COORDINATOR and user.department_id is not None:
        if contribution.department_id != user.department_id:
            return False
        if contribution.status == ContributionStatus.APPROVED:
            return False
        # Prefer: block non-admin edits if cycle is closed
        return cycle_open
    return False


def ensure_can_view_contribution(user: User, contribution: Contribution) -> None:
    """Raise ValueError if user cannot view this contribution."""
    if not _user_can_access_contribution(user, contribution):
        raise ValueError("You are not allowed to access this contribution.")


def ensure_can_manage_metrics(session: Session, user: User, contribution: Contribution) -> None:
    """Raise ValueError if user cannot add/delete metrics for this contribution. Viewers never; coordinators only own dept and when contribution editable; admins always."""
    if user.role == UserRole.VIEWER:
        raise ValueError("You are not allowed to modify metrics for this contribution.")
    if user.role == UserRole.ADMIN:
        return
    cycle = get_reporting_cycle_by_id(session, contribution.reporting_cycle_id)
    cycle_open = cycle is not None and cycle.status == ReportingCycleStatus.OPEN
    if not _user_can_edit_contribution(user, contribution, cycle_open):
        raise ValueError("You are not allowed to modify metrics for this contribution.")


def ensure_can_manage_evidence(session: Session, user: User, contribution: Contribution) -> None:
    """Raise ValueError if user cannot add/delete evidence for this contribution. Same rules as metrics."""
    if user.role == UserRole.VIEWER:
        raise ValueError("You are not allowed to modify evidence for this contribution.")
    if user.role == UserRole.ADMIN:
        return
    cycle = get_reporting_cycle_by_id(session, contribution.reporting_cycle_id)
    cycle_open = cycle is not None and cycle.status == ReportingCycleStatus.OPEN
    if not _user_can_edit_contribution(user, contribution, cycle_open):
        raise ValueError("You are not allowed to modify evidence for this contribution.")


def ensure_can_add_comment(user: User, contribution: Contribution) -> None:
    """Raise ValueError if user cannot add a comment. Viewers read-only; admins and coordinators with access can add (even if approved)."""
    if user.role == UserRole.VIEWER:
        raise ValueError("You are not allowed to comment on this contribution.")
    if not _user_can_access_contribution(user, contribution):
        raise ValueError("You are not allowed to comment on this contribution.")


def list_contributions(
    session: Session,
    current_user: User,
    reporting_cycle_id: UUID | None = None,
    department_id: UUID | None = None,
    sdg_id: int | None = None,
    status: ContributionStatus | None = None,
    type_filter: str | None = None,
    skip: int = PAGINATION_SKIP_DEFAULT,
    limit: int = PAGINATION_LIMIT_DEFAULT,
) -> list[Contribution]:
    """
    List contributions with optional filters. Access: admin/viewer see all;
    department coordinator sees only their department's contributions.
    Pagination: skip >= 0, limit applied after filters.
    """
    from app.models.enums import ContributionType

    statement = (
        select(Contribution)
        .options(
            selectinload(Contribution.department),
            selectinload(Contribution.reporting_cycle),
        )
        .order_by(Contribution.created_at.desc())
    )
    if reporting_cycle_id is not None:
        statement = statement.where(Contribution.reporting_cycle_id == reporting_cycle_id)
    if department_id is not None:
        statement = statement.where(Contribution.department_id == department_id)
    if sdg_id is not None:
        statement = statement.where(Contribution.primary_sdg_id == sdg_id)
    if status is not None:
        statement = statement.where(Contribution.status == status)
    if type_filter is not None:
        try:
            ct = ContributionType(type_filter)
            statement = statement.where(Contribution.type == ct)
        except ValueError:
            pass  # invalid enum, return empty or ignore
    rows = list(session.exec(statement).all())
    # Apply access: coordinator only their department
    if current_user.role == UserRole.DEPARTMENT_COORDINATOR and current_user.department_id is not None:
        rows = [c for c in rows if c.department_id == current_user.department_id]
    return rows[skip : skip + limit]


def create_contribution(
    session: Session,
    reporting_cycle_id: UUID,
    data: ContributionCreate,
    current_user: User,
) -> Contribution:
    """
    Create a contribution in the given reporting cycle. Cycle must exist and be OPEN.
    Department coordinator: department_id must match their department (or we set it from user).
    Admin: can set any department. created_by_user_id = current user, status = DRAFT.
    """
    cycle = get_reporting_cycle_by_id(session, reporting_cycle_id)
    if cycle is None:
        raise ValueError("Reporting cycle not found.")
    if cycle.status != ReportingCycleStatus.OPEN:
        raise ValueError("Contributions can only be created in an open reporting cycle.")

    if current_user.role == UserRole.ADMIN:
        dept_id = data.department_id
        if dept_id is None:
            raise ValueError("department_id is required when creating a contribution.")
    elif current_user.role == UserRole.DEPARTMENT_COORDINATOR:
        if current_user.department_id is None:
            raise ValueError("You must belong to a department to create contributions.")
        dept_id = current_user.department_id
        if data.department_id is not None and data.department_id != dept_id:
            raise ValueError("You are not allowed to create contributions for another department.")
    else:
        # Viewer or other: require department and must be their own
        if current_user.department_id is not None:
            dept_id = current_user.department_id
            if data.department_id is not None and data.department_id != dept_id:
                raise ValueError("You are not allowed to create contributions for another department.")
        else:
            raise ValueError("department_id is required; you must belong to a department to create contributions.")

    contribution = Contribution(
        reporting_cycle_id=reporting_cycle_id,
        department_id=dept_id,
        title=data.title.strip(),
        type=data.type,
        description=data.description.strip(),
        primary_sdg_id=data.primary_sdg_id,
        secondary_sdg_ids=sorted(set(data.secondary_sdg_ids)) if data.secondary_sdg_ids else None,
        start_date=data.start_date,
        end_date=data.end_date,
        status=ContributionStatus.DRAFT,
        created_by_user_id=current_user.id,
    )
    session.add(contribution)
    session.commit()
    session.refresh(contribution)
    return contribution


def update_contribution(
    session: Session,
    contribution: Contribution,
    data: ContributionUpdate,
    current_user: User,
) -> Contribution:
    """
    Partial update. Coordinator can update own department's contribution only if not APPROVED
    and cycle is open. Admin can update any. Approved contributions cannot be edited by non-admin.
    """
    cycle = get_reporting_cycle_by_id(session, contribution.reporting_cycle_id)
    cycle_open = cycle is not None and cycle.status == ReportingCycleStatus.OPEN
    if not _user_can_edit_contribution(current_user, contribution, cycle_open):
        if contribution.status == ContributionStatus.APPROVED:
            raise ValueError("Approved contributions cannot be edited by non-admin users.")
        if not cycle_open and current_user.role != UserRole.ADMIN:
            raise ValueError("You are not allowed to modify this contribution.")
        raise ValueError("You are not allowed to modify this contribution.")

    if data.title is not None:
        contribution.title = data.title.strip()
    if data.type is not None:
        contribution.type = data.type
    if data.description is not None:
        contribution.description = data.description.strip()
    if data.primary_sdg_id is not None:
        contribution.primary_sdg_id = data.primary_sdg_id
    if data.secondary_sdg_ids is not None:
        contribution.secondary_sdg_ids = sorted(set(data.secondary_sdg_ids))
    if data.start_date is not None:
        contribution.start_date = data.start_date
    if data.end_date is not None:
        contribution.end_date = data.end_date
    if current_user.role == UserRole.ADMIN and data.department_id is not None:
        contribution.department_id = data.department_id

    if contribution.end_date is not None and contribution.start_date is not None:
        if contribution.end_date < contribution.start_date:
            raise ValueError("end_date must not be earlier than start_date.")

    session.add(contribution)
    session.commit()
    session.refresh(contribution)
    return contribution


def submit_contribution(session: Session, contribution: Contribution, current_user: User) -> Contribution:
    """DRAFT or REJECTED -> SUBMITTED. Allowed for owning department coordinator or admin."""
    if not _user_can_access_contribution(current_user, contribution):
        raise ValueError("You are not allowed to access this contribution.")
    if current_user.role == UserRole.DEPARTMENT_COORDINATOR and contribution.department_id != current_user.department_id:
        raise ValueError("You are not allowed to submit this contribution.")
    if contribution.status not in (ContributionStatus.DRAFT, ContributionStatus.REJECTED):
        raise ValueError("Only draft or rejected contributions can be submitted.")
    contribution.status = ContributionStatus.SUBMITTED
    session.add(contribution)
    session.commit()
    session.refresh(contribution)
    return contribution


def approve_contribution(
    session: Session,
    contribution: Contribution,
    admin_user: User,
    approval_notes: str | None = None,
) -> Contribution:
    """Admin only. SUBMITTED or UNDER_REVIEW -> APPROVED. Set approved_by_user_id and notes."""
    if admin_user.role != UserRole.ADMIN:
        raise ValueError("Admin access required.")
    if contribution.status not in (ContributionStatus.SUBMITTED, ContributionStatus.UNDER_REVIEW):
        raise ValueError("Only submitted contributions can be approved.")
    contribution.status = ContributionStatus.APPROVED
    contribution.approved_by_user_id = admin_user.id
    contribution.approval_notes = approval_notes.strip() if approval_notes else None
    session.add(contribution)
    session.commit()
    session.refresh(contribution)
    return contribution


def reject_contribution(
    session: Session,
    contribution: Contribution,
    admin_user: User,
    approval_notes: str | None = None,
) -> Contribution:
    """Admin only. SUBMITTED or UNDER_REVIEW -> REJECTED. Set approved_by_user_id and notes."""
    if admin_user.role != UserRole.ADMIN:
        raise ValueError("Admin access required.")
    if contribution.status not in (ContributionStatus.SUBMITTED, ContributionStatus.UNDER_REVIEW):
        raise ValueError("Only submitted contributions can be rejected.")
    contribution.status = ContributionStatus.REJECTED
    contribution.approved_by_user_id = admin_user.id
    contribution.approval_notes = approval_notes.strip() if approval_notes else None
    session.add(contribution)
    session.commit()
    session.refresh(contribution)
    return contribution
