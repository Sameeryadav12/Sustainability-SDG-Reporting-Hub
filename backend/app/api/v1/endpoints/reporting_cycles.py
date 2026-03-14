"""
Reporting cycle endpoints: list, get, create (admin), patch (admin), open (admin), close (admin).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import AdminUserDep, CurrentUserDep
from app.core.http_errors import raise_404
from app.core.pagination import (
    PAGINATION_LIMIT_DEFAULT,
    PAGINATION_LIMIT_MAX,
    PAGINATION_SKIP_DEFAULT,
    validate_pagination,
)
from app.db.session import SessionDep
from app.models.enums import ReportingCycleStatus
from app.schemas.reporting_cycle import (
    ReportingCycleCreate,
    ReportingCycleListItem,
    ReportingCycleRead,
    ReportingCycleStatusActionResponse,
    ReportingCycleUpdate,
)
from app.services.audit_service import log_action
from app.services.reporting_cycle_service import (
    close_reporting_cycle,
    create_reporting_cycle,
    get_reporting_cycle_by_id,
    list_reporting_cycles,
    open_reporting_cycle,
    update_reporting_cycle,
)

router = APIRouter(prefix="/reporting-cycles", tags=["Reporting Cycles"])


@router.get("", response_model=list[ReportingCycleListItem])
def list_reporting_cycles_endpoint(
    session: SessionDep,
    current_user: CurrentUserDep,
    status_filter: ReportingCycleStatus | None = Query(None, alias="status"),
    skip: int = Query(PAGINATION_SKIP_DEFAULT, ge=0, description="Number of records to skip"),
    limit: int = Query(PAGINATION_LIMIT_DEFAULT, ge=1, le=PAGINATION_LIMIT_MAX, description="Max records to return"),
) -> list[ReportingCycleListItem]:
    """List reporting cycles (authenticated). Ordered by year desc, created_at desc. Optional ?status=OPEN. Supports skip/limit pagination."""
    try:
        validate_pagination(skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    cycles = list_reporting_cycles(session, status_filter=status_filter, skip=skip, limit=limit)
    return [ReportingCycleListItem.model_validate(c) for c in cycles]


@router.get("/{cycle_id}", response_model=ReportingCycleRead)
def get_reporting_cycle_endpoint(
    cycle_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ReportingCycleRead:
    """Get a reporting cycle by id (authenticated). Returns 404 if not found."""
    cycle = get_reporting_cycle_by_id(session, cycle_id)
    if cycle is None:
        raise_404("Reporting cycle not found.")
    return ReportingCycleRead.model_validate(cycle)


@router.post("", response_model=ReportingCycleRead, status_code=status.HTTP_201_CREATED)
def create_reporting_cycle_endpoint(
    data: ReportingCycleCreate,
    session: SessionDep,
    current_user: AdminUserDep,
) -> ReportingCycleRead:
    """Create a new reporting cycle (admin only). Created as DRAFT."""
    try:
        cycle = create_reporting_cycle(session, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    log_action(
        session,
        current_user.id,
        "reporting_cycle_created",
        "reporting_cycle",
        str(cycle.id),
        metadata_json={"name": cycle.name, "year": cycle.year},
    )
    return ReportingCycleRead.model_validate(cycle)


@router.patch("/{cycle_id}", response_model=ReportingCycleRead)
def update_reporting_cycle_endpoint(
    cycle_id: UUID,
    data: ReportingCycleUpdate,
    session: SessionDep,
    current_user: AdminUserDep,
) -> ReportingCycleRead:
    """Update a reporting cycle (admin only). Partial update; dates and SDGs validated."""
    cycle = get_reporting_cycle_by_id(session, cycle_id)
    if cycle is None:
        raise_404("Reporting cycle not found.")
    try:
        cycle = update_reporting_cycle(session, cycle, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    log_action(
        session,
        current_user.id,
        "reporting_cycle_updated",
        "reporting_cycle",
        str(cycle.id),
        metadata_json={"name": cycle.name},
    )
    return ReportingCycleRead.model_validate(cycle)


@router.post(
    "/{cycle_id}/open",
    response_model=ReportingCycleStatusActionResponse,
)
def open_reporting_cycle_endpoint(
    cycle_id: UUID,
    session: SessionDep,
    current_user: AdminUserDep,
) -> ReportingCycleStatusActionResponse:
    """Open a reporting cycle (admin only). Only one cycle may be OPEN at a time. DRAFT -> OPEN."""
    cycle = get_reporting_cycle_by_id(session, cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporting cycle not found.",
        )
    try:
        cycle = open_reporting_cycle(session, cycle)
    except ValueError as e:
        msg = str(e)
        if "already open" in msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        if "another reporting cycle" in msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "reporting_cycle_opened",
        "reporting_cycle",
        str(cycle.id),
        metadata_json={"reporting_cycle_id": str(cycle.id)},
    )
    return ReportingCycleStatusActionResponse(
        id=cycle.id,
        status=cycle.status,
        message="Reporting cycle is now open.",
    )


@router.post(
    "/{cycle_id}/close",
    response_model=ReportingCycleStatusActionResponse,
)
def close_reporting_cycle_endpoint(
    cycle_id: UUID,
    session: SessionDep,
    current_user: AdminUserDep,
) -> ReportingCycleStatusActionResponse:
    """Close a reporting cycle (admin only). OPEN -> CLOSED."""
    cycle = get_reporting_cycle_by_id(session, cycle_id)
    if cycle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reporting cycle not found.",
        )
    try:
        cycle = close_reporting_cycle(session, cycle)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "reporting_cycle_closed",
        "reporting_cycle",
        str(cycle.id),
        metadata_json={"reporting_cycle_id": str(cycle.id)},
    )
    return ReportingCycleStatusActionResponse(
        id=cycle.id,
        status=cycle.status,
        message="Reporting cycle is now closed.",
    )
