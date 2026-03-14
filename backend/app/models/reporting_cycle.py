"""
Reporting cycle model.

A time-bounded period for collecting contributions (e.g. academic year).
"""

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON, Text
from sqlmodel import Field, Relationship, SQLModel

from app.models.base_mixins import TimestampMixin
from app.models.enums import ReportingCycleStatus


class ReportingCycle(SQLModel, TimestampMixin, table=True):
    """A reporting period with optional scope (which SDGs are in scope)."""

    __tablename__ = "reporting_cycle"
    __table_args__ = {"schema": None}

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    name: str = Field(max_length=256, nullable=False)
    year: int = Field(nullable=False, index=True)
    start_date: date = Field(nullable=False)
    end_date: date = Field(nullable=False)
    status: ReportingCycleStatus = Field(nullable=False)
    description: str | None = Field(default=None, sa_column=Column(Text(), nullable=True))
    # Store list of SDG ids (1–17) as JSON for portability and simplicity
    in_scope_sdgs: list[int] | None = Field(
        default=None,
        sa_column=Column("in_scope_sdgs", JSON, nullable=True),
    )

    contributions: list["Contribution"] = Relationship(back_populates="reporting_cycle")
    report_section_drafts: list["ReportSectionDraft"] = Relationship(
        back_populates="reporting_cycle"
    )
