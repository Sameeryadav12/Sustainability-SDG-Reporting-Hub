"""
User model.

Stores identity, role, and optional department. Auth (login/JWT) is a later step.
"""

from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from app.models.base_mixins import TimestampMixin
from app.models.enums import UserRole


class User(SQLModel, TimestampMixin, table=True):
    """Platform user; may be admin, department coordinator, or viewer."""

    __tablename__ = "user"
    __table_args__ = {"schema": None}

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    name: str = Field(max_length=256, nullable=False)
    email: str = Field(max_length=256, nullable=False, unique=True, index=True)
    password_hash: str = Field(max_length=256, nullable=False)
    role: UserRole = Field(nullable=False)
    department_id: UUID | None = Field(default=None, foreign_key="department.id", nullable=True)
    is_active: bool = Field(default=True, nullable=False)

    department: "Department" = Relationship(back_populates="users")
    created_contributions: list["Contribution"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "Contribution.created_by_user_id"},
    )
    approved_contributions: list["Contribution"] = Relationship(
        back_populates="approved_by_user",
        sa_relationship_kwargs={"foreign_keys": "Contribution.approved_by_user_id"},
    )
    uploaded_evidence_files: list["EvidenceFile"] = Relationship(back_populates="uploaded_by_user")
    authored_comments: list["Comment"] = Relationship(back_populates="author_user")
    audit_logs: list["AuditLog"] = Relationship(back_populates="user")
