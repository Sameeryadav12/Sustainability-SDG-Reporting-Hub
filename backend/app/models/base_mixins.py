"""
Reusable mixins for SQLModel table models.

Provides timestamp fields (created_at, updated_at) in UTC.
The migration adds server_default/onupdate in the DB; here we set Python defaults
so new instances have sensible values before flush.
"""

from datetime import datetime, timezone

from sqlmodel import Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    """
    Mixin adding created_at and updated_at (UTC).
    Use with SQLModel table models. Migration sets server_default and onupdate.
    """

    created_at: datetime = Field(default_factory=_utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=_utc_now, nullable=False)
