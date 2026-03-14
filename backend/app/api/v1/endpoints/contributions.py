"""
Contribution endpoints: list, get, create (under reporting cycle), update, submit, approve, reject.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import inspect as orm_inspect

from app.api.deps import AdminUserDep, CurrentUserDep
from app.core.http_errors import raise_403, raise_404
from app.core.pagination import (
    PAGINATION_LIMIT_DEFAULT,
    PAGINATION_LIMIT_MAX,
    PAGINATION_SKIP_DEFAULT,
    validate_pagination,
)
from app.db.session import SessionDep
from app.models.enums import ContributionStatus, ContributionType
from app.schemas.contribution import (
    ContributionApproveRequest,
    ContributionCreate,
    ContributionListItem,
    ContributionRead,
    ContributionRejectRequest,
    ContributionUpdate,
)
from app.services.audit_service import log_action
from app.services.contribution_service import (
    _user_can_access_contribution,
    approve_contribution,
    create_contribution,
    get_contribution_by_id,
    get_contribution_by_id_with_relations,
    list_contributions,
    reject_contribution,
    submit_contribution,
    update_contribution,
)

router = APIRouter(tags=["Contributions"])


@router.get("/contributions", response_model=list[ContributionListItem])
def list_contributions_endpoint(
    session: SessionDep,
    current_user: CurrentUserDep,
    reporting_cycle_id: UUID | None = Query(None),
    department_id: UUID | None = Query(None),
    sdg_id: int | None = Query(None),
    status_filter: ContributionStatus | None = Query(None, alias="status"),
    type_filter: ContributionType | None = Query(None, alias="type"),
    skip: int = Query(PAGINATION_SKIP_DEFAULT, ge=0, description="Number of records to skip"),
    limit: int = Query(PAGINATION_LIMIT_DEFAULT, ge=1, le=PAGINATION_LIMIT_MAX, description="Max records to return"),
) -> list[ContributionListItem]:
    """List contributions (authenticated). Filters: reporting_cycle_id, department_id, sdg_id, status, type. Access: admin/viewer all; coordinator own department only. Supports skip/limit pagination."""
    try:
        validate_pagination(skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    items = list_contributions(
        session,
        current_user,
        reporting_cycle_id=reporting_cycle_id,
        department_id=department_id,
        sdg_id=sdg_id,
        status=status_filter,
        type_filter=type_filter.value if type_filter else None,
        skip=skip,
        limit=limit,
    )
    result = []
    for c in items:
        result.append(
            ContributionListItem(
                id=c.id,
                title=c.title,
                type=c.type,
                status=c.status,
                primary_sdg_id=c.primary_sdg_id,
                primary_sdg=c.primary_sdg_id,
                department_id=c.department_id,
                department_name=c.department.name if c.department else None,
                reporting_cycle_id=c.reporting_cycle_id,
                reporting_cycle_name=c.reporting_cycle.name if c.reporting_cycle else None,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
        )
    return result


@router.get("/contributions/{contribution_id}", response_model=ContributionRead)
def get_contribution_endpoint(
    contribution_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ContributionRead:
    """Get a contribution by id (authenticated). Access rules apply; 404 if not found or no access."""
    try:
        contribution = get_contribution_by_id_with_relations(session, contribution_id)
        if contribution is None:
            raise_404("Contribution not found.")
        if not _user_can_access_contribution(current_user, contribution):
            raise_403("You are not allowed to access this contribution.")
        return _contribution_to_read(contribution)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load contribution: {e!s}",
        ) from e


def _contribution_to_read(contribution) -> ContributionRead:
    """Build ContributionRead from scalar attributes and relation names. Avoids model_validate so primary_sdg (relationship) is not confused with primary_sdg (int)."""
    data = {
        "id": contribution.id,
        "reporting_cycle_id": contribution.reporting_cycle_id,
        "department_id": contribution.department_id,
        "title": contribution.title,
        "type": contribution.type,
        "description": contribution.description,
        "primary_sdg_id": contribution.primary_sdg_id,
        "primary_sdg": contribution.primary_sdg_id,
        "secondary_sdg_ids": contribution.secondary_sdg_ids,
        "start_date": contribution.start_date,
        "end_date": contribution.end_date,
        "status": contribution.status,
        "created_by_user_id": contribution.created_by_user_id,
        "approved_by_user_id": contribution.approved_by_user_id,
        "approval_notes": contribution.approval_notes,
        "created_at": contribution.created_at,
        "updated_at": contribution.updated_at,
        "reporting_cycle_name": None,
        "department_name": None,
    }
    try:
        insp = orm_inspect(contribution)
        unloaded = getattr(insp, "unloaded", set()) or set()
        if "department" not in unloaded:
            dept = getattr(contribution, "department", None)
            if dept is not None and hasattr(dept, "name"):
                data["department_name"] = dept.name
        if "reporting_cycle" not in unloaded:
            cycle = getattr(contribution, "reporting_cycle", None)
            if cycle is not None and hasattr(cycle, "name"):
                data["reporting_cycle_name"] = cycle.name
    except Exception:
        pass
    return ContributionRead(**data)


@router.post(
    "/reporting-cycles/{cycle_id}/contributions",
    response_model=ContributionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contribution_endpoint(
    cycle_id: UUID,
    data: ContributionCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ContributionRead:
    """Create a contribution in the given reporting cycle (authenticated). Cycle must be OPEN. Coordinator: own department only; admin: any department."""
    try:
        contribution = create_contribution(session, cycle_id, data, current_user)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Create failed: {e!s}") from e
    log_action(
        session,
        current_user.id,
        "contribution_created",
        "contribution",
        str(contribution.id),
        metadata_json={"reporting_cycle_id": str(contribution.reporting_cycle_id), "status": contribution.status.value},
    )
    # Re-load with relations to avoid lazy load after commit (prevents "Unable to connect" on client). Expunge so we get a fresh load.
    _id = contribution.id
    session.expunge(contribution)
    contribution_with_relations = get_contribution_by_id_with_relations(session, _id)
    return _contribution_to_read(contribution_with_relations or contribution)


@router.patch("/contributions/{contribution_id}", response_model=ContributionRead)
def update_contribution_endpoint(
    contribution_id: UUID,
    data: ContributionUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ContributionRead:
    """Update a contribution (authenticated). Coordinator: own department only and not approved; admin: any."""
    contribution = get_contribution_by_id(session, contribution_id)
    if contribution is None:
        raise_404("Contribution not found.")
    try:
        contribution = update_contribution(session, contribution, data, current_user)
    except ValueError as e:
        msg = str(e)
        if "not allowed" in msg.lower() or "cannot be edited" in msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Update failed: {e!s}") from e
    log_action(
        session,
        current_user.id,
        "contribution_updated",
        "contribution",
        str(contribution.id),
        metadata_json={"status": contribution.status.value},
    )
    _id = contribution.id
    session.expunge(contribution)
    contribution_with_relations = get_contribution_by_id_with_relations(session, _id)
    return _contribution_to_read(contribution_with_relations or contribution)


@router.post("/contributions/{contribution_id}/submit", response_model=ContributionRead)
def submit_contribution_endpoint(
    contribution_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ContributionRead:
    """Submit a contribution (DRAFT or REJECTED -> SUBMITTED). Coordinator (own dept) or admin."""
    contribution = get_contribution_by_id(session, contribution_id)
    if contribution is None:
        raise_404("Contribution not found.")
    try:
        contribution = submit_contribution(session, contribution, current_user)
    except ValueError as e:
        msg = str(e)
        if "not allowed" in msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "contribution_submitted",
        "contribution",
        str(contribution.id),
        metadata_json={"status": contribution.status.value},
    )
    _id = contribution.id
    session.expunge(contribution)
    contribution_with_relations = get_contribution_by_id_with_relations(session, _id)
    return _contribution_to_read(contribution_with_relations or contribution)


@router.post("/contributions/{contribution_id}/approve", response_model=ContributionRead)
def approve_contribution_endpoint(
    contribution_id: UUID,
    session: SessionDep,
    current_user: AdminUserDep,
    body: ContributionApproveRequest | None = None,
) -> ContributionRead:
    """Approve a contribution (admin only). SUBMITTED or UNDER_REVIEW -> APPROVED."""
    contribution = get_contribution_by_id(session, contribution_id)
    if contribution is None:
        raise_404("Contribution not found.")
    try:
        contribution = approve_contribution(
            session,
            contribution,
            current_user,
            approval_notes=body.approval_notes if body else None,
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "contribution_approved",
        "contribution",
        str(contribution.id),
        metadata_json={"status": contribution.status.value},
    )
    _id = contribution.id
    session.expunge(contribution)
    contribution_with_relations = get_contribution_by_id_with_relations(session, _id)
    return _contribution_to_read(contribution_with_relations or contribution)


@router.post("/contributions/{contribution_id}/reject", response_model=ContributionRead)
def reject_contribution_endpoint(
    contribution_id: UUID,
    session: SessionDep,
    current_user: AdminUserDep,
    body: ContributionRejectRequest | None = None,
) -> ContributionRead:
    """Reject a contribution (admin only). SUBMITTED or UNDER_REVIEW -> REJECTED. Approval notes encouraged."""
    contribution = get_contribution_by_id(session, contribution_id)
    if contribution is None:
        raise_404("Contribution not found.")
    try:
        contribution = reject_contribution(
            session,
            contribution,
            current_user,
            approval_notes=body.approval_notes if body else None,
        )
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "contribution_rejected",
        "contribution",
        str(contribution.id),
        metadata_json={"status": contribution.status.value},
    )
    _id = contribution.id
    session.expunge(contribution)
    contribution_with_relations = get_contribution_by_id_with_relations(session, _id)
    return _contribution_to_read(contribution_with_relations or contribution)
