"""
Report section draft service: list, get, create, update, compile Markdown report.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlmodel import Session, select

from app.models.enums import DraftGeneratedBy, ReportSectionScopeType, ReportSectionStatus, UserRole
from app.models.report_section_draft import ReportSectionDraft
from app.models.reporting_cycle import ReportingCycle
from app.models.user import User
from app.schemas.report_section import (
    CompiledReportResponse,
    ReportSectionDraftCreate,
    ReportSectionDraftUpdate,
)
from app.services.reporting_cycle_service import get_reporting_cycle_by_id
from app.core.pagination import PAGINATION_LIMIT_DEFAULT, PAGINATION_SKIP_DEFAULT


def list_report_sections(
    session: Session,
    reporting_cycle_id: UUID,
    skip: int = PAGINATION_SKIP_DEFAULT,
    limit: int = PAGINATION_LIMIT_DEFAULT,
) -> list[ReportSectionDraft]:
    """List report sections for a reporting cycle in a deterministic order, with optional pagination."""
    cycle = get_reporting_cycle_by_id(session, reporting_cycle_id)
    if cycle is None:
        raise ValueError("Reporting cycle not found.")
    statement = select(ReportSectionDraft).where(
        ReportSectionDraft.reporting_cycle_id == reporting_cycle_id
    )
    sections: list[ReportSectionDraft] = list(session.exec(statement).all())
    sorted_sections = _sort_sections(sections)
    return sorted_sections[skip : skip + limit]


def get_report_section_by_id(session: Session, section_id: UUID) -> ReportSectionDraft | None:
    """Return a report section draft by id or None."""
    return session.get(ReportSectionDraft, section_id)


def get_report_section_by_scope(
    session: Session,
    reporting_cycle_id: UUID,
    scope_type: ReportSectionScopeType,
    scope_value: str,
) -> ReportSectionDraft | None:
    """Return the report section draft matching cycle + scope_type + scope_value, or None."""
    statement = select(ReportSectionDraft).where(
        ReportSectionDraft.reporting_cycle_id == reporting_cycle_id,
        ReportSectionDraft.scope_type == scope_type,
        ReportSectionDraft.scope_value == scope_value.strip(),
    )
    return session.exec(statement).first()


def create_report_section(
    session: Session,
    data: ReportSectionDraftCreate,
    current_user: User,
) -> ReportSectionDraft:
    """Create a new report section draft. Admin-only."""
    if current_user.role != UserRole.ADMIN:
        raise ValueError("Only admins can modify report sections.")
    cycle = get_reporting_cycle_by_id(session, data.reporting_cycle_id)
    if cycle is None:
        raise ValueError("Reporting cycle not found.")
    section = ReportSectionDraft(
        reporting_cycle_id=data.reporting_cycle_id,
        scope_type=data.scope_type,
        scope_value=data.scope_value.strip(),
        title=data.title.strip(),
        content_markdown=data.content_markdown,
        status=data.status or ReportSectionStatus.DRAFT,
        generated_by=data.generated_by or DraftGeneratedBy.HUMAN,
    )
    session.add(section)
    session.commit()
    session.refresh(section)
    return section


def update_report_section(
    session: Session,
    section: ReportSectionDraft,
    data: ReportSectionDraftUpdate,
    current_user: User,
) -> ReportSectionDraft:
    """Update an existing report section draft. Admin-only."""
    if current_user.role != UserRole.ADMIN:
        raise ValueError("Only admins can modify report sections.")

    if data.title is not None:
        section.title = data.title.strip()
    if data.content_markdown is not None:
        section.content_markdown = data.content_markdown
    if data.status is not None:
        section.status = data.status
    if data.generated_by is not None:
        section.generated_by = data.generated_by

    session.add(section)
    session.commit()
    session.refresh(section)
    return section


def compile_markdown_report(session: Session, reporting_cycle_id: UUID) -> CompiledReportResponse:
    """
    Compile a Markdown report for the given reporting cycle.
    Sections are ordered: OVERALL, SDG, DEPARTMENT, THEME, then by title.
    """
    cycle = get_reporting_cycle_by_id(session, reporting_cycle_id)
    if cycle is None:
        raise ValueError("Reporting cycle not found.")
    statement = select(ReportSectionDraft).where(
        ReportSectionDraft.reporting_cycle_id == reporting_cycle_id
    )
    sections: list[ReportSectionDraft] = _sort_sections(list(session.exec(statement).all()))

    lines: list[str] = []
    # Top-level heading
    lines.append(f"# {cycle.name}")
    lines.append("")
    lines.append(f"_Reporting year: {cycle.year}_")
    lines.append("")

    for section in sections:
        lines.append(f"## {section.title.strip()}")
        lines.append("")
        content = (section.content_markdown or "").strip()
        if content:
            lines.append(content)
            lines.append("")

    content_markdown = "\n".join(lines).rstrip() + "\n"
    return CompiledReportResponse(
        reporting_cycle_id=cycle.id,
        cycle_name=cycle.name,
        cycle_year=cycle.year,
        section_count=len(sections),
        content_markdown=content_markdown,
    )


def _sort_sections(sections: Sequence[ReportSectionDraft]) -> list[ReportSectionDraft]:
    """Sort sections by scope type (OVERALL, SDG, DEPARTMENT, THEME) then title."""
    scope_order = {
        ReportSectionScopeType.OVERALL: 0,
        ReportSectionScopeType.SDG: 1,
        ReportSectionScopeType.DEPARTMENT: 2,
        ReportSectionScopeType.THEME: 3,
    }

    def sort_key(s: ReportSectionDraft) -> tuple[int, str]:
        return (scope_order.get(s.scope_type, 99), (s.title or "").lower())

    return sorted(sections, key=sort_key)

