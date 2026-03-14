"""
Analytics service: contributions per SDG, department, status, type, and reporting cycle.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlmodel import Session

from app.models.contribution import Contribution
from app.models.contribution_metric import ContributionMetric
from app.models.reporting_cycle import ReportingCycle


def get_analytics_summary(
    session: Session,
    reporting_cycle_id: UUID,
) -> dict | None:
    """
    Return analytics summary for a reporting cycle.
    Returns None if the cycle does not exist.
    Shape matches frontend AnalyticsSummary type.
    """
    cycle = session.get(ReportingCycle, reporting_cycle_id)
    if cycle is None:
        return None

    try:
        stmt = (
            select(Contribution)
            .options(selectinload(Contribution.department))
            .where(Contribution.reporting_cycle_id == reporting_cycle_id)
        )
        contributions = list(session.exec(stmt).all())
    except Exception:
        contributions = []

    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_sdg: dict[int, int] = {}
    by_department: dict[str, dict] = {}  # department_id -> {id, name, count}

    def _get_attr(obj, name: str, default=None):
        """Get attribute or key from model or Row-like object."""
        try:
            return getattr(obj, name, default)
        except Exception:
            try:
                return obj[name] if hasattr(obj, "__getitem__") else default
            except Exception:
                return default

    for c in contributions:
        try:
            status_val = _get_attr(c, "status")
            s = status_val.value if hasattr(status_val, "value") else (str(status_val) if status_val else "DRAFT")
        except Exception:
            s = "DRAFT"
        by_status[s] = by_status.get(s, 0) + 1
        try:
            type_val = _get_attr(c, "type")
            t = type_val.value if hasattr(type_val, "value") else str(type_val or "OTHER")
        except Exception:
            t = "OTHER"
        by_type[t] = by_type.get(t, 0) + 1
        try:
            raw_sdg = _get_attr(c, "primary_sdg_id")
            if raw_sdg is None:
                sdg = 0
            else:
                sdg = int(raw_sdg)
        except (TypeError, ValueError):
            sdg = 0
        if sdg > 0:
            by_sdg[sdg] = by_sdg.get(sdg, 0) + 1
        dept_id = _get_attr(c, "department_id")
        dept_key = str(dept_id) if dept_id is not None else "none"
        if dept_key not in by_department:
            dept_name = None
            dept_rel = _get_attr(c, "department")
            if dept_rel is not None:
                dept_name = _get_attr(dept_rel, "name")
            by_department[dept_key] = {
                "department_id": str(dept_id) if dept_id is not None else None,
                "department_name": dept_name,
                "count": 0,
            }
        by_department[dept_key]["count"] += 1

    status_breakdown = [{"status": k, "count": v} for k, v in sorted(by_status.items())]
    type_breakdown = [{"type": k, "count": v} for k, v in sorted(by_type.items())]
    sdg_breakdown = [{"sdg": k, "count": v} for k, v in sorted(by_sdg.items())]
    department_breakdown = [
        {"department_id": v["department_id"], "department_name": v["department_name"], "count": v["count"]}
        for v in sorted(by_department.values(), key=lambda x: x["count"], reverse=True)
    ]

    try:
        metrics_count_stmt = (
            select(func.count(ContributionMetric.id))
            .join(Contribution, ContributionMetric.contribution_id == Contribution.id)
            .where(Contribution.reporting_cycle_id == reporting_cycle_id)
        )
        row = session.exec(metrics_count_stmt).one()
        if row is None:
            metrics_count = 0
        else:
            # Result can be a Row (tuple-like) or a scalar; avoid passing Row to int()
            try:
                val = row[0]
            except (TypeError, IndexError):
                val = row
            metrics_count = 0 if val is None else int(val)
    except Exception:
        metrics_count = 0

    return {
        "reporting_cycle_id": str(reporting_cycle_id),
        "reporting_cycle_name": cycle.name if cycle.name is not None else "",
        "total_contributions": len(contributions),
        "departments_with_contributions": len(by_department),
        "sdgs_covered": len(by_sdg),
        "metrics_count": metrics_count,
        "status_breakdown": status_breakdown,
        "sdg_breakdown": sdg_breakdown,
        "department_breakdown": department_breakdown,
        "type_breakdown": type_breakdown,
    }
