"""
Auth and user endpoint tests.

Some tests require no DB (401/403). For full login/create flow use a test DB or run manually.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.security import validate_password_strength
from app.main import app

client = TestClient(app)


# --- Password validation (unit) ---


def test_validate_password_strength_accepts_strong() -> None:
    validate_password_strength("StrongPass1!")  # no raise


def test_validate_password_strength_rejects_short() -> None:
    with pytest.raises(ValueError, match="8 to 128"):
        validate_password_strength("Ab1!")


def test_validate_password_strength_rejects_no_uppercase() -> None:
    with pytest.raises(ValueError, match="uppercase"):
        validate_password_strength("strongpass1!")


def test_validate_password_strength_rejects_no_lowercase() -> None:
    with pytest.raises(ValueError, match="lowercase"):
        validate_password_strength("STRONGPASS1!")


def test_validate_password_strength_rejects_no_digit() -> None:
    with pytest.raises(ValueError, match="number"):
        validate_password_strength("StrongPass!")


def test_validate_password_strength_rejects_no_special() -> None:
    with pytest.raises(ValueError, match="special"):
        validate_password_strength("StrongPass1")


def test_validate_password_strength_rejects_too_long() -> None:
    """Max 128 characters; reject longer with clear message."""
    long_pass = "A1!" + "x" * 126  # 129 chars
    with pytest.raises(ValueError, match="8 to 128"):
        validate_password_strength(long_pass)


# --- Auth endpoints (no token / invalid) ---


def test_me_without_token_returns_401() -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_login_wrong_password_returns_401() -> None:
    """No user in DB or wrong password -> 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "WrongPass1!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json().get("detail", "")


# --- Users endpoint (admin-only) ---


def test_create_user_without_auth_returns_401() -> None:
    response = client.post(
        "/api/v1/users",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "StrongPass1!",
            "role": "VIEWER",
        },
    )
    assert response.status_code == 401


def test_create_user_weak_password_validation() -> None:
    """Password strength is validated by schema; unit tests cover validate_password_strength."""
    # Without valid admin token we get 401; with valid token and weak password we would get 422
    response = client.post(
        "/api/v1/users",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "weak",
            "role": "VIEWER",
        },
        headers={"Authorization": "Bearer invalid"},
    )
    assert response.status_code == 401
