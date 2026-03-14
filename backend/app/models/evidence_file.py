"""
Evidence file model.

Stores metadata for files attached to a contribution (file bytes stored elsewhere).
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceFile(SQLModel, table=True):
    """Metadata for an evidence file linked to a contribution."""

    __tablename__ = "evidence_file"
    __table_args__ = {"schema": None}

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    contribution_id: UUID = Field(foreign_key="contribution.id", nullable=False)
    file_name: str = Field(max_length=512, nullable=False)
    file_url: str = Field(max_length=2048, nullable=False)
    file_type: str = Field(max_length=128, nullable=False)
    uploaded_by_user_id: UUID = Field(foreign_key="user.id", nullable=False)
    uploaded_at: datetime = Field(default_factory=_utc_now, nullable=False)

    contribution: "Contribution" = Relationship(back_populates="evidence_files")
    uploaded_by_user: "User" = Relationship(back_populates="uploaded_evidence_files")
