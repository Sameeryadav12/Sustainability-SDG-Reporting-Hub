"""
Basic health endpoint tests.

Uses FastAPI TestClient — no live server or database required.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_message() -> None:
    """GET / returns a friendly message and links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Sustainability & SDG Reporting Hub" in data["message"]
    assert "docs" in data
    assert "health" in data


def test_health_returns_ok() -> None:
    """GET /health returns status ok and project info."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["project"] == "Sustainability & SDG Reporting Hub"
    assert "environment" in data


def test_api_v1_health_returns_ok() -> None:
    """GET /api/v1/health returns status ok and project info."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["project"] == "Sustainability & SDG Reporting Hub"
    assert "environment" in data
