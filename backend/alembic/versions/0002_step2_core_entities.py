"""Step 2: Core entities, enums, relationships.

Revision ID: 0002
Revises: 0001
Create Date: (Step 2 — tables and enums)

Creates: PostgreSQL ENUM types, SDG, Department, User, ReportingCycle,
Contribution, ContributionMetric, EvidenceFile, Comment, ReportSectionDraft, AuditLog.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Reusable PostgreSQL ENUM types.
# We create them once with checkfirst=True, then reuse in all table definitions.
userrole_enum = postgresql.ENUM(
    "ADMIN",
    "DEPARTMENT_COORDINATOR",
    "VIEWER",
    name="userrole",
    create_type=False,
)
departmenttype_enum = postgresql.ENUM(
    "ACADEMIC",
    "OPERATIONS",
    "RESEARCH_CENTRE",
    "OTHER",
    name="departmenttype",
    create_type=False,
)
reportingcyclestatus_enum = postgresql.ENUM(
    "DRAFT",
    "OPEN",
    "CLOSED",
    "ARCHIVED",
    name="reportingcyclestatus",
    create_type=False,
)
contributiontype_enum = postgresql.ENUM(
    "RESEARCH",
    "TEACHING",
    "OPERATIONS",
    "POLICY",
    "COMMUNITY",
    "OTHER",
    name="contributiontype",
    create_type=False,
)
contributionstatus_enum = postgresql.ENUM(
    "DRAFT",
    "SUBMITTED",
    "UNDER_REVIEW",
    "APPROVED",
    "REJECTED",
    name="contributionstatus",
    create_type=False,
)
reportsectionscopetype_enum = postgresql.ENUM(
    "SDG",
    "DEPARTMENT",
    "THEME",
    "OVERALL",
    name="reportsectionscopetype",
    create_type=False,
)
reportsectionstatus_enum = postgresql.ENUM(
    "DRAFT",
    "REVIEWED",
    "FINAL",
    name="reportsectionstatus",
    create_type=False,
)
draftgeneratedby_enum = postgresql.ENUM(
    "AI",
    "HUMAN",
    name="draftgeneratedby",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    # Create PostgreSQL ENUM types (idempotent; safe if types already exist)
    userrole_enum.create(bind, checkfirst=True)
    departmenttype_enum.create(bind, checkfirst=True)
    reportingcyclestatus_enum.create(bind, checkfirst=True)
    contributiontype_enum.create(bind, checkfirst=True)
    contributionstatus_enum.create(bind, checkfirst=True)
    reportsectionscopetype_enum.create(bind, checkfirst=True)
    reportsectionstatus_enum.create(bind, checkfirst=True)
    draftgeneratedby_enum.create(bind, checkfirst=True)

    # 1. SDG — reference table, id 1–17
    op.create_table(
        "sdg",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon_url", sa.String(length=512), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. Department
    op.create_table(
        "department",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("type", departmenttype_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_department_code", "department", ["code"], unique=True)
    op.create_index("ix_department_name", "department", ["name"], unique=False)

    # 3. User
    op.create_table(
        "user",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("email", sa.String(length=256), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("role", userrole_enum, nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["department_id"], ["department.id"]),
    )
    op.create_index("ix_user_email", "user", ["email"], unique=True)

    # 4. ReportingCycle
    op.create_table(
        "reporting_cycle",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", reportingcyclestatus_enum, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("in_scope_sdgs", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reporting_cycle_year", "reporting_cycle", ["year"], unique=False)

    # 5. Contribution
    op.create_table(
        "contribution",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reporting_cycle_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("type", contributiontype_enum, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("primary_sdg_id", sa.Integer(), nullable=False),
        sa.Column("secondary_sdg_ids", sa.JSON(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", contributionstatus_enum, nullable=False, server_default=sa.text("'DRAFT'::contributionstatus")),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("approved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["reporting_cycle_id"], ["reporting_cycle.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["department.id"]),
        sa.ForeignKeyConstraint(["primary_sdg_id"], ["sdg.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["user.id"]),
    )
    op.create_index("ix_contribution_department_id", "contribution", ["department_id"], unique=False)
    op.create_index("ix_contribution_primary_sdg_id", "contribution", ["primary_sdg_id"], unique=False)
    op.create_index("ix_contribution_reporting_cycle_id", "contribution", ["reporting_cycle_id"], unique=False)
    op.create_index("ix_contribution_status", "contribution", ["status"], unique=False)
    op.create_index("ix_contribution_type", "contribution", ["type"], unique=False)

    # 6. ContributionMetric
    op.create_table(
        "contribution_metric",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("contribution_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("value_number", sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["contribution_id"], ["contribution.id"]),
    )

    # 7. EvidenceFile
    op.create_table(
        "evidence_file",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("contribution_id", sa.Uuid(), nullable=False),
        sa.Column("file_name", sa.String(length=512), nullable=False),
        sa.Column("file_url", sa.String(length=2048), nullable=False),
        sa.Column("file_type", sa.String(length=128), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["contribution_id"], ["contribution.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["user.id"]),
    )

    # 8. Comment
    op.create_table(
        "comment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("contribution_id", sa.Uuid(), nullable=False),
        sa.Column("author_user_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["contribution_id"], ["contribution.id"]),
        sa.ForeignKeyConstraint(["author_user_id"], ["user.id"]),
    )

    # 9. ReportSectionDraft
    op.create_table(
        "report_section_draft",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reporting_cycle_id", sa.Uuid(), nullable=False),
        sa.Column("scope_type", reportsectionscopetype_enum, nullable=False),
        sa.Column("scope_value", sa.String(length=256), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("status", reportsectionstatus_enum, nullable=False, server_default=sa.text("'DRAFT'::reportsectionstatus")),
        sa.Column("generated_by", draftgeneratedby_enum, nullable=False),
        sa.Column("last_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["reporting_cycle_id"], ["reporting_cycle.id"]),
    )
    op.create_index("ix_report_section_draft_reporting_cycle_id", "report_section_draft", ["reporting_cycle_id"], unique=False)
    op.create_index("ix_report_section_draft_scope_type", "report_section_draft", ["scope_type"], unique=False)
    op.create_index("ix_report_section_draft_status", "report_section_draft", ["status"], unique=False)

    # 10. AuditLog (column 'metadata' in DB; Python field metadata_json)
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=128), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_index("ix_audit_log_action", "audit_log", ["action"], unique=False)
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"], unique=False)
    op.create_index("ix_audit_log_entity_type", "audit_log", ["entity_type"], unique=False)
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (respect FKs)
    op.drop_table("audit_log")
    op.drop_index("ix_report_section_draft_status", table_name="report_section_draft")
    op.drop_index("ix_report_section_draft_scope_type", table_name="report_section_draft")
    op.drop_index(
        "ix_report_section_draft_reporting_cycle_id", table_name="report_section_draft"
    )
    op.drop_table("report_section_draft")
    op.drop_table("comment")
    op.drop_table("evidence_file")
    op.drop_table("contribution_metric")
    op.drop_index("ix_contribution_type", table_name="contribution")
    op.drop_index("ix_contribution_status", table_name="contribution")
    op.drop_index("ix_contribution_reporting_cycle_id", table_name="contribution")
    op.drop_index("ix_contribution_primary_sdg_id", table_name="contribution")
    op.drop_index("ix_contribution_department_id", table_name="contribution")
    op.drop_table("contribution")
    op.drop_index("ix_reporting_cycle_year", table_name="reporting_cycle")
    op.drop_table("reporting_cycle")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_table("user")
    op.drop_index("ix_department_name", table_name="department")
    op.drop_index("ix_department_code", table_name="department")
    op.drop_table("department")
    op.drop_table("sdg")

    # Drop ENUM types (idempotent)
    bind = op.get_bind()
    draftgeneratedby_enum.drop(bind, checkfirst=True)
    reportsectionstatus_enum.drop(bind, checkfirst=True)
    reportsectionscopetype_enum.drop(bind, checkfirst=True)
    contributionstatus_enum.drop(bind, checkfirst=True)
    contributiontype_enum.drop(bind, checkfirst=True)
    reportingcyclestatus_enum.drop(bind, checkfirst=True)
    departmenttype_enum.drop(bind, checkfirst=True)
    userrole_enum.drop(bind, checkfirst=True)
