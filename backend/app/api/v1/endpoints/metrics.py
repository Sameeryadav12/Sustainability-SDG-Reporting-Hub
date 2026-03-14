"""
Contribution metrics endpoints: list, create, delete.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUserDep
from app.core.http_errors import raise_404
from app.db.session import SessionDep
from app.schemas.metric import ContributionMetricCreate, ContributionMetricRead
from app.services.contribution_service import get_contribution_by_id
from app.services.audit_service import log_action
from app.services.metric_service import (
    create_metric,
    delete_metric,
    get_metric_by_id,
    list_metrics_for_contribution,
)

router = APIRouter(tags=["Contribution Metrics"])


@router.get("/contributions/{contribution_id}/metrics", response_model=list[ContributionMetricRead])
def list_metrics_endpoint(
    contribution_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[ContributionMetricRead]:
    """List metrics for a contribution (authenticated; contribution access rules apply)."""
    contribution = get_contribution_by_id(session, contribution_id)
    if contribution is None:
        raise_404("Contribution not found.")
    try:
        items = list_metrics_for_contribution(session, contribution, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return [ContributionMetricRead.model_validate(m) for m in items]


@router.post(
    "/contributions/{contribution_id}/metrics",
    response_model=ContributionMetricRead,
    status_code=status.HTTP_201_CREATED,
)
def create_metric_endpoint(
    contribution_id: UUID,
    data: ContributionMetricCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ContributionMetricRead:
    """Create a metric for a contribution (authenticated; viewers cannot create)."""
    contribution = get_contribution_by_id(session, contribution_id)
    if contribution is None:
        raise_404("Contribution not found.")
    try:
        metric = create_metric(session, contribution, data, current_user)
    except ValueError as e:
        msg = str(e)
        if "not allowed" in msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "metric_created",
        "metric",
        str(metric.id),
        metadata_json={"contribution_id": str(contribution_id)},
    )
    return ContributionMetricRead.model_validate(metric)


@router.delete("/metrics/{metric_id}", status_code=status.HTTP_200_OK)
def delete_metric_endpoint(
    metric_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> dict[str, str]:
    """Delete a metric (authenticated; only admin or coordinator for editable contribution)."""
    metric = get_metric_by_id(session, metric_id)
    if metric is None:
        raise_404("Metric not found.")
    try:
        delete_metric(session, metric, current_user)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    log_action(
        session,
        current_user.id,
        "metric_deleted",
        "metric",
        str(metric_id),
        metadata_json={"contribution_id": str(metric.contribution_id)},
    )
    return {"message": "Metric deleted."}
