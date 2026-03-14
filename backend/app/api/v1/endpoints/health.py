"""
Health check endpoints.

Used by load balancers, Docker HEALTHCHECK, and monitoring.
No database or heavy dependencies — fast response.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Response schema for health checks."""

    status: str
    project: str
    environment: str


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
)
def health() -> HealthResponse:
    """
    Return service health status. Use for liveness/readiness probes.
    """
    settings = get_settings()
    return HealthResponse(
        status="ok",
        project=settings.project_name,
        environment=settings.environment,
    )
