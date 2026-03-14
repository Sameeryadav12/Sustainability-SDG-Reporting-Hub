"""
Contribution metrics service: list, create, delete.
"""

from uuid import UUID

from sqlmodel import Session, select

from app.models.contribution_metric import ContributionMetric
from app.models.contribution import Contribution
from app.schemas.metric import ContributionMetricCreate
from app.services.contribution_service import (
    ensure_can_manage_metrics,
    ensure_can_view_contribution,
    get_contribution_by_id,
)


def list_metrics_for_contribution(
    session: Session,
    contribution: Contribution,
    current_user: "User",
) -> list[ContributionMetric]:
    """List metrics for a contribution. User must have view access."""
    from app.models.user import User
    ensure_can_view_contribution(current_user, contribution)
    statement = (
        select(ContributionMetric)
        .where(ContributionMetric.contribution_id == contribution.id)
        .order_by(ContributionMetric.created_at.asc())
    )
    return list(session.exec(statement).all())


def create_metric(
    session: Session,
    contribution: Contribution,
    data: ContributionMetricCreate,
    current_user: "User",
) -> ContributionMetric:
    """Create a metric for the contribution. User must be allowed to manage metrics."""
    from app.models.user import User
    ensure_can_manage_metrics(session, current_user, contribution)
    metric = ContributionMetric(
        contribution_id=contribution.id,
        name=data.name.strip(),
        value_number=data.value_number,
        value_text=data.value_text.strip() if data.value_text else None,
        unit=data.unit.strip() if data.unit else None,
        year=data.year,
    )
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric


def get_metric_by_id(session: Session, metric_id: UUID) -> ContributionMetric | None:
    """Return metric by id or None."""
    return session.get(ContributionMetric, metric_id)


def delete_metric(
    session: Session,
    metric: ContributionMetric,
    current_user: "User",
) -> None:
    """Hard delete a metric. User must be allowed to manage metrics for the contribution."""
    from app.models.user import User
    contribution = session.get(Contribution, metric.contribution_id)
    if contribution is None:
        raise ValueError("Contribution not found.")
    ensure_can_manage_metrics(session, current_user, contribution)
    session.delete(metric)
    session.commit()
