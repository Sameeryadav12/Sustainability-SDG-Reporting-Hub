"""
CSV export service for contributions, metrics, and evidence (Step 10).

Uses Python's built-in csv module. Exports are filtered by reporting_cycle_id.
"""

import csv
import io
from uuid import UUID

from sqlmodel import Session, select

from app.models.contribution import Contribution
from app.models.contribution_metric import ContributionMetric
from app.models.department import Department
from app.models.evidence_file import EvidenceFile
from app.models.reporting_cycle import ReportingCycle
from app.services.reporting_cycle_service import get_reporting_cycle_by_id


def _str_or_empty(v) -> str:
    """Coerce value to string for CSV; None/empty becomes ''."""
    if v is None:
        return ""
    if isinstance(v, list):
        return "|".join(str(x) for x in v) if v else ""
    return str(v)


def build_csv_string(headers: list[str], rows: list[list]) -> str:
    """Build a UTF-8 CSV string from headers and rows. Rows are lists of values."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_str_or_empty(c) for c in row])
    return buf.getvalue()


def export_contributions_csv(session: Session, reporting_cycle_id: UUID) -> tuple[str, str]:
    """
    Export contributions for a reporting cycle as CSV.
    Returns (csv_content, suggested_filename).
    Raises ValueError("Reporting cycle not found.") if cycle does not exist.
    """
    cycle = get_reporting_cycle_by_id(session, reporting_cycle_id)
    if cycle is None:
        raise ValueError("Reporting cycle not found.")
    headers = [
        "contribution_id", "reporting_cycle_id", "reporting_cycle_name", "reporting_year",
        "department_id", "department_name", "title", "type", "description", "primary_sdg_id",
        "secondary_sdg_ids", "start_date", "end_date", "status",
        "created_by_user_id", "approved_by_user_id", "approval_notes", "created_at", "updated_at",
    ]
    stmt = (
        select(Contribution, ReportingCycle, Department)
        .join(ReportingCycle, Contribution.reporting_cycle_id == ReportingCycle.id)
        .join(Department, Contribution.department_id == Department.id)
        .where(Contribution.reporting_cycle_id == reporting_cycle_id)
        .order_by(Contribution.created_at.asc())
    )
    result = session.exec(stmt).all()
    rows = []
    for c, rc, dept in result:
        rows.append([
            c.id, c.reporting_cycle_id, rc.name, rc.year, dept.id, dept.name,
            c.title, c.type.value if hasattr(c.type, "value") else c.type, c.description,
            c.primary_sdg_id, c.secondary_sdg_ids, c.start_date, c.end_date,
            c.status.value if hasattr(c.status, "value") else c.status,
            c.created_by_user_id, c.approved_by_user_id, c.approval_notes,
            c.created_at.isoformat() if c.created_at else "", c.updated_at.isoformat() if c.updated_at else "",
        ])
    csv_content = build_csv_string(headers, rows)
    filename = f"contributions_{cycle.year}.csv"
    return csv_content, filename


def export_metrics_csv(session: Session, reporting_cycle_id: UUID) -> tuple[str, str]:
    """
    Export metrics (one row per metric) for contributions in the reporting cycle.
    Returns (csv_content, suggested_filename).
    Raises ValueError("Reporting cycle not found.") if cycle does not exist.
    """
    cycle = get_reporting_cycle_by_id(session, reporting_cycle_id)
    if cycle is None:
        raise ValueError("Reporting cycle not found.")
    headers = [
        "metric_id", "contribution_id", "contribution_title", "reporting_cycle_id",
        "reporting_cycle_name", "reporting_year", "department_id", "department_name",
        "metric_name", "value_number", "value_text", "unit", "metric_year", "created_at", "updated_at",
    ]
    stmt = (
        select(ContributionMetric, Contribution, ReportingCycle, Department)
        .join(Contribution, ContributionMetric.contribution_id == Contribution.id)
        .join(ReportingCycle, Contribution.reporting_cycle_id == ReportingCycle.id)
        .join(Department, Contribution.department_id == Department.id)
        .where(Contribution.reporting_cycle_id == reporting_cycle_id)
        .order_by(ContributionMetric.contribution_id, ContributionMetric.created_at.asc())
    )
    result = session.exec(stmt).all()
    rows = []
    for m, c, rc, dept in result:
        rows.append([
            m.id, m.contribution_id, c.title, rc.id, rc.name, rc.year, dept.id, dept.name,
            m.name, m.value_number, m.value_text, m.unit, m.year,
            m.created_at.isoformat() if m.created_at else "", m.updated_at.isoformat() if m.updated_at else "",
        ])
    csv_content = build_csv_string(headers, rows)
    filename = f"metrics_{cycle.year}.csv"
    return csv_content, filename


def export_evidence_csv(session: Session, reporting_cycle_id: UUID) -> tuple[str, str]:
    """
    Export evidence files (one row per file) for contributions in the reporting cycle.
    Returns (csv_content, suggested_filename).
    Raises ValueError("Reporting cycle not found.") if cycle does not exist.
    """
    cycle = get_reporting_cycle_by_id(session, reporting_cycle_id)
    if cycle is None:
        raise ValueError("Reporting cycle not found.")
    headers = [
        "evidence_id", "contribution_id", "contribution_title", "reporting_cycle_id",
        "reporting_cycle_name", "reporting_year", "department_id", "department_name",
        "file_name", "file_url", "file_type", "uploaded_by_user_id", "uploaded_at",
    ]
    stmt = (
        select(EvidenceFile, Contribution, ReportingCycle, Department)
        .join(Contribution, EvidenceFile.contribution_id == Contribution.id)
        .join(ReportingCycle, Contribution.reporting_cycle_id == ReportingCycle.id)
        .join(Department, Contribution.department_id == Department.id)
        .where(Contribution.reporting_cycle_id == reporting_cycle_id)
        .order_by(EvidenceFile.contribution_id, EvidenceFile.uploaded_at.asc())
    )
    result = session.exec(stmt).all()
    rows = []
    for e, c, rc, dept in result:
        rows.append([
            e.id, e.contribution_id, c.title, rc.id, rc.name, rc.year, dept.id, dept.name,
            e.file_name, e.file_url, e.file_type, e.uploaded_by_user_id,
            e.uploaded_at.isoformat() if e.uploaded_at else "",
        ])
    csv_content = build_csv_string(headers, rows)
    filename = f"evidence_{cycle.year}.csv"
    return csv_content, filename
