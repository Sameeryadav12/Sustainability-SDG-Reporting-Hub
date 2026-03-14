"""
API v1 router — aggregates all v1 endpoints.

Include this router in the main app with prefix from settings (e.g. /api/v1).
"""

from fastapi import APIRouter

from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.comments import router as comments_router
from app.api.v1.endpoints.contributions import router as contributions_router
from app.api.v1.endpoints.departments import router as departments_router
from app.api.v1.endpoints.evidence import router as evidence_router
from app.api.v1.endpoints.exports import router as exports_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.metrics import router as metrics_router
from app.api.v1.endpoints.report_sections import router as report_sections_router
from app.api.v1.endpoints.reporting_cycles import router as reporting_cycles_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()

# Include endpoint routers (each can have its own prefix under v1)
api_router.include_router(health_router, prefix="")
api_router.include_router(auth_router, prefix="")
api_router.include_router(users_router, prefix="")
api_router.include_router(departments_router, prefix="")
api_router.include_router(reporting_cycles_router, prefix="")
api_router.include_router(contributions_router, prefix="")
api_router.include_router(metrics_router, prefix="")
api_router.include_router(comments_router, prefix="")
api_router.include_router(evidence_router, prefix="")
api_router.include_router(analytics_router, prefix="")
api_router.include_router(report_sections_router, prefix="")
api_router.include_router(exports_router, prefix="")
