"""
Contribution metric request/response schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator


NAME_MIN_LEN = 2
NAME_MAX_LEN = 120
YEAR_MIN = 2000
YEAR_MAX = 2100
UNIT_MAX_LEN = 64
VALUE_TEXT_MAX_LEN = 5000


def _strip_str(v: str) -> str:
    if isinstance(v, str):
        return v.strip()
    return v


class ContributionMetricCreate(BaseModel):
    """Request schema for creating a metric on a contribution."""

    name: str
    value_number: float | None = None
    value_text: str | None = None
    unit: str | None = None
    year: int | None = None

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, v: str) -> str:
        return _strip_str(v)

    @field_validator("name")
    @classmethod
    def name_length(cls, v: str) -> str:
        if len(v) < NAME_MIN_LEN:
            raise ValueError(f"Name must be at least {NAME_MIN_LEN} characters.")
        if len(v) > NAME_MAX_LEN:
            raise ValueError(f"Name must be at most {NAME_MAX_LEN} characters.")
        return v

    @field_validator("value_text", mode="before")
    @classmethod
    def trim_value_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _strip_str(v) if isinstance(v, str) else v

    @field_validator("unit", mode="before")
    @classmethod
    def trim_unit(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _strip_str(v) if isinstance(v, str) else v

    @field_validator("year")
    @classmethod
    def year_range(cls, v: int | None) -> int | None:
        if v is not None and (v < YEAR_MIN or v > YEAR_MAX):
            raise ValueError(f"Year must be between {YEAR_MIN} and {YEAR_MAX}.")
        return v

    @model_validator(mode="after")
    def at_least_one_value(self) -> "ContributionMetricCreate":
        if self.value_number is None and (self.value_text is None or not self.value_text.strip()):
            raise ValueError("At least one of value_number or value_text must be provided.")
        return self


class ContributionMetricRead(BaseModel):
    """Metric response schema."""

    id: UUID
    contribution_id: UUID
    name: str
    value_number: float | None
    value_text: str | None
    unit: str | None
    year: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
