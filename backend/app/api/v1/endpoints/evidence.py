"""
Evidence file endpoints: list, create (metadata), upload (file), delete.

Step 9: POST .../evidence/upload for real file upload; GET list and DELETE unchanged.
"""

from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import CurrentUserDep
from app.core.http_errors import raise_404
from app.db.session import SessionDep
from app.schemas.evidence import EvidenceFileCreate, EvidenceFileRead
from app.services.contribution_service import get_contribution_by_id
from app.services.audit_service import log_action
from app.services.evidence_service import (
    create_evidence_file,
    delete_evidence_file,
    get_evidence_file_by_id,
    list_evidence_for_contribution,
    upload_evidence_file,
)

router = APIRouter(tags=["Contribution Evidence"])


@router.get("/contributions/{contribution_id}/evidence", response_model=list[EvidenceFileRead])
def list_evidence_endpoint(
    contribution_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[EvidenceFileRead]:
    """List evidence metadata for a contribution (authenticated; contribution access rules apply)."""
    contribution = get_contribution_by_id(session, contribution_id)
    if contribution is None:
        raise_404("Contribution not found.")
    try:
        items = list_evidence_for_contribution(session, contribution, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return [EvidenceFileRead.model_validate(e) for e in items]


@router.post(
    "/contributions/{contribution_id}/evidence/upload",
    response_model=EvidenceFileRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence_endpoint(
    contribution_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
    file: UploadFile = File(...),
) -> EvidenceFileRead:
    """Upload an evidence file for a contribution. Validates type, size, permissions."""
    contribution = get_contribution_by_id(session, contribution_id)
    if contribution is None:
        raise_404("Contribution not found.")
    try:
        content = await file.read()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read uploaded file.")
    try:
        evidence = upload_evidence_file(
            session,
            contribution,
            file_content=content,
            original_filename=file.filename or "file",
            content_type=file.content_type,
            current_user=current_user,
        )
    except ValueError as e:
        msg = str(e)
        if "not allowed" in msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    log_action(
        session,
        current_user.id,
        "evidence_uploaded",
        "evidence",
        str(evidence.id),
        metadata_json={"contribution_id": str(contribution_id), "file_name": evidence.file_name},
    )
    return EvidenceFileRead.model_validate(evidence)


@router.post(
    "/contributions/{contribution_id}/evidence",
    response_model=EvidenceFileRead,
    status_code=status.HTTP_201_CREATED,
)
def create_evidence_endpoint(
    contribution_id: UUID,
    data: EvidenceFileCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> EvidenceFileRead:
    """Create evidence metadata (authenticated; metadata only, no file upload). Viewers cannot create."""
    contribution = get_contribution_by_id(session, contribution_id)
    if contribution is None:
        raise_404("Contribution not found.")
    try:
        evidence = create_evidence_file(session, contribution, data, current_user)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    log_action(
        session,
        current_user.id,
        "evidence_created",
        "evidence",
        str(evidence.id),
        metadata_json={"contribution_id": str(contribution_id)},
    )
    return EvidenceFileRead.model_validate(evidence)


@router.delete("/evidence/{evidence_id}", status_code=status.HTTP_200_OK)
def delete_evidence_endpoint(
    evidence_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> dict[str, str]:
    """Delete evidence metadata (authenticated; only admin or coordinator for editable contribution)."""
    evidence = get_evidence_file_by_id(session, evidence_id)
    if evidence is None:
        raise_404("Evidence file not found.")
    try:
        contribution_id = str(evidence.contribution_id)
        delete_evidence_file(session, evidence, current_user)
    except ValueError as e:
        msg = str(e)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    log_action(
        session,
        current_user.id,
        "evidence_deleted",
        "evidence",
        str(evidence_id),
        metadata_json={"contribution_id": contribution_id},
    )
    return {"message": "Evidence file deleted."}
