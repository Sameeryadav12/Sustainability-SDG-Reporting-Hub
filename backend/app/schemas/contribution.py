"""
Contribution request/response schemas.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

from app.models.enums import ContributionStatus, ContributionType


VALID_SDG_IDS = set(range(1, 18))  # 1 to 17
TITLE_MIN_LEN = 3
TITLE_MAX_LEN = 250
DESCRIPTION_MIN_LEN = 10


def _strip_str(v: str) -> str:
    if isinstance(v, str):
        return v.strip()
    return v


def _normalize_secondary_sdgs(value: list[int] | None) -> list[int] | None:
    if value is None:
        return None
    seen: set[int] = set()
    out: list[int] = []
    for i in value:
        if i in VALID_SDG_IDS and i not in seen:
            seen.add(i)
            out.append(i)
    return sorted(out) if out else None


class ContributionCreate(BaseModel):
    """Request schema for creating a contribution (under a reporting cycle)."""

    title: str
    type: ContributionType
    description: str
    primary_sdg_id: int
    secondary_sdg_ids: list[int] | None = None
    start_date: date | None = None
    end_date: date | None = None
    department_id: UUID | None = None  # Optional for admins; coordinators get it from their profile

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

    @field_validator("description", mode="before")
    @classmethod
    def trim_description(cls, v: str) -> str:
        return _strip_str(v)

    @field_validator("description")
    @classmethod
    def description_length(cls, v: str) -> str:
        if len(v) < DESCRIPTION_MIN_LEN:
            raise ValueError(f"Description must be at least {DESCRIPTION_MIN_LEN} characters.")
        return v

    @field_validator("primary_sdg_id")
    @classmethod
    def primary_sdg_valid(cls, v: int) -> int:
        if v not in VALID_SDG_IDS:
            raise ValueError("primary_sdg_id must be between 1 and 17.")
        return v

    @field_validator("secondary_sdg_ids", mode="before")
    @classmethod
    def normalize_secondary(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None
        return _normalize_secondary_sdgs([int(x) for x in v])

    @field_validator("secondary_sdg_ids")
    @classmethod
    def secondary_sdgs_valid(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None
        invalid = [i for i in v if i not in VALID_SDG_IDS]
        if invalid:
            raise ValueError("secondary_sdg_ids may only contain integers from 1 to 17.")
        return sorted(set(v))

    @model_validator(mode="after")
    def primary_not_in_secondary(self) -> "ContributionCreate":
        if self.secondary_sdg_ids and self.primary_sdg_id in self.secondary_sdg_ids:
            raise ValueError("primary_sdg_id must not appear in secondary_sdg_ids.")
        return self

    @model_validator(mode="after")
    def end_date_not_before_start(self) -> "ContributionCreate":
        if self.start_date is not None and self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("end_date must not be earlier than start_date.")
        return self


class ContributionUpdate(BaseModel):
    """Request schema for partial update of a contribution."""

    title: str | None = None
    type: ContributionType | None = None
    description: str | None = None
    primary_sdg_id: int | None = None
    secondary_sdg_ids: list[int] | None = None
    start_date: date | None = None
    end_date: date | None = None
    department_id: UUID | None = None  # Admin only if supported

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _strip_str(v)

    @field_validator("title")
    @classmethod
    def title_length(cls, v: str | None) -> str | None:
        if v is not None and (len(v) < TITLE_MIN_LEN or len(v) > TITLE_MAX_LEN):
            raise ValueError(f"Title must be between {TITLE_MIN_LEN} and {TITLE_MAX_LEN} characters.")
        return v

    @field_validator("description", mode="before")
    @classmethod
    def trim_description(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _strip_str(v)

    @field_validator("description")
    @classmethod
    def description_length(cls, v: str | None) -> str | None:
        if v is not None and len(v) < DESCRIPTION_MIN_LEN:
            raise ValueError(f"Description must be at least {DESCRIPTION_MIN_LEN} characters.")
        return v

    @field_validator("primary_sdg_id")
    @classmethod
    def primary_sdg_valid(cls, v: int | None) -> int | None:
        if v is not None and v not in VALID_SDG_IDS:
            raise ValueError("primary_sdg_id must be between 1 and 17.")
        return v

    @field_validator("secondary_sdg_ids", mode="before")
    @classmethod
    def normalize_secondary(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None
        return _normalize_secondary_sdgs([int(x) for x in v])

    @field_validator("secondary_sdg_ids")
    @classmethod
    def secondary_sdgs_valid(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return None
        invalid = [i for i in v if i not in VALID_SDG_IDS]
        if invalid:
            raise ValueError("secondary_sdg_ids may only contain integers from 1 to 17.")
        return sorted(set(v))

    @model_validator(mode="after")
    def primary_not_in_secondary(self) -> "ContributionUpdate":
        primary = self.primary_sdg_id
        secondary = self.secondary_sdg_ids
        if primary is not None and secondary and primary in secondary:
            raise ValueError("primary_sdg_id must not appear in secondary_sdg_ids.")
        return self

    @model_validator(mode="after")
    def end_date_not_before_start(self) -> "ContributionUpdate":
        if self.start_date is not None and self.end_date is not None:
            if self.end_date < self.start_date:
                raise ValueError("end_date must not be earlier than start_date.")
        return self


class ContributionRead(BaseModel):
    """Contribution response schema (full detail)."""

    id: UUID
    reporting_cycle_id: UUID
    reporting_cycle_name: str | None = None
    department_id: UUID
    department_name: str | None = None
    title: str
    type: ContributionType
    description: str
    primary_sdg_id: int
    primary_sdg: int | None = None  # Same as primary_sdg_id, for frontend display
    secondary_sdg_ids: list[int] | None
    start_date: date | None
    end_date: date | None
    status: ContributionStatus
    created_by_user_id: UUID
    approved_by_user_id: UUID | None
    approval_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContributionListItem(BaseModel):
    """Contribution list item (lighter) with resolved relation names for UI display."""

    id: UUID
    title: str
    type: ContributionType
    status: ContributionStatus
    primary_sdg_id: int
    primary_sdg: int  # Same as primary_sdg_id, for frontend (e.g. "SDG {primary_sdg}")
    department_id: UUID
    department_name: str | None = None
    reporting_cycle_id: UUID
    reporting_cycle_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContributionApproveRequest(BaseModel):
    """Request body for approve action (admin only)."""

    approval_notes: str | None = None

    @field_validator("approval_notes", mode="before")
    @classmethod
    def trim_notes(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _strip_str(v) if isinstance(v, str) else None


class ContributionRejectRequest(BaseModel):
    """Request body for reject action (admin only). Notes strongly encouraged."""

    approval_notes: str | None = None

    @field_validator("approval_notes", mode="before")
    @classmethod
    def trim_notes(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _strip_str(v) if isinstance(v, str) else None
