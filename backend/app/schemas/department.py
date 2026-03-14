"""
Department request/response schemas.
"""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.enums import DepartmentType


# Code: letters, numbers, underscores, hyphens; normalized to uppercase
_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_\-]+$")
NAME_MIN_LEN = 2
NAME_MAX_LEN = 150
CODE_MIN_LEN = 2
CODE_MAX_LEN = 20


def _strip_str(v: str) -> str:
    if isinstance(v, str):
        return v.strip()
    return v


def _normalize_code(v: str) -> str:
    v = _strip_str(v)
    return v.upper() if v else v


class DepartmentCreate(BaseModel):
    """Request schema for creating a department (admin-only)."""

    name: str
    code: str
    type: DepartmentType

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return _strip_str(v)

    @field_validator("name")
    @classmethod
    def name_length(cls, v: str) -> str:
        if len(v) < NAME_MIN_LEN:
            raise ValueError(f"Name must be at least {NAME_MIN_LEN} characters.")
        if len(v) > NAME_MAX_LEN:
            raise ValueError(f"Name must be at most {NAME_MAX_LEN} characters.")
        return v

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return _normalize_code(v)

    @field_validator("code")
    @classmethod
    def code_format(cls, v: str) -> str:
        if len(v) < CODE_MIN_LEN:
            raise ValueError(f"Code must be at least {CODE_MIN_LEN} characters.")
        if len(v) > CODE_MAX_LEN:
            raise ValueError(f"Code must be at most {CODE_MAX_LEN} characters.")
        if not _CODE_PATTERN.match(v):
            raise ValueError("Code may only contain letters, numbers, underscores, and hyphens.")
        return v.upper()


class DepartmentUpdate(BaseModel):
    """Request schema for partial update of a department (admin-only)."""

    name: str | None = None
    code: str | None = None
    type: DepartmentType | None = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _strip_str(v)

    @field_validator("name")
    @classmethod
    def name_length(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if len(v) < NAME_MIN_LEN:
            raise ValueError(f"Name must be at least {NAME_MIN_LEN} characters.")
        if len(v) > NAME_MAX_LEN:
            raise ValueError(f"Name must be at most {NAME_MAX_LEN} characters.")
        return v

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _normalize_code(v)

    @field_validator("code")
    @classmethod
    def code_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if len(v) < CODE_MIN_LEN:
            raise ValueError(f"Code must be at least {CODE_MIN_LEN} characters.")
        if len(v) > CODE_MAX_LEN:
            raise ValueError(f"Code must be at most {CODE_MAX_LEN} characters.")
        if not _CODE_PATTERN.match(v):
            raise ValueError("Code may only contain letters, numbers, underscores, and hyphens.")
        return v.upper()


class DepartmentRead(BaseModel):
    """Department response schema."""

    id: UUID
    name: str
    code: str
    type: DepartmentType
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# List items can use the same as read for now
DepartmentListItem = DepartmentRead
