"""
Report section drafts and Markdown export tests.

- 401 when unauthenticated (endpoints).
- Service: admin-only create/update, ordering, and export compilation.
"""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from app.main import app
from app.models.enums import DraftGeneratedBy, ReportSectionScopeType, ReportSectionStatus, ReportingCycleStatus, UserRole
from app.models.report_section_draft import ReportSectionDraft
from app.models.reporting_cycle import ReportingCycle
from app.models.user import User
from app.schemas.report_section import ReportSectionDraftCreate, ReportSectionDraftUpdate
from app.services.report_section_service import (
    compile_markdown_report,
    create_report_section,
    list_report_sections,
    update_report_section,
)
from app.services.reporting_cycle_service import get_reporting_cycle_by_id
from app.core.security import hash_password

client = TestClient(app)


# --- Endpoint 401 tests ---


def test_list_report_sections_without_auth_returns_401() -> None:
    response = client.get("/api/v1/report-sections", params={"reporting_cycle_id": str(uuid4())})
    assert response.status_code == 401


def test_get_report_section_without_auth_returns_401() -> None:
    response = client.get(f"/api/v1/report-sections/{uuid4()}")
    assert response.status_code == 401


def test_create_report_section_without_auth_returns_401() -> None:
    response = client.post(
        "/api/v1/report-sections",
        json={
            "reporting_cycle_id": str(uuid4()),
            "scope_type": "SDG",
            "scope_value": "4",
            "title": "SDG 4 – Quality Education",
            "content_markdown": "## Overview\nInitial draft.",
        },
    )
    assert response.status_code == 401


def test_update_report_section_without_auth_returns_401() -> None:
    response = client.patch(
        f"/api/v1/report-sections/{uuid4()}",
        json={"content_markdown": "Updated"},
    )
    assert response.status_code == 401


def test_export_markdown_without_auth_returns_401() -> None:
    response = client.get("/api/v1/exports/report.md", params={"reporting_cycle_id": str(uuid4())})
    assert response.status_code == 401


# --- Service-level fixtures and tests ---


@pytest.fixture
def report_db_session() -> Session:
    """Session with ReportingCycle, ReportSectionDraft, and User tables."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine, tables=[ReportingCycle.__table__, ReportSectionDraft.__table__, User.__table__])
    with Session(engine) as session:
        admin = User(
            id=uuid4(),
            name="Admin",
            email="admin8@test.com",
            password_hash=hash_password("StrongPass1!"),
            role=UserRole.ADMIN,
            department_id=None,
            is_active=True,
        )
        viewer = User(
            id=uuid4(),
            name="Viewer",
            email="viewer8@test.com",
            password_hash=hash_password("StrongPass1!"),
            role=UserRole.VIEWER,
            department_id=None,
            is_active=True,
        )
        session.add(admin)
        session.add(viewer)
        cycle = ReportingCycle(
            id=uuid4(),
            name="Sustainability Report 2025",
            year=2025,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status=ReportingCycleStatus.OPEN,
            in_scope_sdgs=[1, 4],
        )
        empty_cycle = ReportingCycle(
            id=uuid4(),
            name="Empty Report 2026",
            year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=ReportingCycleStatus.OPEN,
            in_scope_sdgs=[1],
        )
        session.add(cycle)
        session.add(empty_cycle)
        session.commit()
        session.refresh(admin)
        session.refresh(viewer)
        session.refresh(cycle)
        session.refresh(empty_cycle)
        yield session


def test_create_report_section_unknown_cycle_raises(report_db_session: Session) -> None:
    admin = report_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    section_data = ReportSectionDraftCreate(
        reporting_cycle_id=uuid4(),
        scope_type=ReportSectionScopeType.SDG,
        scope_value="4",
        title="SDG 4 – Quality Education",
        content_markdown="## Overview\nInitial draft.",
    )
    with pytest.raises(ValueError, match="Reporting cycle not found"):
        create_report_section(report_db_session, section_data, admin)


def test_admin_can_create_and_update_report_section(report_db_session: Session) -> None:
    admin = report_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    cycle = report_db_session.exec(select(ReportingCycle).where(ReportingCycle.year == 2025)).first()
    section_data = ReportSectionDraftCreate(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.SDG,
        scope_value="4",
        title="SDG 4 – Quality Education",
        content_markdown="## Overview\nInitial draft.",
    )
    section = create_report_section(report_db_session, section_data, admin)
    assert section.id is not None
    assert section.status == ReportSectionStatus.DRAFT
    update_data = ReportSectionDraftUpdate(
        content_markdown="## Overview\nUpdated draft text.",
        status=ReportSectionStatus.REVIEWED,
    )
    updated = update_report_section(report_db_session, section, update_data, admin)
    assert updated.status == ReportSectionStatus.REVIEWED
    assert "Updated draft text." in updated.content_markdown


def test_non_admin_cannot_create_report_section(report_db_session: Session) -> None:
    viewer = report_db_session.exec(select(User).where(User.role == UserRole.VIEWER)).first()
    cycle = report_db_session.exec(select(ReportingCycle).where(ReportingCycle.year == 2025)).first()
    section_data = ReportSectionDraftCreate(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.SDG,
        scope_value="4",
        title="SDG 4 – Quality Education",
        content_markdown="## Overview\nInitial draft.",
    )
    with pytest.raises(ValueError, match="Only admins can modify report sections"):
        create_report_section(report_db_session, section_data, viewer)


def test_list_report_sections_empty_cycle_returns_empty(report_db_session: Session) -> None:
    empty_cycle = report_db_session.exec(select(ReportingCycle).where(ReportingCycle.year == 2026)).first()
    sections = list_report_sections(report_db_session, empty_cycle.id)
    assert sections == []


def test_compile_markdown_empty_cycle_has_header_only(report_db_session: Session) -> None:
    empty_cycle = report_db_session.exec(select(ReportingCycle).where(ReportingCycle.year == 2026)).first()
    compiled = compile_markdown_report(report_db_session, empty_cycle.id)
    assert compiled.section_count == 0
    assert compiled.cycle_name == empty_cycle.name
    assert compiled.cycle_year == empty_cycle.year
    assert compiled.content_markdown.startswith(f"# {empty_cycle.name}")


def test_compile_markdown_orders_sections_by_scope_and_title(report_db_session: Session) -> None:
    admin = report_db_session.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    cycle = report_db_session.exec(select(ReportingCycle).where(ReportingCycle.year == 2025)).first()
    # OVERALL, SDG, DEPARTMENT, THEME
    s_overall = ReportSectionDraftCreate(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.OVERALL,
        scope_value="summary",
        title="Executive Summary",
        content_markdown="Overall content.",
    )
    s_sdg = ReportSectionDraftCreate(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.SDG,
        scope_value="4",
        title="SDG 4 – Quality Education",
        content_markdown="SDG 4 content.",
    )
    s_department = ReportSectionDraftCreate(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.DEPARTMENT,
        scope_value="Dept-1",
        title="Department of Science",
        content_markdown="Department content.",
    )
    s_theme = ReportSectionDraftCreate(
        reporting_cycle_id=cycle.id,
        scope_type=ReportSectionScopeType.THEME,
        scope_value="Climate",
        title="Climate Action Theme",
        content_markdown="Theme content.",
    )
    create_report_section(report_db_session, s_department, admin)
    create_report_section(report_db_session, s_sdg, admin)
    create_report_section(report_db_session, s_overall, admin)
    create_report_section(report_db_session, s_theme, admin)
    compiled = compile_markdown_report(report_db_session, cycle.id)
    # Expect headings in order: Executive Summary, SDG 4..., Department of Science, Climate Action Theme
    content = compiled.content_markdown
    idx_exec = content.index("## Executive Summary")
    idx_sdg4 = content.index("## SDG 4 – Quality Education")
    idx_dept = content.index("## Department of Science")
    idx_theme = content.index("## Climate Action Theme")
    assert idx_exec < idx_sdg4 < idx_dept < idx_theme

