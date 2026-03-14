"""
Request/response schemas for AI report section generation (Step 11).
"""

from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.enums import ReportSectionScopeType
from app.schemas.report_section import ReportSectionDraftRead


TARGET_WORD_COUNT_MIN = 100
TARGET_WORD_COUNT_MAX = 1200


def _strip_str(v: str) -> str:
    if isinstance(v, str):
        return v.strip()
    return v


class ReportSectionGenerateRequest(BaseModel):
    """Request body for POST /report-sections/generate (admin only)."""

    reporting_cycle_id: UUID
    scope_type: ReportSectionScopeType
    scope_value: str
    title: str | None = None
    target_word_count: int = 500
    overwrite_existing: bool = True

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

    @field_validator("target_word_count")
    @classmethod
    def target_word_count_range(cls, v: int) -> int:
        if v < TARGET_WORD_COUNT_MIN or v > TARGET_WORD_COUNT_MAX:
            raise ValueError(
                f"target_word_count must be between {TARGET_WORD_COUNT_MIN} and {TARGET_WORD_COUNT_MAX}."
            )
        return v


class ReportSectionGenerateResponse(ReportSectionDraftRead):
    """Response for generate endpoint; section data plus optional metadata."""

    source_contribution_count: int | None = None
