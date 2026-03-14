"""
Auth service: authenticate user and build token payload.
"""

from sqlmodel import Session, select

from app.core.security import verify_password
from app.models.user import User


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    """
    Return the User if email exists and password matches; otherwise None.
    Does not check is_active; caller may enforce that.
    """
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
