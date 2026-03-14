"""
Comments service: list, create.
"""

from sqlmodel import Session, select

from app.models.comment import Comment
from app.models.contribution import Contribution
from app.schemas.comment import CommentCreate
from app.services.contribution_service import (
    ensure_can_add_comment,
    ensure_can_view_contribution,
)


def list_comments_for_contribution(
    session: Session,
    contribution: Contribution,
    current_user: "User",
) -> list[Comment]:
    """List comments for a contribution. User must have view access."""
    from app.models.user import User
    ensure_can_view_contribution(current_user, contribution)
    statement = (
        select(Comment)
        .where(Comment.contribution_id == contribution.id)
        .order_by(Comment.created_at.asc())
    )
    return list(session.exec(statement).all())


def create_comment(
    session: Session,
    contribution: Contribution,
    data: CommentCreate,
    current_user: "User",
) -> Comment:
    """Create a comment. User must be allowed to add comments (admin or coordinator with access)."""
    from app.models.user import User
    ensure_can_add_comment(current_user, contribution)
    comment = Comment(
        contribution_id=contribution.id,
        author_user_id=current_user.id,
        text=data.text.strip(),
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment
