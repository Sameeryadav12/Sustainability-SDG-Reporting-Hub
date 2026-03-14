"""
Evidence file metadata request/response schemas.

Metadata only; no file bytes or upload URLs in this step.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


FILE_NAME_MAX_LEN = 512
FILE_URL_MAX_LEN = 2048
FILE_TYPE_MAX_LEN = 128


def _strip_str(v: str) -> str:
    if isinstance(v, str):
        return v.strip()
    return v


class EvidenceFileCreate(BaseModel):
    """Request schema for creating evidence metadata (no file upload)."""

    file_name: str
    file_url: str
    file_type: str

    @field_validator("file_name", mode="before")
    @classmethod
    def trim_file_name(cls, v: str) -> str:
        return _strip_str(v)

    @field_validator("file_name")
    @classmethod
    def file_name_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("file_name is required.")
        if len(v) > FILE_NAME_MAX_LEN:
            raise ValueError(f"file_name must be at most {FILE_NAME_MAX_LEN} characters.")
        return v

    @field_validator("file_url", mode="before")
    @classmethod
    def trim_file_url(cls, v: str) -> str:
        return _strip_str(v)

    @field_validator("file_url")
    @classmethod
    def file_url_valid(cls, v: str) -> str:
        if not v:
            raise ValueError("file_url is required.")
        if len(v) > FILE_URL_MAX_LEN:
            raise ValueError(f"file_url must be at most {FILE_URL_MAX_LEN} characters.")
        # Basic URL check: has scheme and netloc or path
        if not v.startswith(("http://", "https://")) and "://" not in v:
            # Allow relative or placeholder for now; strict URL can be added later
            pass
        return v

    @field_validator("file_type", mode="before")
    @classmethod
    def normalize_file_type(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("file_type")
    @classmethod
    def file_type_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("file_type is required.")
        if len(v) > FILE_TYPE_MAX_LEN:
            raise ValueError(f"file_type must be at most {FILE_TYPE_MAX_LEN} characters.")
        return v


class EvidenceFileRead(BaseModel):
    """Evidence file metadata response schema."""

    id: UUID
    contribution_id: UUID
    file_name: str
    file_url: str
    file_type: str
    uploaded_by_user_id: UUID
    uploaded_at: datetime

    model_config = {"from_attributes": True}
