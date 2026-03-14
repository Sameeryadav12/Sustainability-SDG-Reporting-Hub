"""
Reporting cycle request/response schemas.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

from app.models.enums import ReportingCycleStatus


YEAR_MIN = 2000
YEAR_MAX = 2100
VALID_SDG_IDS = set(range(1, 18))  # 1 to 17


def _validate_sdg_ids(value: list[int], field_name: str = "in_scope_sdgs") -> None:
    """Raise ValueError if any id is not in 1–17. Message includes '1 to 17'."""
    invalid = [i for i in value if i not in VALID_SDG_IDS]
    if invalid:
        raise ValueError(
            f"{field_name} may only contain integers from 1 to 17; invalid value(s): {invalid}."
        )


class ReportingCycleCreate(BaseModel):
    """Request schema for creating a reporting cycle (admin-only)."""

    name: str
    year: int
    start_date: date
    end_date: date
    description: str | None = None
    in_scope_sdgs: list[int]

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("Name is required.")
        return v

    @field_validator("year")
    @classmethod
    def year_range(cls, v: int) -> int:
        if v < YEAR_MIN or v > YEAR_MAX:
            raise ValueError(f"Year must be between {YEAR_MIN} and {YEAR_MAX}.")
        return v

    @field_validator("in_scope_sdgs", mode="before")
    @classmethod
    def coerce_in_scope_sdgs_to_ints(cls, v: list[int]) -> list[int]:
        if not isinstance(v, list):
            raise ValueError("in_scope_sdgs must be a list of integers.")
        return [int(x) for x in v]

    @field_validator("in_scope_sdgs")
    @classmethod
    def in_scope_sdgs_valid(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("in_scope_sdgs must not be empty and must contain only SDG ids 1 to 17.")
        _validate_sdg_ids(v)
        return sorted(set(v))

    @model_validator(mode="after")
    def end_date_not_before_start(self) -> "ReportingCycleCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must not be earlier than start_date.")
        return self


class ReportingCycleUpdate(BaseModel):
    """Request schema for partial update of a reporting cycle (admin-only)."""

    name: str | None = None
    year: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    in_scope_sdgs: list[int] | None = None

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return v.strip() if isinstance(v, str) else v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v:
            raise ValueError("Name must not be empty.")
        return v

    @field_validator("year")
    @classmethod
    def year_range(cls, v: int | None) -> int | None:
        if v is not None and (v < YEAR_MIN or v > YEAR_MAX):
            raise ValueError(f"Year must be between {YEAR_MIN} and {YEAR_MAX}.")
        return v

    @field_validator("in_scope_sdgs", mode="before")
    @classmethod
    def coerce_in_scope_sdgs_to_ints(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("in_scope_sdgs must be a list of integers.")
        return [int(x) for x in v]

    @field_validator("in_scope_sdgs")
    @classmethod
    def in_scope_sdgs_valid(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None
        if not v:
            raise ValueError("in_scope_sdgs must not be empty and must contain only SDG ids 1 to 17.")
        _validate_sdg_ids(v)
        return sorted(set(v))

    @model_validator(mode="after")
    def dates_order(self) -> "ReportingCycleUpdate":
        start = self.start_date
        end = self.end_date
        if start is not None and end is not None and end < start:
            raise ValueError("end_date must not be earlier than start_date.")
        return self


class ReportingCycleRead(BaseModel):
    """Reporting cycle response schema."""

    id: UUID
    name: str
    year: int
    start_date: date
    end_date: date
    status: ReportingCycleStatus
    description: str | None
    in_scope_sdgs: list[int] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


ReportingCycleListItem = ReportingCycleRead


class ReportingCycleStatusActionResponse(BaseModel):
    """Optional response for open/close actions."""

    id: UUID
    status: ReportingCycleStatus
    message: str
