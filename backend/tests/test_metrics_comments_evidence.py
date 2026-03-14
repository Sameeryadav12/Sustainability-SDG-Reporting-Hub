"""
Metrics, comments, and evidence endpoints and service tests.

- 401 when unauthenticated.
- Schema validation (metric: at least one of value_number/value_text).
- Service: access rules (coordinator own dept, viewer read-only, admin full).
"""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select
from sqlmodel import SQLModel

from app.main import app
from app.models.comment import Comment
from app.models.contribution import Contribution
from app.models.contribution_metric import ContributionMetric
from app.models.department import Department
from app.models.enums import DepartmentType, ReportingCycleStatus, UserRole
from app.models.evidence_file import EvidenceFile
from app.models.reporting_cycle import ReportingCycle
from app.models.sdg import SDG
from app.models.user import User
from app.schemas.metric import ContributionMetricCreate
from app.schemas.comment import CommentCreate
from app.schemas.evidence import EvidenceFileCreate
from app.services.contribution_service import create_contribution, get_contribution_by_id
from app.services.metric_service import create_metric, delete_metric, list_metrics_for_contribution
from app.services.comment_service import create_comment, list_comments_for_contribution
from app.services.evidence_service import (
    create_evidence_file,
    delete_evidence_file,
    list_evidence_for_contribution,
)
from app.core.security import hash_password
from app.schemas.contribution import ContributionCreate

client = TestClient(app)


# --- 401 unauthenticated ---


def test_list_metrics_without_auth_returns_401() -> None:
    response = client.get(f"/api/v1/contributions/{uuid4()}/metrics")
    assert response.status_code == 401


def test_create_metric_without_auth_returns_401() -> None:
    response = client.post(
        f"/api/v1/contributions/{uuid4()}/metrics",
        json={"name": "Students", "value_number": 100},
    )
    assert response.status_code == 401


def test_delete_metric_without_auth_returns_401() -> None:
    response = client.delete(f"/api/v1/metrics/{uuid4()}")
    assert response.status_code == 401


def test_list_comments_without_auth_returns_401() -> None:
    response = client.get(f"/api/v1/contributions/{uuid4()}/comments")
    assert response.status_code == 401


def test_create_comment_without_auth_returns_401() -> None:
    response = client.post(
        f"/api/v1/contributions/{uuid4()}/comments",
        json={"text": "A short comment here."},
    )
    assert response.status_code == 401


def test_list_evidence_without_auth_returns_401() -> None:
    response = client.get(f"/api/v1/contributions/{uuid4()}/evidence")
    assert response.status_code == 401


def test_create_evidence_without_auth_returns_401() -> None:
    response = client.post(
        f"/api/v1/contributions/{uuid4()}/evidence",
        json={
            "file_name": "doc.pdf",
            "file_url": "https://example.com/doc.pdf",
            "file_type": "pdf",
        },
    )
    assert response.status_code == 401


def test_delete_evidence_without_auth_returns_401() -> None:
    response = client.delete(f"/api/v1/evidence/{uuid4()}")
    assert response.status_code == 401


# --- Schema validation ---


def test_metric_create_rejects_missing_both_value_number_and_value_text() -> None:
    from pydantic import ValidationError
    with pytest.raises((ValidationError, ValueError), match="At least one"):
        ContributionMetricCreate(name="No value", value_number=None, value_text=None)


# --- Service layer (shared fixture with contribution DB) ---


@pytest.fixture
def step6_db_session() -> Session:
    """Session with SDG, Department, User, ReportingCycle, Contribution, ContributionMetric, Comment, EvidenceFile."""
    engine = create_engine("sqlite:///:memory:")
    tables = [
        SDG.__table__,
        Department.__table__,
        User.__table__,
        ReportingCycle.__table__,
        Contribution.__table__,
        ContributionMetric.__table__,
        Comment.__table__,
        EvidenceFile.__table__,
    ]
    for t in tables:
        t.create(engine, checkfirst=True)
    with Session(engine) as session:
        session.add(SDG(id=1, name="No Poverty", description="End poverty."))
        session.commit()
        dept = Department(id=uuid4(), name="Science", code="SCI", type=DepartmentType.ACADEMIC)
        session.add(dept)
        session.flush()
        admin = User(
            id=uuid4(),
            name="Admin",
            email="admin6@test.com",
            password_hash=hash_password("StrongPass1!"),
            role=UserRole.ADMIN,
            department_id=None,
            is_active=True,
        )
        session.add(admin)
        session.flush()
        coord = User(
            id=uuid4(),
            name="Coord",
            email="coord6@test.com",
            password_hash=hash_password("StrongPass1!"),
            role=UserRole.DEPARTMENT_COORDINATOR,
            department_id=dept.id,
            is_active=True,
        )
        session.add(coord)
        session.flush()
        viewer = User(
            id=uuid4(),
            name="Viewer",
            email="viewer6@test.com",
            password_hash=hash_password("StrongPass1!"),
            role=UserRole.VIEWER,
            department_id=None,
            is_active=True,
        )
        session.add(viewer)
        session.flush()
        cycle = ReportingCycle(
            id=uuid4(),
            name="2025",
            year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status=ReportingCycleStatus.OPEN,
            in_scope_sdgs=[1],
        )
        session.add(cycle)
        session.commit()
        session.refresh(dept)
        session.refresh(admin)
        session.refresh(coord)
        session.refresh(viewer)
        session.refresh(cycle)
        yield session


def test_coordinator_can_add_metric_to_own_contribution(step6_db_session: Session) -> None:
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step6_db_session, cycle.id, data, coord)
    metric_data = ContributionMetricCreate(name="Students reached", value_number=1200.0, unit="students", year=2025)
    m = create_metric(step6_db_session, c, metric_data, coord)
    assert m.contribution_id == c.id
    assert m.value_number == 1200.0


def test_coordinator_cannot_add_metric_to_another_department(step6_db_session: Session) -> None:
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    admin = step6_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    dept = step6_db_session.exec(select(Department)).first()
    other_dept_id = uuid4()
    step6_db_session.add(Department(id=other_dept_id, name="Other", code="OTH", type=DepartmentType.OTHER))
    step6_db_session.commit()
    data = ContributionCreate(
        title="Other Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
        department_id=other_dept_id,
    )
    c = create_contribution(step6_db_session, cycle.id, data, admin)
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    metric_data = ContributionMetricCreate(name="X1", value_number=1.0)
    with pytest.raises(ValueError, match="not allowed"):
        create_metric(step6_db_session, c, metric_data, coord)


def test_viewer_cannot_add_metric(step6_db_session: Session) -> None:
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step6_db_session, cycle.id, data, coord)
    viewer = step6_db_session.exec(select(User).where(User.role == UserRole.VIEWER)).first()
    metric_data = ContributionMetricCreate(name="M1", value_number=1.0)
    with pytest.raises(ValueError, match="not allowed"):
        create_metric(step6_db_session, c, metric_data, viewer)


def test_admin_can_delete_metric(step6_db_session: Session) -> None:
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    admin = step6_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step6_db_session, cycle.id, data, coord)
    metric_data = ContributionMetricCreate(name="M1", value_number=1.0)
    m = create_metric(step6_db_session, c, metric_data, coord)
    delete_metric(step6_db_session, m, admin)
    assert step6_db_session.get(ContributionMetric, m.id) is None


def test_non_admin_cannot_delete_metric_from_approved_contribution(step6_db_session: Session) -> None:
    from app.services.contribution_service import approve_contribution, submit_contribution
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    admin = step6_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step6_db_session, cycle.id, data, coord)
    submit_contribution(step6_db_session, c, coord)
    step6_db_session.refresh(c)
    approve_contribution(step6_db_session, c, admin)
    step6_db_session.refresh(c)
    metric_data = ContributionMetricCreate(name="M1", value_number=1.0)
    m = create_metric(step6_db_session, c, metric_data, admin)  # admin added before we check delete
    with pytest.raises(ValueError, match="not allowed"):
        delete_metric(step6_db_session, m, coord)


def test_authenticated_user_with_access_can_list_comments(step6_db_session: Session) -> None:
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step6_db_session, cycle.id, data, coord)
    comment_data = CommentCreate(text="A review comment here.")
    create_comment(step6_db_session, c, comment_data, coord)
    items = list_comments_for_contribution(step6_db_session, c, coord)
    assert len(items) == 1
    assert items[0].text == "A review comment here."


def test_coordinator_can_add_comment(step6_db_session: Session) -> None:
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step6_db_session, cycle.id, data, coord)
    comment_data = CommentCreate(text="Please add more detail.")
    com = create_comment(step6_db_session, c, comment_data, coord)
    assert com.author_user_id == coord.id


def test_viewer_cannot_add_comment(step6_db_session: Session) -> None:
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    viewer = step6_db_session.exec(select(User).where(User.role == UserRole.VIEWER)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step6_db_session, cycle.id, data, coord)
    with pytest.raises(ValueError, match="not allowed"):
        create_comment(step6_db_session, c, CommentCreate(text="Viewer comment here."), viewer)


def test_coordinator_can_add_evidence_to_own_contribution(step6_db_session: Session) -> None:
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step6_db_session, cycle.id, data, coord)
    ev_data = EvidenceFileCreate(
        file_name="summary.pdf",
        file_url="https://example.com/summary.pdf",
        file_type="pdf",
    )
    ev = create_evidence_file(step6_db_session, c, ev_data, coord)
    assert ev.contribution_id == c.id
    assert ev.file_type == "pdf"


def test_viewer_cannot_add_evidence(step6_db_session: Session) -> None:
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    viewer = step6_db_session.exec(select(User).where(User.role == UserRole.VIEWER)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step6_db_session, cycle.id, data, coord)
    ev_data = EvidenceFileCreate(
        file_name="x.pdf",
        file_url="https://example.com/x.pdf",
        file_type="pdf",
    )
    with pytest.raises(ValueError, match="not allowed"):
        create_evidence_file(step6_db_session, c, ev_data, viewer)


def test_admin_can_delete_evidence(step6_db_session: Session) -> None:
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    admin = step6_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step6_db_session, cycle.id, data, coord)
    ev_data = EvidenceFileCreate(
        file_name="x.pdf",
        file_url="https://example.com/x.pdf",
        file_type="pdf",
    )
    ev = create_evidence_file(step6_db_session, c, ev_data, coord)
    delete_evidence_file(step6_db_session, ev, admin)
    assert step6_db_session.get(EvidenceFile, ev.id) is None


def test_non_admin_cannot_delete_evidence_from_approved_contribution(step6_db_session: Session) -> None:
    from app.services.contribution_service import approve_contribution, submit_contribution
    cycle = step6_db_session.exec(select(ReportingCycle)).first()
    coord = step6_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    admin = step6_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step6_db_session, cycle.id, data, coord)
    ev_data = EvidenceFileCreate(
        file_name="x.pdf",
        file_url="https://example.com/x.pdf",
        file_type="pdf",
    )
    ev = create_evidence_file(step6_db_session, c, ev_data, coord)
    submit_contribution(step6_db_session, c, coord)
    step6_db_session.refresh(c)
    approve_contribution(step6_db_session, c, admin)
    step6_db_session.refresh(c)
    with pytest.raises(ValueError, match="not allowed"):
        delete_evidence_file(step6_db_session, ev, coord)
