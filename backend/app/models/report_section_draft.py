"""
Report section draft model.

AI- or human-generated draft section for a report (per SDG, department, theme, or overall).
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, Text
from sqlmodel import Field, Relationship, SQLModel

from app.models.base_mixins import TimestampMixin
from app.models.enums import DraftGeneratedBy, ReportSectionScopeType, ReportSectionStatus


class ReportSectionDraft(SQLModel, TimestampMixin, table=True):
    """A draft section of a report (e.g. SDG 4 summary, department summary)."""

    __tablename__ = "report_section_draft"
    __table_args__ = {"schema": None}

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    reporting_cycle_id: UUID = Field(foreign_key="reporting_cycle.id", nullable=False, index=True)
    scope_type: ReportSectionScopeType = Field(nullable=False, index=True)
    scope_value: str = Field(max_length=256, nullable=False)
    title: str = Field(max_length=512, nullable=False)
    content_markdown: str = Field(sa_column=Column(Text(), nullable=False))
    status: ReportSectionStatus = Field(
        default=ReportSectionStatus.DRAFT, nullable=False, index=True
    )
    generated_by: DraftGeneratedBy = Field(nullable=False)
    last_generated_at: datetime | None = Field(default=None, nullable=True)

    reporting_cycle: "ReportingCycle" = Relationship(back_populates="report_section_drafts")
