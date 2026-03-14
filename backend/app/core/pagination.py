"""
Pagination constants and validation (Step 12).

Used by list endpoints: skip >= 0, 1 <= limit <= LIMIT_MAX.
"""

PAGINATION_SKIP_DEFAULT = 0
PAGINATION_LIMIT_DEFAULT = 100
PAGINATION_LIMIT_MAX = 200


def validate_pagination(skip: int, limit: int) -> None:
    """Raise ValueError if skip or limit are out of allowed range."""
    if skip < 0:
        raise ValueError("skip must be >= 0.")
    if limit < 1 or limit > PAGINATION_LIMIT_MAX:
        raise ValueError(f"limit must be between 1 and {PAGINATION_LIMIT_MAX}.")
