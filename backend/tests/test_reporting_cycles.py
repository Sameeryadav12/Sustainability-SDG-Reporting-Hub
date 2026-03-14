"""
Reporting cycle endpoints and service tests.

- 401 when unauthenticated for all endpoints.
- Validation: invalid SDG list, end_date before start_date.
- Service: open/close workflow, only one open at a time.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel import SQLModel

from app.main import app
from app.models.enums import ReportingCycleStatus
from app.models.reporting_cycle import ReportingCycle
from app.schemas.reporting_cycle import ReportingCycleCreate, ReportingCycleUpdate
from app.services.reporting_cycle_service import (
    close_reporting_cycle,
    create_reporting_cycle,
    get_reporting_cycle_by_id,
    list_reporting_cycles,
    open_reporting_cycle,
    update_reporting_cycle,
)

client = TestClient(app)


# --- Endpoint: unauthenticated returns 401 ---


def test_list_reporting_cycles_without_auth_returns_401() -> None:
    response = client.get("/api/v1/reporting-cycles")
    assert response.status_code == 401


def test_get_reporting_cycle_without_auth_returns_401() -> None:
    response = client.get(
        "/api/v1/reporting-cycles/00000000-0000-0000-0000-000000000001"
    )
    assert response.status_code == 401


def test_create_reporting_cycle_without_auth_returns_401() -> None:
    response = client.post(
        "/api/v1/reporting-cycles",
        json={
            "name": "Report 2025",
            "year": 2025,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "in_scope_sdgs": [4, 5, 9],
        },
    )
    assert response.status_code == 401


def test_patch_reporting_cycle_without_auth_returns_401() -> None:
    response = client.patch(
        "/api/v1/reporting-cycles/00000000-0000-0000-0000-000000000001",
        json={"name": "Updated"},
    )
    assert response.status_code == 401


def test_open_reporting_cycle_without_auth_returns_401() -> None:
    response = client.post(
        "/api/v1/reporting-cycles/00000000-0000-0000-0000-000000000001/open"
    )
    assert response.status_code == 401


def test_close_reporting_cycle_without_auth_returns_401() -> None:
    response = client.post(
        "/api/v1/reporting-cycles/00000000-0000-0000-0000-000000000001/close"
    )
    assert response.status_code == 401


# --- Schema validation ---


def test_reporting_cycle_create_in_scope_sdgs_empty_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises((ValidationError, ValueError), match="must not be empty"):
        ReportingCycleCreate(
            name="Report 2025",
            year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            in_scope_sdgs=[],
        )


def test_reporting_cycle_create_invalid_sdg_id_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises((ValidationError, ValueError), match="1 to 17"):
        ReportingCycleCreate(
            name="Report 2025",
            year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            in_scope_sdgs=[4, 18],
        )


def test_reporting_cycle_create_end_date_before_start_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises((ValidationError, ValueError), match="end_date must not be earlier"):
        ReportingCycleCreate(
            name="Report 2025",
            year=2025,
            start_date=date(2025, 12, 31),
            end_date=date(2025, 1, 1),
            in_scope_sdgs=[4, 5],
        )


def test_reporting_cycle_create_valid_sets_draft() -> None:
    data = ReportingCycleCreate(
        name="Report 2025",
        year=2025,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        in_scope_sdgs=[4, 5, 9],
    )
    assert data.name == "Report 2025"
    assert data.in_scope_sdgs == [4, 5, 9]


# --- Service layer (in-memory SQLite) ---


@pytest.fixture
def reporting_cycle_session() -> Session:
    """Session with only ReportingCycle table for service tests."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine, tables=[ReportingCycle.__table__])
    with Session(engine) as session:
        yield session


def test_service_create_reporting_cycle(reporting_cycle_session: Session) -> None:
    data = ReportingCycleCreate(
        name="Sustainability Report 2025",
        year=2025,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        description="Annual cycle",
        in_scope_sdgs=[4, 5, 9, 11],
    )
    cycle = create_reporting_cycle(reporting_cycle_session, data)
    assert cycle.id is not None
    assert cycle.status == ReportingCycleStatus.DRAFT
    assert cycle.in_scope_sdgs == [4, 5, 9, 11]


def test_service_open_cycle(reporting_cycle_session: Session) -> None:
    data = ReportingCycleCreate(
        name="Report 2025",
        year=2025,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        in_scope_sdgs=[4, 5],
    )
    cycle = create_reporting_cycle(reporting_cycle_session, data)
    opened = open_reporting_cycle(reporting_cycle_session, cycle)
    assert opened.status == ReportingCycleStatus.OPEN


def test_service_second_open_rejected(reporting_cycle_session: Session) -> None:
    data1 = ReportingCycleCreate(
        name="Report 2025",
        year=2025,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        in_scope_sdgs=[4],
    )
    data2 = ReportingCycleCreate(
        name="Report 2026",
        year=2026,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        in_scope_sdgs=[5],
    )
    c1 = create_reporting_cycle(reporting_cycle_session, data1)
    c2 = create_reporting_cycle(reporting_cycle_session, data2)
    open_reporting_cycle(reporting_cycle_session, c1)
    with pytest.raises(ValueError, match="Another reporting cycle is already open"):
        open_reporting_cycle(reporting_cycle_session, c2)


def test_service_close_open_cycle(reporting_cycle_session: Session) -> None:
    data = ReportingCycleCreate(
        name="Report 2025",
        year=2025,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        in_scope_sdgs=[4],
    )
    cycle = create_reporting_cycle(reporting_cycle_session, data)
    open_reporting_cycle(reporting_cycle_session, cycle)
    closed = close_reporting_cycle(reporting_cycle_session, cycle)
    assert closed.status == ReportingCycleStatus.CLOSED


def test_service_close_non_open_rejected(reporting_cycle_session: Session) -> None:
    data = ReportingCycleCreate(
        name="Report 2025",
        year=2025,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        in_scope_sdgs=[4],
    )
    cycle = create_reporting_cycle(reporting_cycle_session, data)
    with pytest.raises(ValueError, match="not open and cannot be closed"):
        close_reporting_cycle(reporting_cycle_session, cycle)


def test_service_list_ordered_by_year_desc(reporting_cycle_session: Session) -> None:
    create_reporting_cycle(
        reporting_cycle_session,
        ReportingCycleCreate(
            name="2024",
            year=2024,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            in_scope_sdgs=[1],
        ),
    )
    create_reporting_cycle(
        reporting_cycle_session,
        ReportingCycleCreate(
            name="2025",
            year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            in_scope_sdgs=[1],
        ),
    )
    cycles = list_reporting_cycles(reporting_cycle_session)
    assert len(cycles) == 2
    assert cycles[0].year == 2025
    assert cycles[1].year == 2024


def test_service_update_validates_dates(reporting_cycle_session: Session) -> None:
    """Schema rejects end_date before start_date at construction time."""
    from pydantic import ValidationError

    with pytest.raises((ValidationError, ValueError), match="end_date must not be earlier"):
        ReportingCycleUpdate(
            start_date=date(2025, 12, 31),
            end_date=date(2025, 1, 1),
        )
