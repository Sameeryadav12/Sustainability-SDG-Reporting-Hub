"""
FastAPI application entry point.

Creates the app, loads config, includes routers, and sets up docs.
"""

from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure upload dir exists, log readiness. Shutdown: cleanup if needed."""
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / "evidence").mkdir(exist_ok=True)
    print(f"[Startup] {settings.project_name} — environment: {settings.environment}")
    yield
    print("[Shutdown] Application stopping.")


def create_application() -> FastAPI:
    """Build and return the FastAPI application instance."""
    settings = get_settings()
    app = FastAPI(
        title=settings.project_name,
        description="Backend API for collecting sustainability data and mapping to UN SDGs.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS: use CORS_ORIGINS from env if set (comma-separated); else allow localhost + production
    _default_origins = [
        "http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176",
        "http://localhost:3000", "http://localhost:8080",
        "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://127.0.0.1:5175", "http://127.0.0.1:5176",
        "http://127.0.0.1:3000", "http://127.0.0.1:8080",
        "https://sustainability-sdg-reporting-hub.vercel.app",  # Production frontend (Vercel)
    ]
    _env_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    _cors_origins = _env_origins if _env_origins else _default_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Root message
    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "message": "This is the backend API for Sustainability & SDG Reporting Hub.",
            "docs": "/docs",
            "health": "/health",
            "api_v1_health": f"{settings.api_v1_prefix}/health",
        }

    # Mount versioned API
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # Local uploads (dev): serve files from upload_dir at /uploads
    upload_path = Path(settings.upload_dir).resolve()
    upload_path.mkdir(parents=True, exist_ok=True)
    (upload_path / "evidence").mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

    # Top-level health (no version prefix) — common for load balancers
    from app.api.v1.endpoints import health as health_endpoint
    app.include_router(health_endpoint.router, prefix="", tags=["health"])

    return app


app = create_application()
