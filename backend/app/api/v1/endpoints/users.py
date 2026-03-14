"""
User endpoints: admin-only user creation.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import AdminUserDep
from app.db.session import SessionDep
from app.schemas.user import UserCreate, UserRead
from app.services.audit_service import log_action
from app.services.user_service import create_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    user_in: UserCreate,
    session: SessionDep,
    current_user: AdminUserDep,
) -> UserRead:
    """
    Create a new user (admin only). Email must be unique. Password must meet strength policy.
    Department coordinators must have department_id set.
    """
    try:
        user = create_user(session, user_in)
    except ValueError as e:
        msg = str(e)
        if "already exists" in msg.lower():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "user_created",
        "user",
        str(user.id),
        metadata_json={"email": user.email},
    )
    return UserRead.model_validate(user)
