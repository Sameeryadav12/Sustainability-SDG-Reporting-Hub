"""
Auth-related request/response schemas.
"""

from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class UserSummary(BaseModel):
    """Minimal user info for embedding in token response or /auth/me."""

    id: UUID
    name: str
    email: str
    role: str
    department_id: UUID | None
    is_active: bool

    @field_validator("role", mode="before")
    @classmethod
    def role_to_str(cls, v: str | UserRole) -> str:
        if isinstance(v, UserRole):
            return v.value
        return v

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT access token and basic user info."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary
