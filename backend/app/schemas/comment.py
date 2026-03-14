"""
Comment request/response schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


TEXT_MIN_LEN = 3
TEXT_MAX_LEN = 2000


def _strip_str(v: str) -> str:
    if isinstance(v, str):
        return v.strip()
    return v


class CommentCreate(BaseModel):
    """Request schema for creating a comment on a contribution."""

    text: str

    @field_validator("text", mode="before")
    @classmethod
    def trim_text(cls, v: str) -> str:
        return _strip_str(v)

    @field_validator("text")
    @classmethod
    def text_length(cls, v: str) -> str:
        if len(v) < TEXT_MIN_LEN:
            raise ValueError(f"Text must be at least {TEXT_MIN_LEN} characters.")
        if len(v) > TEXT_MAX_LEN:
            raise ValueError(f"Text must be at most {TEXT_MAX_LEN} characters.")
        return v


class CommentRead(BaseModel):
    """Comment response schema."""

    id: UUID
    contribution_id: UUID
    author_user_id: UUID
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}
