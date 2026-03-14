"""
Analytics endpoints.

GET /analytics/summary returns contributions per SDG, department, status, and type.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUserDep
from app.core.http_errors import raise_404
from app.db.session import SessionDep
from app.services.analytics_service import get_analytics_summary

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_analytics_summary_endpoint(
    session: SessionDep,
    current_user: CurrentUserDep,
    reporting_cycle_id: UUID = Query(..., description="Reporting cycle ID"),
) -> dict:
    """Return analytics summary for a reporting cycle. Authenticated users only."""
    try:
        summary = get_analytics_summary(session, reporting_cycle_id)
    except HTTPException:
        raise  # 404/403 etc — pass through unchanged
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics failed: {e!s}",
        ) from e
    if summary is None:
        raise_404("Reporting cycle not found.")
    return summary
