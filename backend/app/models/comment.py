"""
Comment model.

Review or discussion comment on a contribution.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, Text
from sqlmodel import Field, Relationship, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Comment(SQLModel, table=True):
    """A comment on a contribution by a user."""

    __tablename__ = "comment"
    __table_args__ = {"schema": None}

    id: UUID = Field(primary_key=True, default_factory=uuid4)
    contribution_id: UUID = Field(foreign_key="contribution.id", nullable=False)
    author_user_id: UUID = Field(foreign_key="user.id", nullable=False)
    text: str = Field(sa_column=Column(Text(), nullable=False))
    created_at: datetime = Field(default_factory=_utc_now, nullable=False)

    contribution: "Contribution" = Relationship(back_populates="comments")
    author_user: "User" = Relationship(back_populates="authored_comments")
