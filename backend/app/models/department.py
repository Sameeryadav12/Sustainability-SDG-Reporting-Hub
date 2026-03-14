"""
Department (organisational unit) model.

Examples: Faculty of Science, Facilities, Research Office.
"""

from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from app.models.base_mixins import TimestampMixin
from app.models.enums import DepartmentType


class Department(SQLModel, TimestampMixin, table=True):
    """Organisational unit that can submit contributions."""

    __tablename__ = "department"
    __table_args__ = {"schema": None}

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    name: str = Field(max_length=256, nullable=False, index=True)
    code: str = Field(max_length=32, nullable=False, unique=True, index=True)
    type: DepartmentType = Field(nullable=False)

    # Relationships — populated by SQLModel/relationship()
    users: list["User"] = Relationship(back_populates="department")
    contributions: list["Contribution"] = Relationship(back_populates="department")

