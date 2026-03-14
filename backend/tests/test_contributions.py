"""
Contribution endpoints and service tests.

- 401 when unauthenticated for all endpoints.
- Schema validation (title, description, primary_sdg_id, secondary_sdg_ids, dates).
- Service: create (admin, coordinator), access rules, submit, approve, reject.
"""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel import SQLModel

from app.main import app
from app.models.contribution import Contribution
from app.models.department import Department
from app.models.enums import (
    ContributionStatus,
    ContributionType,
    DepartmentType,
    ReportingCycleStatus,
    UserRole,
)
from app.models.reporting_cycle import ReportingCycle
from app.models.sdg import SDG
from app.models.user import User
from app.schemas.contribution import ContributionCreate, ContributionUpdate
from app.services.contribution_service import (
    _user_can_access_contribution,
    approve_contribution,
    create_contribution,
    list_contributions,
    reject_contribution,
    submit_contribution,
    update_contribution,
)
from app.core.security import hash_password
from sqlmodel import select

client = TestClient(app)


# --- Endpoint: unauthenticated returns 401 ---


def test_list_contributions_without_auth_returns_401() -> None:
    response = client.get("/api/v1/contributions")
    assert response.status_code == 401


def test_get_contribution_without_auth_returns_401() -> None:
    response = client.get(f"/api/v1/contributions/{uuid4()}")
    assert response.status_code == 401


def test_create_contribution_without_auth_returns_401() -> None:
    response = client.post(
        f"/api/v1/reporting-cycles/{uuid4()}/contributions",
        json={
            "title": "Test Contribution",
            "type": "RESEARCH",
            "description": "At least ten chars here.",
            "primary_sdg_id": 4,
        },
    )
    assert response.status_code == 401


def test_patch_contribution_without_auth_returns_401() -> None:
    response = client.patch(
        f"/api/v1/contributions/{uuid4()}",
        json={"title": "Updated"},
    )
    assert response.status_code == 401


def test_submit_contribution_without_auth_returns_401() -> None:
    response = client.post(f"/api/v1/contributions/{uuid4()}/submit")
    assert response.status_code == 401


def test_approve_contribution_without_auth_returns_401() -> None:
    response = client.post(
        f"/api/v1/contributions/{uuid4()}/approve",
        json={"approval_notes": "Approved."},
    )
    assert response.status_code == 401


def test_reject_contribution_without_auth_returns_401() -> None:
    response = client.post(
        f"/api/v1/contributions/{uuid4()}/reject",
        json={"approval_notes": "Rejected."},
    )
    assert response.status_code == 401


# --- Schema validation ---


def test_contribution_create_title_too_short() -> None:
    with pytest.raises(ValueError, match="at least 3"):
        ContributionCreate(
            title="Ab",
            type=ContributionType.RESEARCH,
            description="At least ten characters here.",
            primary_sdg_id=4,
        )


def test_contribution_create_primary_sdg_in_secondary_rejected() -> None:
    with pytest.raises(ValueError, match="must not appear in secondary"):
        ContributionCreate(
            title="Valid Title Here",
            type=ContributionType.RESEARCH,
            description="At least ten characters here.",
            primary_sdg_id=4,
            secondary_sdg_ids=[4, 5],
        )


def test_contribution_create_end_date_before_start_rejected() -> None:
    with pytest.raises(ValueError, match="end_date must not be earlier"):
        ContributionCreate(
            title="Valid Title Here",
            type=ContributionType.RESEARCH,
            description="At least ten characters here.",
            primary_sdg_id=4,
            start_date=date(2025, 12, 1),
            end_date=date(2025, 1, 1),
        )


def test_contribution_create_valid() -> None:
    data = ContributionCreate(
        title="Valid Title Here",
        type=ContributionType.TEACHING,
        description="At least ten characters here.",
        primary_sdg_id=4,
        secondary_sdg_ids=[5, 9],
    )
    assert data.primary_sdg_id == 4
    assert data.secondary_sdg_ids == [5, 9]


# --- Service layer: access and workflow (in-memory SQLite with required tables) ---


@pytest.fixture
def contribution_db_session() -> Session:
    """Session with SDG, Department, User, ReportingCycle, Contribution tables and seed data."""
    engine = create_engine("sqlite:///:memory:")
    tables = [
        SDG.__table__,
        Department.__table__,
        User.__table__,
        ReportingCycle.__table__,
        Contribution.__table__,
    ]
    for t in tables:
        t.create(engine, checkfirst=True)
    with Session(engine) as session:
        # Seed SDG id=1 (required for primary_sdg_id FK)
        session.add(SDG(id=1, name="No Poverty", description="End poverty in all its forms."))
        session.commit()
        dept = Department(
            id=uuid4(),
            name="Faculty of Science",
            code="SCI",
            type=DepartmentType.ACADEMIC,
        )
        session.add(dept)
        session.flush()
        admin = User(
            id=uuid4(),
            name="Admin",
            email="admin@test.com",
            password_hash=hash_password("StrongPass1!"),
            role=UserRole.ADMIN,
            department_id=None,
            is_active=True,
        )
        session.add(admin)
        session.flush()
        coordinator = User(
            id=uuid4(),
            name="Coord",
            email="coord@test.com",
            password_hash=hash_password("StrongPass1!"),
            role=UserRole.DEPARTMENT_COORDINATOR,
            department_id=dept.id,
            is_active=True,
        )
        session.add(coordinator)
        session.flush()
        cycle = ReportingCycle(
            id=uuid4(),
            name="2025",
            year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status=ReportingCycleStatus.OPEN,
            in_scope_sdgs=[1, 4, 5],
        )
        session.add(cycle)
        session.commit()
        session.refresh(dept)
        session.refresh(admin)
        session.refresh(coordinator)
        session.refresh(cycle)
        yield session


def test_service_admin_can_create_contribution(contribution_db_session: Session) -> None:
    cycle = contribution_db_session.exec(
        select(ReportingCycle).where(ReportingCycle.status == ReportingCycleStatus.OPEN)
    ).first()
    admin = contribution_db_session.exec(
        select(User).where(User.role == UserRole.ADMIN)
    ).first()
    dept = contribution_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="Admin Contribution",
        type=ContributionType.RESEARCH,
        description="At least ten characters here.",
        primary_sdg_id=1,
        department_id=dept.id,
    )
    c = create_contribution(contribution_db_session, cycle.id, data, admin)
    assert c.status == ContributionStatus.DRAFT
    assert c.created_by_user_id == admin.id


def test_service_coordinator_can_create_for_own_department(contribution_db_session: Session) -> None:
    cycle = contribution_db_session.exec(
        select(ReportingCycle).where(ReportingCycle.status == ReportingCycleStatus.OPEN)
    ).first()
    coord = contribution_db_session.exec(
        select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)
    ).first()
    data = ContributionCreate(
        title="Coord Contribution",
        type=ContributionType.TEACHING,
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(contribution_db_session, cycle.id, data, coord)
    assert c.department_id == coord.department_id


def test_service_coordinator_cannot_create_for_other_department(contribution_db_session: Session) -> None:
    cycle = contribution_db_session.exec(
        select(ReportingCycle).where(ReportingCycle.status == ReportingCycleStatus.OPEN)
    ).first()
    coord = contribution_db_session.exec(
        select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)
    ).first()
    other_dept_id = uuid4()
    data = ContributionCreate(
        title="Other Dept",
        type=ContributionType.RESEARCH,
        description="At least ten characters here.",
        primary_sdg_id=1,
        department_id=other_dept_id,
    )
    with pytest.raises(ValueError, match="another department"):
        create_contribution(contribution_db_session, cycle.id, data, coord)


def test_service_cannot_create_in_non_open_cycle(contribution_db_session: Session) -> None:
    # Create a DRAFT cycle
    draft_cycle = ReportingCycle(
        id=uuid4(),
        name="2026",
        year=2026,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=ReportingCycleStatus.DRAFT,
        in_scope_sdgs=[1],
    )
    contribution_db_session.add(draft_cycle)
    contribution_db_session.commit()
    contribution_db_session.refresh(draft_cycle)
    admin = contribution_db_session.exec(
        select(User).where(User.role == UserRole.ADMIN)
    ).first()
    dept = contribution_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="Draft Cycle Contribution",
        type=ContributionType.RESEARCH,
        description="At least ten characters here.",
        primary_sdg_id=1,
        department_id=dept.id,
    )
    with pytest.raises(ValueError, match="open reporting cycle"):
        create_contribution(contribution_db_session, draft_cycle.id, data, admin)


def test_service_list_filters_by_coordinator_department(contribution_db_session: Session) -> None:
    cycle = contribution_db_session.exec(select(ReportingCycle)).first()
    admin = contribution_db_session.exec(
        select(User).where(User.role == UserRole.ADMIN)
    ).first()
    dept = contribution_db_session.exec(select(Department)).first()
    coord = contribution_db_session.exec(
        select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)
    ).first()
    data = ContributionCreate(
        title="Only One",
        type=ContributionType.RESEARCH,
        description="At least ten characters here.",
        primary_sdg_id=1,
        department_id=dept.id,
    )
    create_contribution(contribution_db_session, cycle.id, data, admin)
    all_list = list_contributions(contribution_db_session, admin)
    coord_list = list_contributions(contribution_db_session, coord)
    assert len(all_list) >= 1
    assert len(coord_list) >= 1  # coordinator sees own dept's


def test_service_submit_changes_draft_to_submitted(contribution_db_session: Session) -> None:
    coord = contribution_db_session.exec(
        select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)
    ).first()
    cycle = contribution_db_session.exec(select(ReportingCycle)).first()
    data = ContributionCreate(
        title="To Submit",
        type=ContributionType.RESEARCH,
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(contribution_db_session, cycle.id, data, coord)
    assert c.status == ContributionStatus.DRAFT
    c = submit_contribution(contribution_db_session, c, coord)
    assert c.status == ContributionStatus.SUBMITTED


def test_service_admin_can_approve_submitted(contribution_db_session: Session) -> None:
    coord = contribution_db_session.exec(
        select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)
    ).first()
    admin = contribution_db_session.exec(
        select(User).where(User.role == UserRole.ADMIN)
    ).first()
    cycle = contribution_db_session.exec(select(ReportingCycle)).first()
    data = ContributionCreate(
        title="To Approve",
        type=ContributionType.RESEARCH,
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(contribution_db_session, cycle.id, data, coord)
    submit_contribution(contribution_db_session, c, coord)
    contribution_db_session.refresh(c)
    c = approve_contribution(contribution_db_session, c, admin, approval_notes="Looks good.")
    assert c.status == ContributionStatus.APPROVED
    assert c.approved_by_user_id == admin.id
    assert c.approval_notes == "Looks good."


def test_service_admin_can_reject_submitted(contribution_db_session: Session) -> None:
    coord = contribution_db_session.exec(
        select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)
    ).first()
    admin = contribution_db_session.exec(
        select(User).where(User.role == UserRole.ADMIN)
    ).first()
    cycle = contribution_db_session.exec(select(ReportingCycle)).first()
    data = ContributionCreate(
        title="To Reject",
        type=ContributionType.RESEARCH,
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(contribution_db_session, cycle.id, data, coord)
    submit_contribution(contribution_db_session, c, coord)
    contribution_db_session.refresh(c)
    c = reject_contribution(contribution_db_session, c, admin, approval_notes="Please revise.")
    assert c.status == ContributionStatus.REJECTED
    assert c.approved_by_user_id == admin.id


def test_service_approved_contribution_cannot_be_edited_by_non_admin(contribution_db_session: Session) -> None:
    coord = contribution_db_session.exec(
        select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)
    ).first()
    admin = contribution_db_session.exec(
        select(User).where(User.role == UserRole.ADMIN)
    ).first()
    cycle = contribution_db_session.exec(select(ReportingCycle)).first()
    data = ContributionCreate(
        title="Approved One",
        type=ContributionType.RESEARCH,
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(contribution_db_session, cycle.id, data, coord)
    submit_contribution(contribution_db_session, c, coord)
    contribution_db_session.refresh(c)
    approve_contribution(contribution_db_session, c, admin)
    contribution_db_session.refresh(c)
    update_data = ContributionUpdate(title="Trying to Change")
    with pytest.raises(ValueError, match="cannot be edited"):
        update_contribution(contribution_db_session, c, update_data, coord)


def test_user_can_access_contribution_admin_sees_any() -> None:
    """Unit test for access: admin can access any contribution (no DB needed for this logic)."""
    admin = User(
        id=uuid4(),
        name="A",
        email="a@b.com",
        password_hash="x",
        role=UserRole.ADMIN,
        department_id=None,
        is_active=True,
    )
    c = Contribution(
        id=uuid4(),
        reporting_cycle_id=uuid4(),
        department_id=uuid4(),
        title="T",
        type=ContributionType.RESEARCH,
        description="Desc",
        primary_sdg_id=1,
        status=ContributionStatus.DRAFT,
        created_by_user_id=uuid4(),
    )
    assert _user_can_access_contribution(admin, c) is True
