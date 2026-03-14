"""
Department endpoints and service tests.

- 401 when unauthenticated for list/get/create/patch.
- Validation (422) for invalid create/update bodies.
- Service: duplicate code/name rejected; not found.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlmodel import SQLModel

from app.main import app
from app.models.department import Department
from app.models.enums import DepartmentType
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.department_service import (
    create_department,
    get_department_by_code,
    get_department_by_id,
    list_departments,
    update_department,
)

client = TestClient(app)


# --- Endpoint: unauthenticated returns 401 ---


def test_list_departments_without_auth_returns_401() -> None:
    response = client.get("/api/v1/departments")
    assert response.status_code == 401


def test_get_department_without_auth_returns_401() -> None:
    response = client.get("/api/v1/departments/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 401


def test_create_department_without_auth_returns_401() -> None:
    response = client.post(
        "/api/v1/departments",
        json={"name": "Faculty of Science", "code": "SCI", "type": "ACADEMIC"},
    )
    assert response.status_code == 401


def test_patch_department_without_auth_returns_401() -> None:
    response = client.patch(
        "/api/v1/departments/00000000-0000-0000-0000-000000000001",
        json={"name": "Updated"},
    )
    assert response.status_code == 401


# --- Schema validation (422) via endpoint (no auth, so 401; test schema separately) ---


def test_department_create_schema_name_too_short() -> None:
    with pytest.raises(ValueError, match="at least 2"):
        DepartmentCreate(name="A", code="AB", type=DepartmentType.ACADEMIC)


def test_department_create_schema_code_invalid_chars() -> None:
    with pytest.raises(ValueError, match="letters, numbers"):
        DepartmentCreate(name="Faculty", code="SC I", type=DepartmentType.ACADEMIC)


def test_department_create_schema_code_normalized_uppercase() -> None:
    d = DepartmentCreate(name="Faculty", code="sci", type=DepartmentType.ACADEMIC)
    assert d.code == "SCI"


# --- Service layer (in-memory SQLite, department table only) ---


@pytest.fixture
def department_session() -> Session:
    """Session with only Department table for service tests."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine, tables=[Department.__table__])
    with Session(engine) as session:
        yield session


def test_service_create_department(department_session: Session) -> None:
    data = DepartmentCreate(name="Faculty of Science", code="SCI", type=DepartmentType.ACADEMIC)
    dept = create_department(department_session, data)
    assert dept.id is not None
    assert dept.name == "Faculty of Science"
    assert dept.code == "SCI"
    assert dept.type == DepartmentType.ACADEMIC


def test_service_duplicate_code_rejected(department_session: Session) -> None:
    data = DepartmentCreate(name="Faculty of Science", code="SCI", type=DepartmentType.ACADEMIC)
    create_department(department_session, data)
    data2 = DepartmentCreate(name="Other", code="SCI", type=DepartmentType.OTHER)
    with pytest.raises(ValueError, match="code already exists"):
        create_department(department_session, data2)


def test_service_duplicate_name_rejected(department_session: Session) -> None:
    data = DepartmentCreate(name="Faculty of Science", code="SCI", type=DepartmentType.ACADEMIC)
    create_department(department_session, data)
    data2 = DepartmentCreate(name="Faculty of Science", code="FS", type=DepartmentType.ACADEMIC)
    with pytest.raises(ValueError, match="name already exists"):
        create_department(department_session, data2)


def test_service_get_department_by_id_not_found(department_session: Session) -> None:
    from uuid import uuid4
    result = get_department_by_id(department_session, uuid4())
    assert result is None


def test_service_list_departments_sorted_by_name(department_session: Session) -> None:
    create_department(
        department_session,
        DepartmentCreate(name="Zebra", code="ZE", type=DepartmentType.OTHER),
    )
    create_department(
        department_session,
        DepartmentCreate(name="Alpha", code="AL", type=DepartmentType.ACADEMIC),
    )
    depts = list_departments(department_session)
    assert len(depts) == 2
    assert depts[0].name == "Alpha"
    assert depts[1].name == "Zebra"


def test_service_update_department(department_session: Session) -> None:
    data = DepartmentCreate(name="Faculty of Science", code="SCI", type=DepartmentType.ACADEMIC)
    dept = create_department(department_session, data)
    update_data = DepartmentUpdate(name="Faculty of Sciences")
    updated = update_department(department_session, dept, update_data)
    assert updated.name == "Faculty of Sciences"
    assert updated.code == "SCI"
