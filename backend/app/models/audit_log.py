"""
Audit log model.

Records user actions for compliance and debugging. Python field is metadata_json
to avoid conflict with SQLAlchemy's reserved 'metadata'; DB column is 'metadata'.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(SQLModel, table=True):
    """Log of user actions (entity_type, entity_id, action, optional JSON payload)."""

    __tablename__ = "audit_log"
    __table_args__ = {"schema": None}

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    user_id: UUID = Field(foreign_key="user.id", nullable=False, index=True)
    action: str = Field(max_length=128, nullable=False, index=True)
    entity_type: str = Field(max_length=128, nullable=False, index=True)
    entity_id: str | None = Field(default=None, max_length=64, nullable=True)
    # Python name 'metadata_json' to avoid SQLAlchemy reserved 'metadata'; DB column 'metadata'
    metadata_json: dict | None = Field(
        default=None,
        sa_column=Column("metadata", JSON, nullable=True),
    )
    created_at: datetime = Field(default_factory=_utc_now, nullable=False, index=True)

    user: "User" = Relationship(back_populates="audit_logs")
