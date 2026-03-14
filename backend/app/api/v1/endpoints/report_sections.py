"""
Report section draft endpoints: list, get, create (admin), update (admin), generate (admin, Step 11).
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AdminUserDep, CurrentUserDep
from app.core.http_errors import raise_404
from app.core.pagination import (
    PAGINATION_LIMIT_DEFAULT,
    PAGINATION_LIMIT_MAX,
    PAGINATION_SKIP_DEFAULT,
    validate_pagination,
)
from app.db.session import SessionDep
from app.schemas.report_generation import ReportSectionGenerateRequest, ReportSectionGenerateResponse
from app.schemas.report_section import (
    ReportSectionDraftCreate,
    ReportSectionDraftRead,
    ReportSectionDraftUpdate,
    ReportSectionListItem,
)
from app.services.ai_report_service import generate_report_section
from app.services.audit_service import log_action
from app.services.report_section_service import (
    create_report_section,
    get_report_section_by_id,
    list_report_sections,
    update_report_section,
)

router = APIRouter(tags=["Report Sections"])


@router.get("/report-sections", response_model=list[ReportSectionListItem])
def list_report_sections_endpoint(
    session: SessionDep,
    current_user: CurrentUserDep,
    reporting_cycle_id: UUID = Query(...),
    skip: int = Query(PAGINATION_SKIP_DEFAULT, ge=0, description="Number of records to skip"),
    limit: int = Query(PAGINATION_LIMIT_DEFAULT, ge=1, le=PAGINATION_LIMIT_MAX, description="Max records to return"),
) -> list[ReportSectionListItem]:
    """List report sections for a reporting cycle (authenticated users). Supports skip/limit pagination."""
    try:
        validate_pagination(skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    try:
        sections = list_report_sections(session, reporting_cycle_id, skip=skip, limit=limit)
    except ValueError as e:
        msg = str(e)
        if "reporting cycle not found" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting cycle not found.",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return [ReportSectionListItem.model_validate(s) for s in sections]


@router.post(
    "/report-sections/generate",
    response_model=ReportSectionGenerateResponse,
    status_code=status.HTTP_200_OK,
)
def generate_report_section_endpoint(
    data: ReportSectionGenerateRequest,
    session: SessionDep,
    current_user: AdminUserDep,
) -> ReportSectionGenerateResponse:
    """Generate a report section draft using AI (admin only). Saves or updates ReportSectionDraft."""
    try:
        section = generate_report_section(session, data, current_user)
    except ValueError as e:
        msg = str(e)
        if "reporting cycle not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporting cycle not found.")
        if "scope is not supported" in msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        if "no relevant data" in msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        if "only admins" in msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        if "generation failed" in msg.lower() or "not configured" in msg.lower():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    section_obj, source_count = section
    log_action(
        session,
        current_user.id,
        "report_section_generated",
        "report_section",
        str(section_obj.id),
        metadata_json={
            "reporting_cycle_id": str(section_obj.reporting_cycle_id),
            "scope_type": section_obj.scope_type.value,
            "scope_value": section_obj.scope_value,
        },
    )
    response = ReportSectionGenerateResponse.model_validate(section_obj)
    response.source_contribution_count = source_count
    return response


@router.get("/report-sections/{section_id}", response_model=ReportSectionDraftRead)
def get_report_section_endpoint(
    section_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ReportSectionDraftRead:
    """Get a single report section draft by id (authenticated users)."""
    section = get_report_section_by_id(session, section_id)
    if section is None:
        raise_404("Report section not found.")
    return ReportSectionDraftRead.model_validate(section)


@router.post(
    "/report-sections",
    response_model=ReportSectionDraftRead,
    status_code=status.HTTP_201_CREATED,
)
def create_report_section_endpoint(
    data: ReportSectionDraftCreate,
    session: SessionDep,
    current_user: AdminUserDep,
) -> ReportSectionDraftRead:
    """Create a report section draft (admin only)."""
    try:
        section = create_report_section(session, data, current_user)
    except ValueError as e:
        msg = str(e)
        if "reporting cycle not found" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting cycle not found.",
            )
        if "only admins" in msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "report_section_created",
        "report_section",
        str(section.id),
        metadata_json={"reporting_cycle_id": str(section.reporting_cycle_id), "scope_type": section.scope_type.value},
    )
    return ReportSectionDraftRead.model_validate(section)


@router.patch("/report-sections/{section_id}", response_model=ReportSectionDraftRead)
def update_report_section_endpoint(
    section_id: UUID,
    data: ReportSectionDraftUpdate,
    session: SessionDep,
    current_user: AdminUserDep,
) -> ReportSectionDraftRead:
    """Update a report section draft (admin only)."""
    section = get_report_section_by_id(session, section_id)
    if section is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report section not found.",
        )
    try:
        section = update_report_section(session, section, data, current_user)
    except ValueError as e:
        msg = str(e)
        if "only admins" in msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "report_section_updated",
        "report_section",
        str(section.id),
        metadata_json={"reporting_cycle_id": str(section.reporting_cycle_id)},
    )
    return ReportSectionDraftRead.model_validate(section)

