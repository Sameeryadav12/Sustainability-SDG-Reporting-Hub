"""
User-related request/response schemas.
"""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.models.enums import UserRole

from app.core.security import validate_password_strength


class UserCreate(BaseModel):
    """Request schema for creating a user (admin-only)."""

    name: str
    email: EmailStr
    password: str
    role: UserRole
    department_id: UUID | None = None
    is_active: bool = True

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
        return v

    @field_validator("name")
    @classmethod
    def name_length(cls, v: str) -> str:
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters.")
        return v

    @field_validator("name")
    @classmethod
    def name_allowed_chars(cls, v: str) -> str:
        # Allow letters (unicode), spaces, hyphens, apostrophes
        if not re.match(r"^[\w\s\-']+$", v) or not re.search(r"[a-zA-Z]", v):
            raise ValueError("Name must contain at least one letter and only letters, spaces, hyphens, or apostrophes.")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password")
    @classmethod
    def password_strong(cls, v: str) -> str:
        validate_password_strength(v)
        return v

    @model_validator(mode="after")
    def department_coordinator_has_department(self):
        if self.role == UserRole.DEPARTMENT_COORDINATOR and self.department_id is None:
            raise ValueError("A department coordinator must belong to a department.")
        return self


class UserRead(BaseModel):
    """User response schema (no password)."""

    id: UUID
    name: str
    email: str
    role: UserRole
    department_id: UUID | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
