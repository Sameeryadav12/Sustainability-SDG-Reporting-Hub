"""
Step 11: AI report section generation tests.

All tests mock the LLM; no real API calls.
- 401/403 for unauthenticated / non-admin.
- 404 for unknown cycle, 400 for unsupported scope or no data.
- SDG / DEPARTMENT / OVERALL generation saves section with generated_by=AI, status=DRAFT.
- Overwrite updates existing section; LLM failure returns clean error.
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
from app.models.enums import (
    DraftGeneratedBy,
    ReportSectionScopeType,
    ReportSectionStatus,
    ReportingCycleStatus,
    UserRole,
)
from app.models.report_section_draft import ReportSectionDraft
from app.models.reporting_cycle import ReportingCycle
from app.models.sdg import SDG
from app.models.user import User
from app.schemas.report_generation import ReportSectionGenerateRequest
from app.services.ai_report_service import generate_report_section
from app.services.contribution_service import create_contribution
from app.schemas.contribution import ContributionCreate
from app.core.security import hash_password

client = TestClient(app)


def test_generate_report_section_without_auth_returns_401() -> None:
    response = client.post(
        "/api/v1/report-sections/generate",
        json={
            "reporting_cycle_id": str(uuid4()),
            "scope_type": "SDG",
            "scope_value": "4",
            "title": "SDG 4",
            "target_word_count": 300,
        },
    )
    assert response.status_code == 401


# --- Service-level tests with mocked LLM ---


@pytest.fixture
def step11_db_session() -> Session:
    """In-memory DB: SDG, Department, User, ReportingCycle, Contribution, ReportSectionDraft."""
    engine = create_engine("sqlite:///:memory:")
    tables = [
        SDG.__table__,
        Department.__table__,
        User.__table__,
        ReportingCycle.__table__,
        Contribution.__table__,
        ReportSectionDraft.__table__,
    ]
    for t in tables:
        t.create(engine, checkfirst=True)
    with Session(engine) as session:
        session.add(SDG(id=1, name="No Poverty", description="End poverty."))
        session.add(SDG(id=4, name="Quality Education", description="Ensure inclusive education."))
        session.commit()
        dept = Department(id=uuid4(), name="Science", code="SCI", type="ACADEMIC")
        session.add(dept)
        session.flush()
        admin = User(
            id=uuid4(),
            name="Admin",
            email="admin11@test.com",
            password_hash=hash_password("StrongPass1!"),
            role=UserRole.ADMIN,
            department_id=None,
            is_active=True,
        )
        viewer = User(
            id=uuid4(),
            name="Viewer",
            email="viewer11@test.com",
            password_hash=hash_password("StrongPass1!"),
            role=UserRole.VIEWER,
            department_id=None,
            is_active=True,
        )
        session.add(admin)
        session.add(viewer)
        session.flush()
        cycle = ReportingCycle(
            id=uuid4(),
            name="Cycle 2025",
            year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status=ReportingCycleStatus.OPEN,
            in_scope_sdgs=[1, 4],
        )
        session.add(cycle)
        session.commit()
        session.refresh(dept)
        session.refresh(admin)
        session.refresh(viewer)
        session.refresh(cycle)
        yield session


@pytest.fixture
def mock_llm(monkeypatch):
    """Mock LLM to return a fixed string and never call the real API."""
    from app.services import ai_report_service
    def _generate_text(prompt: str, *, system_instruction: str | None = None) -> str:
        return "## Summary\n\nThis is mock-generated report content for testing."
    monkeypatch.setattr(ai_report_service, "generate_text", _generate_text)


def test_non_admin_cannot_generate(step11_db_session: Session, mock_llm) -> None:
    cycle = step11_db_session.exec(select(ReportingCycle)).first()
    viewer = step11_db_session.exec(select(User).where(User.role == UserRole.VIEWER)).first()
    dept = step11_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="A Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=4,
        department_id=dept.id,
    )
    create_contribution(step11_db_session, cycle.id, data, step11_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first())
    step11_db_session.commit()
    req = ReportSectionGenerateRequest(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.SDG,
        scope_value="4",
        title="SDG 4",
        target_word_count=300,
    )
    with pytest.raises(ValueError, match="Only admins"):
        generate_report_section(step11_db_session, req, viewer)


def test_unknown_reporting_cycle_returns_404(step11_db_session: Session, mock_llm) -> None:
    admin = step11_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    req = ReportSectionGenerateRequest(
        reporting_cycle_id=uuid4(),
        scope_type=ReportSectionScopeType.SDG,
        scope_value="4",
        target_word_count=300,
    )
    with pytest.raises(ValueError, match="Reporting cycle not found"):
        generate_report_section(step11_db_session, req, admin)


def test_unsupported_scope_returns_clean_error(step11_db_session: Session, mock_llm) -> None:
    cycle = step11_db_session.exec(select(ReportingCycle)).first()
    admin = step11_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    req = ReportSectionGenerateRequest(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.THEME,
        scope_value="Climate",
        target_word_count=300,
    )
    with pytest.raises(ValueError, match="not supported"):
        generate_report_section(step11_db_session, req, admin)


def test_sdg_generation_gathers_data_and_saves_section(step11_db_session: Session, mock_llm) -> None:
    cycle = step11_db_session.exec(select(ReportingCycle)).first()
    admin = step11_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    dept = step11_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="Education Project",
        type="TEACHING",
        description="At least ten characters here.",
        primary_sdg_id=4,
        department_id=dept.id,
    )
    create_contribution(step11_db_session, cycle.id, data, admin)
    step11_db_session.commit()
    req = ReportSectionGenerateRequest(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.SDG,
        scope_value="4",
        title="SDG 4 – Quality Education",
        target_word_count=300,
    )
    section, source_count = generate_report_section(step11_db_session, req, admin)
    assert section.generated_by == DraftGeneratedBy.AI
    assert section.status == ReportSectionStatus.DRAFT
    assert section.scope_type == ReportSectionScopeType.SDG
    assert section.scope_value == "4"
    assert "mock-generated" in section.content_markdown
    assert source_count == 1


def test_department_generation_saves_section(step11_db_session: Session, mock_llm) -> None:
    cycle = step11_db_session.exec(select(ReportingCycle)).first()
    admin = step11_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    dept = step11_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="Dept Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
        department_id=dept.id,
    )
    create_contribution(step11_db_session, cycle.id, data, admin)
    step11_db_session.commit()
    req = ReportSectionGenerateRequest(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.DEPARTMENT,
        scope_value=str(dept.id),
        title="Science Department",
        target_word_count=400,
    )
    section, source_count = generate_report_section(step11_db_session, req, admin)
    assert section.generated_by == DraftGeneratedBy.AI
    assert section.status == ReportSectionStatus.DRAFT
    assert section.scope_type == ReportSectionScopeType.DEPARTMENT
    assert source_count == 1


def test_overall_generation_saves_section(step11_db_session: Session, mock_llm) -> None:
    cycle = step11_db_session.exec(select(ReportingCycle)).first()
    admin = step11_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    dept = step11_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="Overall Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=1,
        department_id=dept.id,
    )
    create_contribution(step11_db_session, cycle.id, data, admin)
    step11_db_session.commit()
    req = ReportSectionGenerateRequest(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.OVERALL,
        scope_value="summary",
        title="Executive Summary",
        target_word_count=500,
    )
    section, source_count = generate_report_section(step11_db_session, req, admin)
    assert section.generated_by == DraftGeneratedBy.AI
    assert section.status == ReportSectionStatus.DRAFT
    assert section.scope_type == ReportSectionScopeType.OVERALL
    assert source_count == 1


def test_existing_section_updated_when_overwrite_true(step11_db_session: Session, mock_llm) -> None:
    cycle = step11_db_session.exec(select(ReportingCycle)).first()
    admin = step11_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    dept = step11_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=4,
        department_id=dept.id,
    )
    create_contribution(step11_db_session, cycle.id, data, admin)
    step11_db_session.commit()
    req = ReportSectionGenerateRequest(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.SDG,
        scope_value="4",
        title="SDG 4",
        target_word_count=300,
        overwrite_existing=True,
    )
    section1, _ = generate_report_section(step11_db_session, req, admin)
    section2, _ = generate_report_section(step11_db_session, req, admin)
    assert section1.id == section2.id
    assert "mock-generated" in section2.content_markdown


def test_mocked_llm_failure_returns_clean_error(step11_db_session: Session, monkeypatch) -> None:
    from app.services import ai_report_service
    def _fail(*args, **kwargs):
        raise ValueError("AI generation failed. Please try again.")
    monkeypatch.setattr(ai_report_service, "generate_text", _fail)
    cycle = step11_db_session.exec(select(ReportingCycle)).first()
    admin = step11_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    dept = step11_db_session.exec(select(Department)).first()
    data = ContributionCreate(
        title="Contribution",
        type="RESEARCH",
        description="At least ten characters here.",
        primary_sdg_id=4,
        department_id=dept.id,
    )
    create_contribution(step11_db_session, cycle.id, data, admin)
    step11_db_session.commit()
    req = ReportSectionGenerateRequest(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.SDG,
        scope_value="4",
        target_word_count=300,
    )
    with pytest.raises(ValueError, match="AI generation failed"):
        generate_report_section(step11_db_session, req, admin)


def test_no_relevant_data_returns_placeholder_section(step11_db_session: Session, mock_llm) -> None:
    """When no contributions exist for the scope, returns a placeholder section (no LLM call)."""
    cycle = step11_db_session.exec(select(ReportingCycle)).first()
    admin = step11_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    req = ReportSectionGenerateRequest(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.SDG,
        scope_value="4",
        target_word_count=300,
    )
    section, count = generate_report_section(step11_db_session, req, admin)
    assert count == 0
    assert section is not None
    assert "SDG 4" in section.content_markdown
    assert "Limited data" in section.content_markdown
