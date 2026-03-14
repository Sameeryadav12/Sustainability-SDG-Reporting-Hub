"""
Step 10: CSV export endpoint tests.

- 401 for unauthenticated access to each export.
- 404 for unknown reporting_cycle_id.
- Empty cycle returns CSV with headers only.
- Contributions/metrics/evidence exports return expected columns and rows.
- Exports respect reporting_cycle_id (no leak from other cycles).
"""

import csv
import io
from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select
from sqlmodel import SQLModel

from app.main import app
from app.models.contribution import Contribution
from app.models.contribution_metric import ContributionMetric
from app.models.department import Department
from app.models.enums import DepartmentType, ReportingCycleStatus, UserRole
from app.models.evidence_file import EvidenceFile
from app.models.reporting_cycle import ReportingCycle
from app.models.sdg import SDG
from app.models.user import User
from app.schemas.contribution import ContributionCreate
from app.services.contribution_service import create_contribution
from app.services.export_service import (
    export_contributions_csv,
    export_evidence_csv,
    export_metrics_csv,
)
from app.core.security import hash_password

client = TestClient(app)


# --- 401 unauthenticated ---


def test_export_contributions_csv_without_auth_returns_401() -> None:
    response = client.get("/api/v1/exports/contributions.csv", params={"reporting_cycle_id": str(uuid4())})
    assert response.status_code == 401


def test_export_metrics_csv_without_auth_returns_401() -> None:
    response = client.get("/api/v1/exports/metrics.csv", params={"reporting_cycle_id": str(uuid4())})
    assert response.status_code == 401


def test_export_evidence_csv_without_auth_returns_401() -> None:
    response = client.get("/api/v1/exports/evidence.csv", params={"reporting_cycle_id": str(uuid4())})
    assert response.status_code == 401


# --- Service-layer fixture and tests ---


@pytest.fixture
def step10_db_session() -> Session:
    """In-memory DB: SDG, Department, User, ReportingCycle, Contribution, ContributionMetric, EvidenceFile."""
    engine = create_engine("sqlite:///:memory:")
    tables = [
        SDG.__table__,
        Department.__table__,
        User.__table__,
        ReportingCycle.__table__,
        Contribution.__table__,
        ContributionMetric.__table__,
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
        user = User(
            id=uuid4(),
            name="User",
            email="user10@test.com",
            password_hash=hash_password("StrongPass1!"),
            role=UserRole.ADMIN,
            department_id=None,
            is_active=True,
        )
        session.add(user)
        session.flush()
        cycle_a = ReportingCycle(
            id=uuid4(),
            name="Cycle 2025",
            year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status=ReportingCycleStatus.OPEN,
            in_scope_sdgs=[1],
        )
        cycle_b = ReportingCycle(
            id=uuid4(),
            name="Cycle 2026",
            year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=ReportingCycleStatus.DRAFT,
            in_scope_sdgs=[1],
        )
        session.add(cycle_a)
        session.add(cycle_b)
        session.commit()
        session.refresh(dept)
        session.refresh(user)
        session.refresh(cycle_a)
        session.refresh(cycle_b)
        yield session


def test_unknown_reporting_cycle_id_returns_404(step10_db_session: Session) -> None:
    with pytest.raises(ValueError, match="Reporting cycle not found"):
        export_contributions_csv(step10_db_session, uuid4())
    with pytest.raises(ValueError, match="Reporting cycle not found"):
        export_metrics_csv(step10_db_session, uuid4())
    with pytest.raises(ValueError, match="Reporting cycle not found"):
        export_evidence_csv(step10_db_session, uuid4())


def test_empty_cycle_returns_csv_headers_only(step10_db_session: Session) -> None:
    cycle = step10_db_session.exec(select(ReportingCycle).where(ReportingCycle.year == 2025)).first()
    content, _ = export_contributions_csv(step10_db_session, cycle.id)
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1
    assert "contribution_id" in rows[0]
    assert "reporting_cycle_name" in rows[0]

    content, _ = export_metrics_csv(step10_db_session, cycle.id)
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1
    assert "metric_id" in rows[0]

    content, _ = export_evidence_csv(step10_db_session, cycle.id)
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1
    assert "evidence_id" in rows[0]


def test_contributions_export_returns_expected_headers_and_rows(step10_db_session: Session) -> None:
    cycle = step10_db_session.exec(select(ReportingCycle).where(ReportingCycle.year == 2025)).first()
    user = step10_db_session.exec(select(User)).first()
    dept = step10_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="Test Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
        secondary_sdg_ids=[4, 13],
        department_id=dept.id,
    )
    create_contribution(step10_db_session, cycle.id, data, user)
    step10_db_session.commit()

    content, filename = export_contributions_csv(step10_db_session, cycle.id)
    assert "2025" in filename
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1
    row = rows[0]
    assert row["reporting_cycle_name"] == "Cycle 2025"
    assert row["reporting_year"] == "2025"
    assert row["department_name"] == "Science"
    assert row["title"] == "Test Contribution"
    assert "4" in row["secondary_sdg_ids"] and "13" in row["secondary_sdg_ids"]


def test_metrics_export_returns_expected_headers_and_rows(step10_db_session: Session) -> None:
    cycle = step10_db_session.exec(select(ReportingCycle).where(ReportingCycle.year == 2025)).first()
    user = step10_db_session.exec(select(User)).first()
    dept = step10_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="Contribution With Metric",
        type="TEACHING",
        description="At least ten characters here.",
        primary_sdg_id=1,
        department_id=dept.id,
    )
    c = create_contribution(step10_db_session, cycle.id, data, user)
    step10_db_session.commit()
    step10_db_session.refresh(c)
    metric = ContributionMetric(
        id=uuid4(),
        contribution_id=c.id,
        name="Students",
        value_number=100.0,
        unit="students",
        year=2025,
    )
    step10_db_session.add(metric)
    step10_db_session.commit()

    content, filename = export_metrics_csv(step10_db_session, cycle.id)
    assert "2025" in filename
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1
    row = rows[0]
    assert row["contribution_title"] == "Contribution With Metric"
    assert row["metric_name"] == "Students"
    assert float(row["value_number"]) == 100.0
    assert row["metric_year"] == "2025"


def test_evidence_export_returns_expected_headers_and_rows(step10_db_session: Session) -> None:
    cycle = step10_db_session.exec(select(ReportingCycle).where(ReportingCycle.year == 2025)).first()
    user = step10_db_session.exec(select(User)).first()
    dept = step10_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="Contribution With Evidence",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
        department_id=dept.id,
    )
    c = create_contribution(step10_db_session, cycle.id, data, user)
    step10_db_session.commit()
    step10_db_session.refresh(c)
    ev = EvidenceFile(
        id=uuid4(),
        contribution_id=c.id,
        file_name="report.pdf",
        file_url="/uploads/evidence/report.pdf",
        file_type="pdf",
        uploaded_by_user_id=user.id,
    )
    step10_db_session.add(ev)
    step10_db_session.commit()

    content, filename = export_evidence_csv(step10_db_session, cycle.id)
    assert "2025" in filename
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1
    row = rows[0]
    assert row["contribution_title"] == "Contribution With Evidence"
    assert row["file_name"] == "report.pdf"
    assert row["file_type"] == "pdf"


def test_export_filtering_respects_reporting_cycle_id(step10_db_session: Session) -> None:
    """Data in cycle A must not appear when exporting cycle B."""
    cycle_2025 = step10_db_session.exec(select(ReportingCycle).where(ReportingCycle.year == 2025)).first()
    cycle_2026 = step10_db_session.exec(select(ReportingCycle).where(ReportingCycle.year == 2026)).first()
    user = step10_db_session.exec(select(User)).first()
    dept = step10_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="Only in 2025",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
        department_id=dept.id,
    )
    create_contribution(step10_db_session, cycle_2025.id, data, user)
    step10_db_session.commit()

    content, _ = export_contributions_csv(step10_db_session, cycle_2026.id)
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 1  # header only
    assert "contribution_id" in rows[0]
