"""
Application models (SQLModel / SQLAlchemy).

Import all table models here so Alembic and the app see full metadata.
Import order matters for relationship resolution; keep dependencies first.
"""

from app.models.sdg import SDG
from app.models.department import Department
from app.models.user import User
from app.models.reporting_cycle import ReportingCycle
from app.models.contribution import Contribution
from app.models.contribution_metric import ContributionMetric
from app.models.evidence_file import EvidenceFile
from app.models.comment import Comment
from app.models.report_section_draft import ReportSectionDraft
from app.models.audit_log import AuditLog
from app.models.base_mixins import TimestampMixin
from app.models.enums import (
    ContributionStatus,
    ContributionType,
    DraftGeneratedBy,
    DepartmentType,
    ReportSectionScopeType,
    ReportSectionStatus,
    ReportingCycleStatus,
    UserRole,
)

__all__ = [
    "AuditLog",
    "Comment",
    "Contribution",
    "ContributionMetric",
    "Department",
    "EvidenceFile",
    "ReportSectionDraft",
    "ReportingCycle",
    "SDG",
    "TimestampMixin",
    "User",
    # Enums
    "ContributionStatus",
    "ContributionType",
    "DraftGeneratedBy",
    "DepartmentType",
    "ReportSectionScopeType",
    "ReportSectionStatus",
    "ReportingCycleStatus",
    "UserRole",
]
