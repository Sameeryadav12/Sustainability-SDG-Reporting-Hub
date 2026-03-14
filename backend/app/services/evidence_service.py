"""
Evidence file service: list, create (metadata or upload), delete.

Step 9: real file upload support; storage abstraction for local (and future cloud).
"""

from uuid import UUID

from sqlmodel import Session, select

from app.core.config import get_settings
from app.models.contribution import Contribution
from app.models.evidence_file import EvidenceFile
from app.schemas.evidence import EvidenceFileCreate
from app.services.contribution_service import (
    ensure_can_manage_evidence,
    ensure_can_view_contribution,
    get_contribution_by_id,
)
from app.services.storage_service import delete_file, save_upload


def list_evidence_for_contribution(
    session: Session,
    contribution: Contribution,
    current_user: "User",
) -> list[EvidenceFile]:
    """List evidence metadata for a contribution. User must have view access."""
    from app.models.user import User
    ensure_can_view_contribution(current_user, contribution)
    statement = (
        select(EvidenceFile)
        .where(EvidenceFile.contribution_id == contribution.id)
        .order_by(EvidenceFile.uploaded_at.desc())
    )
    return list(session.exec(statement).all())


def create_evidence_file(
    session: Session,
    contribution: Contribution,
    data: EvidenceFileCreate,
    current_user: "User",
) -> EvidenceFile:
    """Create evidence metadata (no file upload). User must be allowed to manage evidence."""
    from app.models.user import User
    ensure_can_manage_evidence(session, current_user, contribution)
    evidence = EvidenceFile(
        contribution_id=contribution.id,
        file_name=data.file_name.strip(),
        file_url=data.file_url.strip(),
        file_type=data.file_type.strip().lower(),
        uploaded_by_user_id=current_user.id,
    )
    session.add(evidence)
    session.commit()
    session.refresh(evidence)
    return evidence


def upload_evidence_file(
    session: Session,
    contribution: Contribution,
    file_content: bytes,
    original_filename: str,
    content_type: str | None,
    current_user: "User",
) -> EvidenceFile:
    """
    Save uploaded file via storage service and create EvidenceFile record.
    User must be allowed to manage evidence. Validates extension, size, non-empty.
    """
    from app.models.user import User
    ensure_can_manage_evidence(session, current_user, contribution)
    settings = get_settings()
    allowed = settings.allowed_evidence_extensions_list
    if len(file_content) == 0:
        raise ValueError("Uploaded file is empty.")
    if len(file_content) > settings.max_upload_size_bytes:
        raise ValueError("File exceeds the maximum allowed size.")
    ext = original_filename.rsplit(".", 1)[-1].strip().lower() if "." in original_filename else ""
    if not ext or ext not in allowed:
        raise ValueError("File type is not allowed.")
    result = save_upload(
        file_content,
        original_filename=original_filename,
        content_type=content_type,
        destination_subdir="evidence",
    )
    evidence = EvidenceFile(
        contribution_id=contribution.id,
        file_name=result.original_filename,
        file_url=result.file_url,
        file_type=ext,
        uploaded_by_user_id=current_user.id,
    )
    session.add(evidence)
    session.commit()
    session.refresh(evidence)
    return evidence


def get_evidence_file_by_id(session: Session, evidence_id: UUID) -> EvidenceFile | None:
    """Return evidence file by id or None."""
    return session.get(EvidenceFile, evidence_id)


def delete_evidence_file(
    session: Session,
    evidence_file: EvidenceFile,
    current_user: "User",
) -> None:
    """Hard delete evidence record and local file if stored under /uploads. User must be allowed to manage evidence."""
    from app.models.user import User
    contribution = session.get(Contribution, evidence_file.contribution_id)
    if contribution is None:
        raise ValueError("Contribution not found.")
    ensure_can_manage_evidence(session, current_user, contribution)
    if evidence_file.file_url.startswith("/uploads/"):
        storage_path = evidence_file.file_url[len("/uploads/"):].lstrip("/")
        delete_file(storage_path)
    session.delete(evidence_file)
    session.commit()
