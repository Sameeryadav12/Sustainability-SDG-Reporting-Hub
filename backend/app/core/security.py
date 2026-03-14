"""
Security utilities: password hashing, verification, and JWT access tokens.

Uses pwdlib with Argon2 for passwords (no passlib/bcrypt) and python-jose for JWT.
Validation is 8–128 characters with strength rules; no algorithm-specific length limit.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

# Single shared validator/hasher; validation runs before hashing everywhere
MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 128

# pwdlib recommended() uses Argon2; one instance for hash/verify
_password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Return a secure Argon2 hash of the password for storage. Validate first with validate_password_strength."""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return True if the plain password matches the stored hash."""
    return _password_hasher.verify(plain_password, password_hash)


def validate_password_strength(password: str) -> None:
    """
    Raise ValueError with a human-readable message if the password does not meet
    policy: 8–128 characters, uppercase, lowercase, digit, special character.
    Call this before hashing (e.g. in schema or seed_admin).
    """
    if len(password) < MIN_PASSWORD_LEN:
        raise ValueError(
            "Password must be 8 to 128 characters and include uppercase, "
            "lowercase, number, and special character."
        )
    if len(password) > MAX_PASSWORD_LEN:
        raise ValueError(
            "Password must be 8 to 128 characters and include uppercase, "
            "lowercase, number, and special character."
        )
    if not re.search(r"[A-Z]", password):
        raise ValueError(
            "Password must include at least one uppercase letter."
        )
    if not re.search(r"[a-z]", password):
        raise ValueError(
            "Password must include at least one lowercase letter."
        )
    if not re.search(r"\d", password):
        raise ValueError(
            "Password must include at least one number."
        )
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]", password):
        raise ValueError(
            "Password must include at least one special character."
        )


def create_access_token(subject: str | Any, extra_claims: dict[str, Any] | None = None) -> str:
    """
    Create a JWT access token. subject is typically the user id (str).
    extra_claims can include role, etc.
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate the JWT. Returns payload dict or None if invalid/expired.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
