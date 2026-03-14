"""
SQLModel base and shared declarations.

Import this when defining new models so they are registered with Alembic.
"""

from sqlmodel import SQLModel

# Base class for all ORM models — subclasses will create tables
__all__ = ["SQLModel"]
