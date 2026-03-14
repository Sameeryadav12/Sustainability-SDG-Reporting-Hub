"""
User service: create user, get by email/id.
"""

from uuid import UUID

from sqlmodel import Session, select

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(session: Session, email: str) -> User | None:
    """Return user by email or None."""
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_user_by_id(session: Session, user_id: UUID) -> User | None:
    """Return user by id or None."""
    return session.get(User, user_id)


def create_user(session: Session, user_in: UserCreate) -> User:
    """
    Create a new user. Email is normalized and must be unique.
    Password is hashed; password_hash is never returned in API responses.
    Raises ValueError if email already exists (caller should map to 400).
    """
    email = user_in.email.strip().lower()
    existing = get_user_by_email(session, email)
    if existing is not None:
        raise ValueError("A user with this email already exists.")
    user = User(
        name=user_in.name.strip(),
        email=email,
        password_hash=hash_password(user_in.password),
        role=user_in.role,
        department_id=user_in.department_id,
        is_active=user_in.is_active,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
