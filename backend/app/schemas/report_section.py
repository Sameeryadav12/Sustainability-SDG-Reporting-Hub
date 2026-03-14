"""
Report section draft request/response schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.enums import DraftGeneratedBy, ReportSectionScopeType, ReportSectionStatus


TITLE_MIN_LEN = 3
TITLE_MAX_LEN = 200


def _strip_str(v: str) -> str:
    if isinstance(v, str):
        return v.strip()
    return v


class ReportSectionDraftCreate(BaseModel):
    """Request schema for creating a report section draft (admin-only)."""

    reporting_cycle_id: UUID
    scope_type: ReportSectionScopeType
    scope_value: str
    title: str
    content_markdown: str
    status: ReportSectionStatus = ReportSectionStatus.DRAFT
    generated_by: DraftGeneratedBy = DraftGeneratedBy.HUMAN

    @field_validator("scope_value", mode="before")
    @classmethod
    def trim_scope_value(cls, v: str) -> str:
        return _strip_str(v)

    @field_validator("scope_value")
    @classmethod
    def scope_value_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("scope_value is required.")
        return v

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, v: str) -> str:
        return _strip_str(v)

    @field_validator("title")
    @classmethod
    def title_length(cls, v: str) -> str:
        if len(v) < TITLE_MIN_LEN:
            raise ValueError(f"Title must be at least {TITLE_MIN_LEN} characters.")
        if len(v) > TITLE_MAX_LEN:
            raise ValueError(f"Title must be at most {TITLE_MAX_LEN} characters.")
        return v

    @field_validator("content_markdown", mode="before")
    @classmethod
    def trim_content(cls, v: str) -> str:
        return _strip_str(v)

    @field_validator("content_markdown")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("content_markdown must not be empty.")
        return v


class ReportSectionDraftUpdate(BaseModel):
    """Request schema for updating a report section draft (admin-only)."""

    title: str | None = None
    content_markdown: str | None = None
    status: ReportSectionStatus | None = None
    generated_by: DraftGeneratedBy | None = None

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _strip_str(v)

    @field_validator("title")
    @classmethod
    def title_length(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if len(v) < TITLE_MIN_LEN:
            raise ValueError(f"Title must be at least {TITLE_MIN_LEN} characters.")
        if len(v) > TITLE_MAX_LEN:
            raise ValueError(f"Title must be at most {TITLE_MAX_LEN} characters.")
        return v

    @field_validator("content_markdown", mode="before")
    @classmethod
    def trim_content(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _strip_str(v)

    @field_validator("content_markdown")
    @classmethod
    def content_not_empty(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not v:
            raise ValueError("content_markdown must not be empty.")
        return v


class ReportSectionDraftRead(BaseModel):
    """Full report section draft response schema."""

    id: UUID
    reporting_cycle_id: UUID
    scope_type: ReportSectionScopeType
    scope_value: str
    title: str
    content_markdown: str
    status: ReportSectionStatus
    generated_by: DraftGeneratedBy
    last_generated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportSectionListItem(BaseModel):
    """List item view for report sections."""

    id: UUID
    reporting_cycle_id: UUID
    scope_type: ReportSectionScopeType
    scope_value: str
    title: str
    status: ReportSectionStatus
    generated_by: DraftGeneratedBy
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompiledReportResponse(BaseModel):
    """Response for compiled Markdown report export."""

    reporting_cycle_id: UUID
    cycle_name: str
    cycle_year: int
    section_count: int
    content_markdown: str

