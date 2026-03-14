"""
Report and CSV export endpoints.

Step 8: Markdown report export.
Step 10: CSV exports for contributions, metrics, evidence.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from app.api.deps import CurrentUserDep
from app.db.session import SessionDep
from app.schemas.report_section import CompiledReportResponse
from app.services.export_service import (
    export_contributions_csv,
    export_evidence_csv,
    export_metrics_csv,
)
from app.services.report_section_service import compile_markdown_report

router = APIRouter(tags=["Exports"])


@router.get("/exports/report.md", response_model=CompiledReportResponse)
def export_markdown_report_endpoint(
    reporting_cycle_id: UUID = Query(...),
    session: SessionDep = None,
    current_user: CurrentUserDep = None,
) -> CompiledReportResponse:
    """
    Compile a Markdown report for the given reporting cycle.

    Returns JSON containing reporting_cycle_id, cycle_name, cycle_year, section_count, and content_markdown.
    """
    try:
        summary = compile_markdown_report(session, reporting_cycle_id)
    except ValueError as e:
        msg = str(e)
        if "reporting cycle not found" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporting cycle not found.",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    return summary


@router.get("/exports/contributions.csv")
def export_contributions_csv_endpoint(
    reporting_cycle_id: UUID = Query(..., description="Reporting cycle ID"),
    session: SessionDep = None,
    current_user: CurrentUserDep = None,
) -> Response:
    """Download contributions for the reporting cycle as CSV. Authenticated."""
    try:
        content, filename = export_contributions_csv(session, reporting_cycle_id)
    except ValueError as e:
        if "reporting cycle not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporting cycle not found.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/exports/metrics.csv")
def export_metrics_csv_endpoint(
    reporting_cycle_id: UUID = Query(..., description="Reporting cycle ID"),
    session: SessionDep = None,
    current_user: CurrentUserDep = None,
) -> Response:
    """Download metrics for the reporting cycle as CSV. Authenticated."""
    try:
        content, filename = export_metrics_csv(session, reporting_cycle_id)
    except ValueError as e:
        if "reporting cycle not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporting cycle not found.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/exports/evidence.csv")
def export_evidence_csv_endpoint(
    reporting_cycle_id: UUID = Query(..., description="Reporting cycle ID"),
    session: SessionDep = None,
    current_user: CurrentUserDep = None,
) -> Response:
    """Download evidence file metadata for the reporting cycle as CSV. Authenticated."""
    try:
        content, filename = export_evidence_csv(session, reporting_cycle_id)
    except ValueError as e:
        if "reporting cycle not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporting cycle not found.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

