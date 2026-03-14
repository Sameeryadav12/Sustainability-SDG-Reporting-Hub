"""
Contribution comments endpoints: list, create.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUserDep
from app.db.session import SessionDep
from app.schemas.comment import CommentCreate, CommentRead
from app.services.comment_service import create_comment, list_comments_for_contribution
from app.services.contribution_service import get_contribution_by_id

router = APIRouter(tags=["Contribution Comments"])


@router.get("/contributions/{contribution_id}/comments", response_model=list[CommentRead])
def list_comments_endpoint(
    contribution_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[CommentRead]:
    """List comments for a contribution (authenticated; contribution access rules apply)."""
    contribution = get_contribution_by_id(session, contribution_id)
    if contribution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contribution not found.",
        )
    try:
        items = list_comments_for_contribution(session, contribution, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return [CommentRead.model_validate(c) for c in items]


@router.post(
    "/contributions/{contribution_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_comment_endpoint(
    contribution_id: UUID,
    data: CommentCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> CommentRead:
    """Create a comment (authenticated; admins and coordinators with access; viewers cannot)."""
    contribution = get_contribution_by_id(session, contribution_id)
    if contribution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contribution not found.",
        )
    try:
        comment = create_comment(session, contribution, data, current_user)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    return CommentRead.model_validate(comment)
