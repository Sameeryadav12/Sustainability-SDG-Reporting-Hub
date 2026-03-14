"""
Database session and engine setup for SQLModel.

Creates a sync engine and session factory. Use get_session() as a dependency
in FastAPI endpoints for database access.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from app.core.config import get_settings

# Create engine once at module load (sync — SQLModel uses sync by default)
_settings = get_settings()
engine = create_engine(
    _settings.sqlmodel_database_url,
    echo=_settings.debug,
    pool_pre_ping=True,
)


def get_session() -> Generator[Session, None, None]:
    """
    Yield a database session for the request. Use as FastAPI dependency.
    Session is closed automatically after request.
    """
    with Session(engine) as session:
        yield session


# Type alias for dependency injection: use SessionDep in route handlers
SessionDep = Annotated[Session, Depends(get_session)]
