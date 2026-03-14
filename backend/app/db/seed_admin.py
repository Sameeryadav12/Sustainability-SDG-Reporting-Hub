"""
Bootstrap the first admin user from environment variables.

Idempotent: creates admin only if no user exists with FIRST_ADMIN_EMAIL.
Run after migrations. Password must meet strength policy (see README).

Usage:
  From backend directory: poetry run python -m app.db.seed_admin
  Or: docker compose exec api poetry run python -m app.db.seed_admin

Required env (or .env): FIRST_ADMIN_NAME, FIRST_ADMIN_EMAIL, FIRST_ADMIN_PASSWORD
"""

from sqlmodel import Session, create_engine

from app.core.config import get_settings
from app.core.security import hash_password, validate_password_strength
from app.models.enums import UserRole
from app.models.user import User
from app.services.user_service import get_user_by_email


def seed_admin(session: Session) -> bool:
    """
    Create first admin user if not already present. Returns True if created, False if skipped.
    Raises ValueError if password does not meet strength policy.
    """
    settings = get_settings()
    email = settings.first_admin_email.strip().lower()
    if not email:
        raise ValueError("FIRST_ADMIN_EMAIL must be set.")
    existing = get_user_by_email(session, email)
    if existing is not None:
        return False
    validate_password_strength(settings.first_admin_password)
    user = User(
        name=settings.first_admin_name.strip(),
        email=email,
        password_hash=hash_password(settings.first_admin_password),
        role=UserRole.ADMIN,
        department_id=None,
        is_active=True,
    )
    session.add(user)
    session.commit()
    return True


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.sqlmodel_database_url)
    with Session(engine) as session:
        try:
            created = seed_admin(session)
            if created:
                print(f"First admin created: {settings.first_admin_email}")
            else:
                print(f"Admin already exists: {settings.first_admin_email}. Skipped.")
        except ValueError as e:
            print(f"Error: {e}")
            raise SystemExit(1) from e


if __name__ == "__main__":
    main()
