"""
Contribution metric model.

Quantitative or qualitative metric for a contribution (e.g. number of students, description).
"""

from uuid import UUID, uuid4

from sqlalchemy import Column, Numeric, Text
from sqlmodel import Field, Relationship, SQLModel

from app.models.base_mixins import TimestampMixin


class ContributionMetric(SQLModel, TimestampMixin, table=True):
    """A single metric (numeric or text) attached to a contribution."""

    __tablename__ = "contribution_metric"
    __table_args__ = {"schema": None}

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    contribution_id: UUID = Field(foreign_key="contribution.id", nullable=False)
    name: str = Field(max_length=256, nullable=False)
    value_number: float | None = Field(
        default=None,
        sa_column=Column("value_number", Numeric(precision=20, scale=6), nullable=True),
    )
    value_text: str | None = Field(default=None, sa_column=Column(Text(), nullable=True))
    unit: str | None = Field(default=None, max_length=64, nullable=True)
    year: int | None = Field(default=None, nullable=True)

    contribution: "Contribution" = Relationship(back_populates="metrics")
