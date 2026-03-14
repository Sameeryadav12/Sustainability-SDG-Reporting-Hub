"""
Contribution model.

Main record for a department's contribution (project, initiative, research, etc.)
in a reporting cycle, linked to primary and optional secondary SDGs.
"""

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON, Text
from sqlmodel import Field, Relationship, SQLModel

from app.models.base_mixins import TimestampMixin
from app.models.enums import ContributionStatus, ContributionType


class Contribution(SQLModel, TimestampMixin, table=True):
    """A single contribution (e.g. research, teaching, operations) in a reporting cycle."""

    __tablename__ = "contribution"
    __table_args__ = {"schema": None}

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    reporting_cycle_id: UUID = Field(foreign_key="reporting_cycle.id", nullable=False, index=True)
    department_id: UUID = Field(foreign_key="department.id", nullable=False, index=True)
    title: str = Field(max_length=512, nullable=False)
    type: ContributionType = Field(nullable=False, index=True)
    description: str = Field(sa_column=Column(Text(), nullable=False))
    primary_sdg_id: int = Field(foreign_key="sdg.id", nullable=False, index=True)
    secondary_sdg_ids: list[int] | None = Field(
        default=None,
        sa_column=Column("secondary_sdg_ids", JSON, nullable=True),
    )
    start_date: date | None = Field(default=None, nullable=True)
    end_date: date | None = Field(default=None, nullable=True)
    status: ContributionStatus = Field(default=ContributionStatus.DRAFT, nullable=False, index=True)
    created_by_user_id: UUID = Field(foreign_key="user.id", nullable=False)
    approved_by_user_id: UUID | None = Field(default=None, foreign_key="user.id", nullable=True)
    approval_notes: str | None = Field(default=None, sa_column=Column(Text(), nullable=True))

    reporting_cycle: "ReportingCycle" = Relationship(back_populates="contributions")
    department: "Department" = Relationship(back_populates="contributions")
    primary_sdg: "SDG" = Relationship()
    created_by_user: "User" = Relationship(
        back_populates="created_contributions",
        sa_relationship_kwargs={"foreign_keys": "Contribution.created_by_user_id"},
    )
    approved_by_user: "User" = Relationship(
        back_populates="approved_contributions",
        sa_relationship_kwargs={"foreign_keys": "Contribution.approved_by_user_id"},
    )
    metrics: list["ContributionMetric"] = Relationship(back_populates="contribution")
    evidence_files: list["EvidenceFile"] = Relationship(back_populates="contribution")
    comments: list["Comment"] = Relationship(back_populates="contribution")