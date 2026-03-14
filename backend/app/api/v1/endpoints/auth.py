"""
Auth endpoints: login and current user.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUserDep
from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import SessionDep
from app.schemas.auth import LoginRequest, TokenResponse, UserSummary
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, session: SessionDep) -> TokenResponse:
    """
    Authenticate with email and password; return JWT access token and user summary.
    Returns 401 for invalid credentials or inactive user.
    """
    user = authenticate_user(session, credentials.email, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user.",
        )
    settings = get_settings()
    token = create_access_token(
        subject=str(user.id),
        extra_claims={"role": user.role.value},
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserSummary.model_validate(user),
    )


@router.get("/me", response_model=UserSummary)
def me(current_user: CurrentUserDep) -> UserSummary:
    """Return the currently authenticated user."""
    return UserSummary.model_validate(current_user)
