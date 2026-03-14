"""
Verify the app and auth stack import without runtime errors.
Run after: poetry install (or docker compose exec api poetry install)
  python scripts/verify_startup.py
  or: poetry run python scripts/verify_startup.py
"""
import sys


def main() -> int:
    try:
        from app.main import app  # noqa: F401
        print("app.main: OK")
        from app.core.security import hash_password, verify_password, validate_password_strength
        validate_password_strength("StrongPass1!")
        h = hash_password("StrongPass1!")
        assert verify_password("StrongPass1!", h)
        print("app.core.security (pwdlib/Argon2): OK")
        from app.db.seed_admin import seed_admin  # noqa: F401
        print("app.db.seed_admin: OK")
        from app.api.v1.endpoints import contributions  # noqa: F401
        print("app.api.v1.endpoints.contributions: OK")
        from app.api.v1.endpoints import metrics, comments, evidence  # noqa: F401
        print("app.api.v1.endpoints.metrics, comments, evidence: OK")
        from app.api.v1.endpoints import analytics, report_sections, exports  # noqa: F401
        print("app.api.v1.endpoints.analytics, report_sections, exports: OK")
        from app.services.export_service import export_contributions_csv  # noqa: F401
        print("app.services.export_service: OK")
        from app.services.ai_report_service import generate_report_section  # noqa: F401
        print("app.services.ai_report_service: OK")
        print("All imports and auth flow OK.")
        return 0
    except Exception as e:
        print(f"Verification failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
