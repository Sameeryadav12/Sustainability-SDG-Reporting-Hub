"""
Audit logging for important write actions (Step 12).

Logs to AuditLog model: user_id, action, entity_type, entity_id, optional metadata_json.
"""

from uuid import UUID

from sqlmodel import Session

from app.models.audit_log import AuditLog


def log_action(
    session: Session,
    user_id: UUID,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    metadata_json: dict | None = None,
) -> None:
    """
    Record an audit log entry. Action and entity_type should be short, stable strings.
    entity_id is optional (e.g. stringified UUID). metadata_json kept concise.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action[:128],
        entity_type=entity_type[:128],
        entity_id=str(entity_id)[:64] if entity_id is not None else None,
        metadata_json=metadata_json,
    )
    session.add(entry)
    session.commit()
