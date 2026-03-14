"""
AI report section generation service (Step 11).

Gathers context by scope, builds prompt, calls LLM, saves/updates ReportSectionDraft.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.models.contribution import Contribution
from app.models.department import Department
from app.models.enums import DraftGeneratedBy, ReportSectionScopeType, ReportSectionStatus, UserRole
from app.models.report_section_draft import ReportSectionDraft
from app.models.reporting_cycle import ReportingCycle
from app.models.sdg import SDG
from app.models.user import User
from app.core.config import get_settings
from app.schemas.report_generation import ReportSectionGenerateRequest
from app.services.llm_service import generate_text
from app.services.prompt_builder import build_system_instruction, build_user_context
from app.services.report_section_service import get_report_section_by_id, get_report_section_by_scope
from app.services.reporting_cycle_service import get_reporting_cycle_by_id


SUPPORTED_SCOPE_TYPES = {ReportSectionScopeType.SDG, ReportSectionScopeType.DEPARTMENT, ReportSectionScopeType.OVERALL}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _contribution_to_summary(c: Contribution) -> dict:
    """Build a small dict for prompt context. Includes department name when available."""
    return {
        "id": str(c.id),
        "title": c.title,
        "type": c.type.value if hasattr(c.type, "value") else str(c.type),
        "description": (c.description or "")[:500],
        "department": c.department.name if c.department else None,
        "primary_sdg_id": c.primary_sdg_id,
        "status": c.status.value if hasattr(c.status, "value") else str(c.status),
        "start_date": str(c.start_date) if c.start_date else None,
        "end_date": str(c.end_date) if c.end_date else None,
    }


def _gather_sdg_context(
    session: Session,
    reporting_cycle_id: UUID,
    scope_value: str,
) -> tuple[dict, list[dict], list[Contribution]]:
    """Gather scope metadata, contributions summary list, and full contribution list for SDG scope.
    Includes contributions where primary_sdg_id = sdg_id OR sdg_id in secondary_sdg_ids."""
    try:
        sdg_id = int(scope_value.strip())
    except ValueError:
        return {}, [], []
    sdg = session.get(SDG, sdg_id)
    if not sdg:
        return {}, [], []
    scope_metadata = {"sdg_id": sdg_id, "sdg_name": sdg.name, "sdg_description": (sdg.description or "")[:300]}
    stmt = (
        select(Contribution)
        .options(selectinload(Contribution.department))
        .where(Contribution.reporting_cycle_id == reporting_cycle_id)
        .order_by(Contribution.created_at.asc())
    )
    all_for_cycle = list(session.exec(stmt).all())
    contributions = [
        c
        for c in all_for_cycle
        if c.primary_sdg_id == sdg_id
        or (c.secondary_sdg_ids is not None and sdg_id in c.secondary_sdg_ids)
    ]
    summaries = [_contribution_to_summary(c) for c in contributions]
    return scope_metadata, summaries, contributions


def _gather_department_context(
    session: Session,
    reporting_cycle_id: UUID,
    scope_value: str,
) -> tuple[dict, list[dict], list[Contribution]]:
    """Gather scope metadata and contributions for DEPARTMENT scope."""
    try:
        dept_uuid = UUID(scope_value.strip())
    except (ValueError, TypeError):
        return {}, [], []
    dept = session.get(Department, dept_uuid)
    if not dept:
        return {}, [], []
    scope_metadata = {"department_id": str(dept.id), "department_name": dept.name, "department_code": dept.code}
    stmt = (
        select(Contribution)
        .options(selectinload(Contribution.department))
        .where(
            Contribution.reporting_cycle_id == reporting_cycle_id,
            Contribution.department_id == dept_uuid,
        )
        .order_by(Contribution.created_at.asc())
    )
    contributions = list(session.exec(stmt).all())
    summaries = [_contribution_to_summary(c) for c in contributions]
    return scope_metadata, summaries, contributions


def _gather_overall_context(
    session: Session,
    reporting_cycle_id: UUID,
) -> tuple[dict, list[dict], list[Contribution]]:
    """Gather analytics-like summary and contributions for OVERALL scope."""
    stmt = (
        select(Contribution)
        .options(selectinload(Contribution.department))
        .where(Contribution.reporting_cycle_id == reporting_cycle_id)
        .order_by(Contribution.created_at.asc())
    )
    contributions = list(session.exec(stmt).all())
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for c in contributions:
        s = c.status.value if hasattr(c.status, "value") else str(c.status)
        by_status[s] = by_status.get(s, 0) + 1
        t = c.type.value if hasattr(c.type, "value") else str(c.type)
        by_type[t] = by_type.get(t, 0) + 1
    scope_metadata = {}
    analytics_summary = {
        "total_contributions": len(contributions),
        "by_status": by_status,
        "by_type": by_type,
    }
    summaries = [_contribution_to_summary(c) for c in contributions[:30]]
    return scope_metadata, summaries, contributions


def generate_report_section(
    session: Session,
    request_data: ReportSectionGenerateRequest,
    current_user: User,
) -> tuple[ReportSectionDraft, int]:
    """
    Generate a report section draft using AI. Admin only.
    Returns (saved_section, source_contribution_count).
    Raises ValueError for validation/generation errors.
    """
    if current_user.role != UserRole.ADMIN:
        raise ValueError("Only admins can generate report sections.")
    cycle = get_reporting_cycle_by_id(session, request_data.reporting_cycle_id)
    if cycle is None:
        raise ValueError("Reporting cycle not found.")
    if request_data.scope_type not in SUPPORTED_SCOPE_TYPES:
        raise ValueError("Scope is not supported for generation.")
    scope_value = request_data.scope_value.strip()
    if request_data.scope_type == ReportSectionScopeType.SDG:
        scope_metadata, contributions_summary, contributions = _gather_sdg_context(
            session, request_data.reporting_cycle_id, scope_value
        )
    elif request_data.scope_type == ReportSectionScopeType.DEPARTMENT:
        scope_metadata, contributions_summary, contributions = _gather_department_context(
            session, request_data.reporting_cycle_id, scope_value
        )
    else:
        scope_metadata, contributions_summary, contributions = _gather_overall_context(
            session, request_data.reporting_cycle_id
        )
    analytics_summary = None
    if request_data.scope_type == ReportSectionScopeType.OVERALL and contributions:
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for c in contributions:
            s = c.status.value if hasattr(c.status, "value") else str(c.status)
            by_status[s] = by_status.get(s, 0) + 1
            t = c.type.value if hasattr(c.type, "value") else str(c.type)
            by_type[t] = by_type.get(t, 0) + 1
        analytics_summary = {"total_contributions": len(contributions), "by_status": by_status, "by_type": by_type}
    title = (request_data.title or "").strip()
    if not title and request_data.scope_type == ReportSectionScopeType.SDG and scope_metadata:
        title = f"SDG {scope_metadata.get('sdg_id', scope_value)} – {scope_metadata.get('sdg_name', '')}"
    if not title and request_data.scope_type == ReportSectionScopeType.DEPARTMENT and scope_metadata:
        title = scope_metadata.get("department_name", "Department summary")
    if not title:
        title = f"Report section – {request_data.scope_type.value} {scope_value}"

    def _build_fallback_markdown() -> str:
        """Build a simple report section from data when OpenAI is not configured."""
        lines = [f"## {title}\n"]
        if request_data.scope_type == ReportSectionScopeType.SDG and scope_metadata:
            sdg_id = scope_metadata.get("sdg_id") or scope_value
            sdg_name = scope_metadata.get("sdg_name", "")
            lines.append(f"This section summarizes contributions related to **SDG {sdg_id}** ({sdg_name}).\n")
        elif request_data.scope_type == ReportSectionScopeType.DEPARTMENT and scope_metadata:
            dept_name = scope_metadata.get("department_name", "Department")
            lines.append(f"This section summarizes sustainability contributions from **{dept_name}**.\n")
        else:
            lines.append("This section summarizes sustainability contributions for this reporting cycle.\n")
        lines.append("### Key contributions\n")
        for i, c in enumerate(contributions_summary[:25], 1):
            title_c = c.get("title") or "Untitled"
            ctype = c.get("type", "")
            desc = (c.get("description") or "")[:300]
            if desc:
                desc = desc.replace("\n", " ") + ("…" if len(c.get("description") or "") > 300 else "")
            lines.append(f"{i}. **{title_c}** ({ctype})")
            if desc:
                lines.append(f"   {desc}")
            lines.append("")
        lines.append("\n*This draft was generated from contribution data. You can edit it in the report section editor.*")
        return "\n".join(lines)

    # When no contributions exist, generate placeholder narrative instead of calling LLM
    if not contributions_summary:
        sdg_id = scope_metadata.get("sdg_id") if request_data.scope_type == ReportSectionScopeType.SDG else None
        dept_name = scope_metadata.get("department_name") if request_data.scope_type == ReportSectionScopeType.DEPARTMENT else None
        if sdg_id is not None:
            content_markdown = f"""## Progress towards SDG {sdg_id}

This section summarizes progress related to SDG {sdg_id}. Limited data is currently available for this reporting cycle. As contributions are submitted and approved, this section will be updated with specific initiatives and outcomes."""
        elif dept_name:
            content_markdown = f"""## Department Summary: {dept_name}

This section summarizes sustainability contributions from {dept_name}. Limited data is currently available for this reporting cycle. As contributions are submitted and approved, this section will be updated with specific initiatives and outcomes."""
        else:
            content_markdown = f"""## Report Section Overview

This section summarizes sustainability progress for the reporting cycle. Limited data is currently available. As contributions are submitted and approved, this section will be updated with specific initiatives and outcomes."""
        existing = get_report_section_by_scope(
            session, request_data.reporting_cycle_id, request_data.scope_type, scope_value
        )
        now = _utc_now()
        if existing and request_data.overwrite_existing:
            existing.content_markdown = content_markdown
            existing.title = title[:512]
            existing.generated_by = DraftGeneratedBy.AI
            existing.status = ReportSectionStatus.DRAFT
            existing.last_generated_at = now
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing, 0
        if existing:
            return existing, 0
        section = ReportSectionDraft(
            reporting_cycle_id=request_data.reporting_cycle_id,
            scope_type=request_data.scope_type,
            scope_value=scope_value,
            title=title[:512],
            content_markdown=content_markdown,
            status=ReportSectionStatus.DRAFT,
            generated_by=DraftGeneratedBy.AI,
            last_generated_at=now,
        )
        session.add(section)
        session.commit()
        session.refresh(section)
        return section, 0

    # Use OpenAI if configured; otherwise build a template-based draft from contribution data
    settings = get_settings()
    if not (settings.openai_api_key or "").strip():
        content_markdown = _build_fallback_markdown()
    else:
        user_context = build_user_context(
            reporting_cycle_name=cycle.name,
            reporting_year=cycle.year,
            scope_type=request_data.scope_type.value,
            scope_value=scope_value,
            scope_metadata=scope_metadata,
            contributions_summary=contributions_summary,
            analytics_summary=analytics_summary,
            target_word_count=request_data.target_word_count,
        )
        system_instruction = build_system_instruction()
        try:
            content_markdown = generate_text(user_context, system_instruction=system_instruction)
        except ValueError:
            raise
        except Exception as e:
            raise ValueError("AI generation failed. Please try again.") from e
        if not content_markdown:
            content_markdown = "_No content generated._"
    existing = get_report_section_by_scope(
        session, request_data.reporting_cycle_id, request_data.scope_type, scope_value
    )
    now = _utc_now()
    if existing and request_data.overwrite_existing:
        existing.content_markdown = content_markdown
        existing.title = title[:512]
        existing.generated_by = DraftGeneratedBy.AI
        existing.status = ReportSectionStatus.DRAFT
        existing.last_generated_at = now
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing, len(contributions)
    if existing:
        return existing, len(contributions)
    section = ReportSectionDraft(
        reporting_cycle_id=request_data.reporting_cycle_id,
        scope_type=request_data.scope_type,
        scope_value=scope_value,
        title=title[:512],
        content_markdown=content_markdown,
        status=ReportSectionStatus.DRAFT,
        generated_by=DraftGeneratedBy.AI,
        last_generated_at=now,
    )
    session.add(section)
    session.commit()
    session.refresh(section)
    return section, len(contributions)
