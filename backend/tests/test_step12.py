"""
Step 12: Final hardening tests.

- Pagination: list_departments with skip/limit returns correct slice.
- Audit: log_action creates an AuditLog row.
- Startup / optional AI: generate_text raises when API key is missing; app starts without key.
- Demo seed: seed_demo_data runs without crashing when SDGs exist.
"""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select
from sqlmodel import SQLModel

from app.core.config import get_settings
from app.core.pagination import PAGINATION_LIMIT_MAX, validate_pagination
from app.main import app
from app.models.audit_log import AuditLog
from app.models.department import Department
from app.models.enums import DepartmentType, UserRole
from app.models.user import User
from app.schemas.department import DepartmentCreate
from app.services.audit_service import log_action
from app.services.department_service import create_department, list_departments
from app.core.security import hash_password

client = TestClient(app)


# --- Pagination ---


def test_validate_pagination_accepts_valid_skip_limit() -> None:
    validate_pagination(0, 1)
    validate_pagination(0, 100)
    validate_pagination(10, PAGINATION_LIMIT_MAX)


def test_validate_pagination_rejects_negative_skip() -> None:
    with pytest.raises(ValueError, match="skip must be >= 0"):
        validate_pagination(-1, 10)


def test_validate_pagination_rejects_limit_out_of_range() -> None:
    with pytest.raises(ValueError, match="limit must be between"):
        validate_pagination(0, 0)
    with pytest.raises(ValueError, match="limit must be between"):
        validate_pagination(0, PAGINATION_LIMIT_MAX + 1)


@pytest.fixture
def dept_session() -> Session:
    """In-memory session with Department table for pagination tests."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine, tables=[Department.__table__])
    with Session(engine) as session:
        yield session


def test_list_departments_pagination_skip_limit(dept_session: Session) -> None:
    """list_departments with skip/limit returns the correct slice."""
    for name, code in [("Alpha", "AL"), ("Beta", "BE"), ("Gamma", "GA")]:
        create_department(dept_session, DepartmentCreate(name=name, code=code, type=DepartmentType.ACADEMIC))
    all_depts = list_departments(dept_session, skip=0, limit=10)
    assert len(all_depts) == 3
    slice_one = list_departments(dept_session, skip=1, limit=1)
    assert len(slice_one) == 1
    assert slice_one[0].name == "Beta"
    slice_none = list_departments(dept_session, skip=10, limit=5)
    assert len(slice_none) == 0


# --- Audit ---


@pytest.fixture
def audit_session() -> Session:
    """In-memory session with User and AuditLog for audit tests."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine, tables=[User.__table__, AuditLog.__table__])
    with Session(engine) as session:
        user = User(
            id=uuid4(),
            name="Audit Test User",
            email="audit@test.com",
            password_hash=hash_password("TestPass1!"),
            role=UserRole.ADMIN,
            department_id=None,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        yield session


def test_log_action_creates_audit_entry(audit_session: Session) -> None:
    """log_action adds an AuditLog row with correct action and entity."""
    user = audit_session.exec(select(User)).first()
    assert user is not None
    before = audit_session.exec(select(AuditLog)).all()
    log_action(
        audit_session,
        user.id,
        "department_created",
        "department",
        str(uuid4()),
        metadata_json={"name": "Test Dept"},
    )
    after = audit_session.exec(select(AuditLog)).all()
    assert len(after) == len(before) + 1
    entry = after[-1]
    assert entry.action == "department_created"
    assert entry.entity_type == "department"
    assert entry.metadata_json == {"name": "Test Dept"}


# --- Optional AI config (startup / generate_text) ---


def test_generate_text_raises_when_api_key_missing(monkeypatch) -> None:
    """generate_text raises ValueError with 'not configured' when OPENAI_API_KEY is empty."""
    from app.services import llm_service
    original = get_settings()
    class EmptyKeySettings:
        openai_api_key = ""
        llm_model = original.llm_model
        llm_base_url = original.llm_base_url
    monkeypatch.setattr(llm_service, "get_settings", lambda: EmptyKeySettings())
    with pytest.raises(ValueError, match="not configured"):
        llm_service.generate_text("Hello", system_instruction="You are helpful.")


def test_app_starts_without_ai_config() -> None:
    """Health endpoint works without OPENAI_API_KEY (app starts cleanly)."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


# --- Demo seed ---


def test_seed_demo_data_runs_without_crashing() -> None:
    """seed_demo_data completes when SDGs exist; returns dict with expected keys."""
    from app.models.comment import Comment
    from app.models.contribution import Contribution
    from app.models.contribution_metric import ContributionMetric
    from app.models.evidence_file import EvidenceFile
    from app.models.report_section_draft import ReportSectionDraft
    from app.models.reporting_cycle import ReportingCycle
    from app.models.sdg import SDG
    from app.db.seed_demo_data import seed_demo_data

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
        ReportSectionDraft.__table__,
        AuditLog.__table__,
    ]
    for t in tables:
        t.create(engine, checkfirst=True)
    with Session(engine) as session:
        for i in range(1, 18):
            session.add(SDG(id=i, name=f"SDG {i}", description=f"Description {i}"))
        session.commit()
        counts = seed_demo_data(session)
    assert "departments" in counts
    assert "reporting_cycles" in counts
    assert "contributions" in counts
    assert counts["departments"] >= 1
    assert counts["reporting_cycles"] >= 1
