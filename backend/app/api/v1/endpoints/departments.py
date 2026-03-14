"""
Department endpoints: list, get, create (admin), patch (admin).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import AdminUserDep, CurrentUserDep
from app.core.http_errors import raise_404
from app.core.pagination import (
    PAGINATION_LIMIT_DEFAULT,
    PAGINATION_LIMIT_MAX,
    PAGINATION_SKIP_DEFAULT,
    validate_pagination,
)
from app.db.session import SessionDep
from app.schemas.department import (
    DepartmentCreate,
    DepartmentListItem,
    DepartmentRead,
    DepartmentUpdate,
)
from app.services.audit_service import log_action
from app.services.department_service import (
    create_department,
    get_department_by_id,
    list_departments,
    update_department,
)

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=list[DepartmentListItem])
def list_departments_endpoint(
    session: SessionDep,
    current_user: CurrentUserDep,
    skip: int = Query(PAGINATION_SKIP_DEFAULT, ge=0, description="Number of records to skip"),
    limit: int = Query(PAGINATION_LIMIT_DEFAULT, ge=1, le=PAGINATION_LIMIT_MAX, description="Max records to return"),
) -> list[DepartmentListItem]:
    """List all departments (authenticated users). Sorted by name ascending. Supports skip/limit pagination."""
    try:
        validate_pagination(skip, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    departments = list_departments(session, skip=skip, limit=limit)
    return [DepartmentListItem.model_validate(d) for d in departments]


@router.get("/{department_id}", response_model=DepartmentRead)
def get_department_endpoint(
    department_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> DepartmentRead:
    """Get a department by id (authenticated users). Returns 404 if not found."""
    department = get_department_by_id(session, department_id)
    if department is None:
        raise_404("Department not found.")
    return DepartmentRead.model_validate(department)


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department_endpoint(
    data: DepartmentCreate,
    session: SessionDep,
    current_user: AdminUserDep,
) -> DepartmentRead:
    """Create a new department (admin only)."""
    try:
        department = create_department(session, data)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "department_created",
        "department",
        str(department.id),
        metadata_json={"name": department.name, "code": department.code},
    )
    return DepartmentRead.model_validate(department)


@router.patch("/{department_id}", response_model=DepartmentRead)
def update_department_endpoint(
    department_id: UUID,
    data: DepartmentUpdate,
    session: SessionDep,
    current_user: AdminUserDep,
) -> DepartmentRead:
    """Update a department (admin only). Partial update; duplicate name/code rejected."""
    department = get_department_by_id(session, department_id)
    if department is None:
        raise_404("Department not found.")
    try:
        department = update_department(session, department, data)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "department_updated",
        "department",
        str(department.id),
        metadata_json={"name": department.name},
    )
    return DepartmentRead.model_validate(department)
