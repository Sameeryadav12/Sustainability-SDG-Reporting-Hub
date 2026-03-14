"""
Reporting cycle service: list, get, create, update, open, close.
"""

from uuid import UUID

from sqlmodel import Session, select

from app.core.pagination import PAGINATION_LIMIT_DEFAULT, PAGINATION_SKIP_DEFAULT
from app.models.enums import ReportingCycleStatus
from app.models.reporting_cycle import ReportingCycle
from app.schemas.reporting_cycle import ReportingCycleCreate, ReportingCycleUpdate


def list_reporting_cycles(
    session: Session,
    status_filter: ReportingCycleStatus | None = None,
    skip: int = PAGINATION_SKIP_DEFAULT,
    limit: int = PAGINATION_LIMIT_DEFAULT,
) -> list[ReportingCycle]:
    """Return reporting cycles ordered by year desc, then created_at desc. Optional status filter and pagination."""
    statement = (
        select(ReportingCycle)
        .order_by(ReportingCycle.year.desc(), ReportingCycle.created_at.desc())
    )
    if status_filter is not None:
        statement = statement.where(ReportingCycle.status == status_filter)
    statement = statement.offset(skip).limit(limit)
    return list(session.exec(statement).all())


def get_reporting_cycle_by_id(session: Session, cycle_id: UUID) -> ReportingCycle | None:
    """Return reporting cycle by id or None."""
    return session.get(ReportingCycle, cycle_id)


def _get_open_cycle(session: Session) -> ReportingCycle | None:
    """Return the currently open reporting cycle, if any."""
    statement = select(ReportingCycle).where(ReportingCycle.status == ReportingCycleStatus.OPEN)
    return session.exec(statement).first()


def create_reporting_cycle(session: Session, data: ReportingCycleCreate) -> ReportingCycle:
    """
    Create a new reporting cycle. Status is set to DRAFT.
    in_scope_sdgs is stored sorted and unique (validated in schema as 1–17, non-empty).
    """
    cycle = ReportingCycle(
        name=data.name.strip(),
        year=data.year,
        start_date=data.start_date,
        end_date=data.end_date,
        status=ReportingCycleStatus.DRAFT,
        description=data.description.strip() if data.description else None,
        in_scope_sdgs=sorted(set(data.in_scope_sdgs)),
    )
    session.add(cycle)
    session.commit()
    session.refresh(cycle)
    return cycle


def update_reporting_cycle(
    session: Session,
    cycle: ReportingCycle,
    data: ReportingCycleUpdate,
) -> ReportingCycle:
    """
    Partially update a reporting cycle. If dates are updated, validate end >= start
    (schema handles when both provided; if only one is updated we validate against existing).
    """
    if data.name is not None:
        cycle.name = data.name.strip()
    if data.year is not None:
        cycle.year = data.year
    if data.start_date is not None:
        cycle.start_date = data.start_date
    if data.end_date is not None:
        cycle.end_date = data.end_date
    if data.description is not None:
        cycle.description = data.description.strip() or None
    if data.in_scope_sdgs is not None:
        cycle.in_scope_sdgs = sorted(set(data.in_scope_sdgs))

    # Validate date order after any date change
    if cycle.end_date < cycle.start_date:
        raise ValueError("end_date must not be earlier than start_date.")

    session.add(cycle)
    session.commit()
    session.refresh(cycle)
    return cycle


def open_reporting_cycle(session: Session, cycle: ReportingCycle) -> ReportingCycle:
    """
    Move cycle from DRAFT to OPEN. Only one cycle may be OPEN at a time.
    Raises ValueError if another cycle is already OPEN or if cycle is not DRAFT.
    """
    if cycle.status == ReportingCycleStatus.OPEN:
        raise ValueError("Reporting cycle is already open.")
    if cycle.status != ReportingCycleStatus.DRAFT:
        raise ValueError(
            "Only a draft reporting cycle can be opened. "
            "Current status: {}.".format(cycle.status.value)
        )
    other_open = _get_open_cycle(session)
    if other_open is not None:
        raise ValueError(
            "Another reporting cycle is already open. Close it before opening a new one."
        )
    cycle.status = ReportingCycleStatus.OPEN
    session.add(cycle)
    session.commit()
    session.refresh(cycle)
    return cycle


def close_reporting_cycle(session: Session, cycle: ReportingCycle) -> ReportingCycle:
    """
    Move cycle from OPEN to CLOSED. If already closed, no-op or clear error.
    """
    if cycle.status == ReportingCycleStatus.CLOSED:
        raise ValueError("Reporting cycle is already closed.")
    if cycle.status != ReportingCycleStatus.OPEN:
        raise ValueError("Reporting cycle is not open and cannot be closed.")
    cycle.status = ReportingCycleStatus.CLOSED
    session.add(cycle)
    session.commit()
    session.refresh(cycle)
    return cycle
