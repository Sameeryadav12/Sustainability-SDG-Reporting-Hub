"""
Shared HTTP error helpers for consistent API responses (Step 12).

Use for common 404/403/400 cases; keeps messages readable and avoids tracebacks.
"""

from fastapi import HTTPException, status


def raise_404(detail: str = "Resource not found.") -> None:
    """Raise 404 NOT FOUND with a readable detail message."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_403(detail: str = "You are not allowed to perform this action.") -> None:
    """Raise 403 FORBIDDEN with a readable detail message."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def raise_400(detail: str) -> None:
    """Raise 400 BAD REQUEST with a readable detail message."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
