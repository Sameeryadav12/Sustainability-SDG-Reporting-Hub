"""
Step 9: Evidence file upload tests.

- 401 for unauthenticated upload.
- Service: coordinator upload own/other dept, viewer no upload, reject type/size/empty.
- Upload creates DB record; list returns it; delete removes record and file.
"""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select
from sqlmodel import SQLModel

from app.main import app
from app.models.contribution import Contribution
from app.models.department import Department
from app.models.enums import ContributionStatus, DepartmentType, ReportingCycleStatus, UserRole
from app.models.evidence_file import EvidenceFile
from app.models.reporting_cycle import ReportingCycle
from app.models.sdg import SDG
from app.models.user import User
from app.schemas.contribution import ContributionCreate
from app.services.contribution_service import (
    approve_contribution,
    create_contribution,
    submit_contribution,
)
from app.services.evidence_service import (
    delete_evidence_file,
    list_evidence_for_contribution,
    upload_evidence_file,
)
from app.core.security import hash_password

client = TestClient(app)


def test_upload_evidence_without_auth_returns_401() -> None:
    response = client.post(
        f"/api/v1/contributions/{uuid4()}/evidence/upload",
        files={"file": ("doc.pdf", b"content", "application/pdf")},
    )
    assert response.status_code == 401


# --- Service-layer fixtures (in-memory DB + temp upload dir) ---


@pytest.fixture
def step9_upload_dir(tmp_path):
    """Temporary directory for uploads in tests."""
    return tmp_path


@pytest.fixture
def step9_settings(step9_upload_dir, monkeypatch):
    """Patch get_settings so upload_dir is tmp_path in storage and evidence services."""
    from app.core import config
    from app.services import evidence_service
    from app.services import storage_service
    _original = config.get_settings

    def _get():
        s = _original()
        class TestSettings:
            upload_dir = str(step9_upload_dir)
            allowed_evidence_extensions_list = getattr(s, "allowed_evidence_extensions_list", None) or [
                "pdf", "xlsx", "xls", "csv", "jpg", "jpeg", "png", "doc", "docx"
            ]
            max_upload_size_bytes = getattr(s, "max_upload_size_bytes", 10 * 1024 * 1024)
        return TestSettings()
    monkeypatch.setattr(config, "get_settings", _get)
    monkeypatch.setattr(evidence_service, "get_settings", _get)
    monkeypatch.setattr(storage_service, "get_settings", _get)
    yield step9_upload_dir


@pytest.fixture
def step9_db_session(step9_settings):
    """In-memory DB with SDG, Department, User, ReportingCycle, Contribution, EvidenceFile."""
    engine = create_engine("sqlite:///:memory:")
    tables = [
        SDG.__table__,
        Department.__table__,
        User.__table__,
        ReportingCycle.__table__,
        Contribution.__table__,
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
            email="admin9@test.com",
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
            email="coord9@test.com",
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
            email="viewer9@test.com",
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


def test_coordinator_can_upload_evidence_to_own_contribution(step9_db_session: Session) -> None:
    cycle = step9_db_session.exec(select(ReportingCycle)).first()
    coord = step9_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step9_db_session, cycle.id, data, coord)
    evidence = upload_evidence_file(
        step9_db_session,
        c,
        file_content=b"pdf content",
        original_filename="doc.pdf",
        content_type="application/pdf",
        current_user=coord,
    )
    assert evidence.contribution_id == c.id
    assert evidence.file_type == "pdf"
    assert evidence.file_url.startswith("/uploads/evidence/")
    assert step9_db_session.get(EvidenceFile, evidence.id) is not None


def test_coordinator_cannot_upload_evidence_to_another_department(step9_db_session: Session) -> None:
    cycle = step9_db_session.exec(select(ReportingCycle)).first()
    admin = step9_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    other_dept_id = uuid4()
    step9_db_session.add(Department(id=other_dept_id, name="Other", code="OTH", type=DepartmentType.OTHER))
    step9_db_session.commit()
    data = ContributionCreate(
        title="Other Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
        department_id=other_dept_id,
    )
    c = create_contribution(step9_db_session, cycle.id, data, admin)
    coord = step9_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    with pytest.raises(ValueError, match="not allowed"):
        upload_evidence_file(
            step9_db_session,
            c,
            file_content=b"content",
            original_filename="doc.pdf",
            content_type="application/pdf",
            current_user=coord,
        )


def test_viewer_cannot_upload_evidence(step9_db_session: Session) -> None:
    cycle = step9_db_session.exec(select(ReportingCycle)).first()
    coord = step9_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step9_db_session, cycle.id, data, coord)
    viewer = step9_db_session.exec(select(User).where(User.role == UserRole.VIEWER)).first()
    with pytest.raises(ValueError, match="not allowed"):
        upload_evidence_file(
            step9_db_session,
            c,
            file_content=b"content",
            original_filename="doc.pdf",
            content_type="application/pdf",
            current_user=viewer,
        )


def test_upload_rejects_disallowed_file_type(step9_db_session: Session) -> None:
    cycle = step9_db_session.exec(select(ReportingCycle)).first()
    coord = step9_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step9_db_session, cycle.id, data, coord)
    with pytest.raises(ValueError, match="File type is not allowed"):
        upload_evidence_file(
            step9_db_session,
            c,
            file_content=b"content",
            original_filename="script.exe",
            content_type="application/octet-stream",
            current_user=coord,
        )


def test_upload_rejects_empty_file(step9_db_session: Session) -> None:
    cycle = step9_db_session.exec(select(ReportingCycle)).first()
    coord = step9_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step9_db_session, cycle.id, data, coord)
    with pytest.raises(ValueError, match="empty"):
        upload_evidence_file(
            step9_db_session,
            c,
            file_content=b"",
            original_filename="doc.pdf",
            content_type="application/pdf",
            current_user=coord,
        )


def test_upload_creates_db_evidence_record(step9_db_session: Session) -> None:
    cycle = step9_db_session.exec(select(ReportingCycle)).first()
    coord = step9_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step9_db_session, cycle.id, data, coord)
    evidence = upload_evidence_file(
        step9_db_session,
        c,
        file_content=b"pdf bytes",
        original_filename="report.pdf",
        content_type="application/pdf",
        current_user=coord,
    )
    step9_db_session.refresh(evidence)
    assert evidence.id is not None
    assert evidence.file_name
    assert evidence.uploaded_by_user_id == coord.id


def test_list_evidence_returns_uploaded_records(step9_db_session: Session) -> None:
    cycle = step9_db_session.exec(select(ReportingCycle)).first()
    coord = step9_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step9_db_session, cycle.id, data, coord)
    upload_evidence_file(
        step9_db_session,
        c,
        file_content=b"content",
        original_filename="a.pdf",
        content_type="application/pdf",
        current_user=coord,
    )
    items = list_evidence_for_contribution(step9_db_session, c, coord)
    assert len(items) == 1
    assert items[0].file_type == "pdf"


def test_admin_can_delete_evidence_removes_record(step9_db_session: Session) -> None:
    cycle = step9_db_session.exec(select(ReportingCycle)).first()
    coord = step9_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    admin = step9_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step9_db_session, cycle.id, data, coord)
    evidence = upload_evidence_file(
        step9_db_session,
        c,
        file_content=b"content",
        original_filename="x.pdf",
        content_type="application/pdf",
        current_user=coord,
    )
    delete_evidence_file(step9_db_session, evidence, admin)
    assert step9_db_session.get(EvidenceFile, evidence.id) is None


def test_non_admin_cannot_delete_evidence_from_approved_contribution(step9_db_session: Session) -> None:
    cycle = step9_db_session.exec(select(ReportingCycle)).first()
    coord = step9_db_session.exec(select(User).where(User.role == UserRole.DEPARTMENT_COORDINATOR)).first()
    admin = step9_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
    )
    c = create_contribution(step9_db_session, cycle.id, data, coord)
    evidence = upload_evidence_file(
        step9_db_session,
        c,
        file_content=b"content",
        original_filename="x.pdf",
        content_type="application/pdf",
        current_user=coord,
    )
    submit_contribution(step9_db_session, c, coord)
    step9_db_session.refresh(c)
    approve_contribution(step9_db_session, c, admin)
    step9_db_session.refresh(c)
    with pytest.raises(ValueError, match="not allowed"):
        delete_evidence_file(step9_db_session, evidence, coord)
