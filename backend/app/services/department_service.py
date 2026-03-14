"""
Department service: list, get, create, update.
"""

from uuid import UUID

from sqlmodel import Session, select

from app.core.pagination import PAGINATION_LIMIT_DEFAULT, PAGINATION_SKIP_DEFAULT
from app.models.department import Department
from app.models.enums import DepartmentType
from app.schemas.department import DepartmentCreate, DepartmentUpdate


def list_departments(
    session: Session,
    skip: int = PAGINATION_SKIP_DEFAULT,
    limit: int = PAGINATION_LIMIT_DEFAULT,
) -> list[Department]:
    """Return departments sorted by name ascending, with optional pagination."""
    statement = (
        select(Department)
        .order_by(Department.name.asc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_department_by_id(session: Session, department_id: UUID) -> Department | None:
    """Return department by id or None."""
    return session.get(Department, department_id)


def get_department_by_code(session: Session, code: str) -> Department | None:
    """Return department by code (normalized uppercase) or None."""
    normalized = code.strip().upper()
    statement = select(Department).where(Department.code == normalized)
    return session.exec(statement).first()


def _get_department_by_name(session: Session, name: str) -> Department | None:
    """Return department by exact name (after strip) or None."""
    normalized = name.strip()
    statement = select(Department).where(Department.name == normalized)
    return session.exec(statement).first()


def create_department(session: Session, data: DepartmentCreate) -> Department:
    """
    Create a new department. Code must be unique; name should be unique.
    Raises ValueError with a readable message if duplicate code/name.
    """
    code = data.code.strip().upper()
    existing_code = get_department_by_code(session, code)
    if existing_code is not None:
        raise ValueError("A department with this code already exists.")

    name = data.name.strip()
    existing_name = _get_department_by_name(session, name)
    if existing_name is not None:
        raise ValueError("A department with this name already exists.")

    department = Department(
        name=name,
        code=code,
        type=data.type,
    )
    session.add(department)
    session.commit()
    session.refresh(department)
    return department


def update_department(
    session: Session,
    department: Department,
    data: DepartmentUpdate,
) -> Department:
    """
    Partially update a department. If name or code is changed, duplicate checks apply.
    Raises ValueError for duplicate code/name or "Department not found."
    """
    if data.name is not None:
        name = data.name.strip()
        other = _get_department_by_name(session, name)
        if other is not None and other.id != department.id:
            raise ValueError("A department with this name already exists.")
        department.name = name

    if data.code is not None:
        code = data.code.strip().upper()
        other = get_department_by_code(session, code)
        if other is not None and other.id != department.id:
            raise ValueError("A department with this code already exists.")
        department.code = code

    if data.type is not None:
        department.type = data.type

    session.add(department)
    session.commit()
    session.refresh(department)
    return department
