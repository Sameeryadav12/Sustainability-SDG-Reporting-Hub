"""
Demo/development seed: minimal dataset for local and demo use (Step 12).

Idempotent: skips entities that already exist (by code, email, or name+year).
Requires: migrations applied, SDGs seeded (run seed_sdgs first if needed).
Safe to run multiple times.

Usage:
  docker compose exec api poetry run python -m app.db.seed_demo_data
  From backend directory: poetry run python -m app.db.seed_demo_data
"""

from datetime import date

from sqlmodel import Session, create_engine, select

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.comment import Comment
from app.models.contribution import Contribution
from app.models.contribution_metric import ContributionMetric
from app.models.department import Department
from app.models.enums import (
    ContributionStatus,
    ContributionType,
    DepartmentType,
    DraftGeneratedBy,
    ReportSectionScopeType,
    ReportSectionStatus,
    ReportingCycleStatus,
    UserRole,
)
from app.models.evidence_file import EvidenceFile
from app.models.report_section_draft import ReportSectionDraft
from app.models.reporting_cycle import ReportingCycle
from app.models.user import User

DEMO_ADMIN_EMAIL = "demo@example.com"
DEMO_ADMIN_PASSWORD = "DemoPassword1!"  # Meets strength policy; change in production

# Canonical demo reporting cycles (professional naming)
DEMO_CYCLE_NAMES = ("Sustainability Report FY2024", "Sustainability Report FY2025")


def ensure_sdgs(session: Session) -> None:
    """Ensure at least SDG 1 exists (for FK). If no SDGs, run seed_sdgs first."""
    from app.models.sdg import SDG
    existing = session.exec(select(SDG).limit(1)).first()
    if existing is None:
        raise RuntimeError("SDG table is empty. Run: poetry run python -m app.db.seed_sdgs")


def get_or_create_departments(session: Session) -> list[Department]:
    """Create demo departments by code if missing. Returns list of 4 departments."""
    result = []
    for code, name, dept_type in [
        ("SCI", "Faculty of Science", DepartmentType.ACADEMIC),
        ("OPS", "Operations & Facilities", DepartmentType.OPERATIONS),
        ("RES", "Research", DepartmentType.ACADEMIC),
        ("EDU", "Education Department", DepartmentType.ACADEMIC),
    ]:
        stmt = select(Department).where(Department.code == code)
        existing = session.exec(stmt).first()
        if existing is None:
            dept = Department(name=name, code=code, type=dept_type)
            session.add(dept)
            session.commit()
            session.refresh(dept)
            result.append(dept)
        else:
            result.append(existing)
    return result


def get_or_create_demo_admin(session: Session) -> User:
    """Create demo admin user if not present. Returns an admin user (for created_by_user_id)."""
    stmt = select(User).where(User.email == DEMO_ADMIN_EMAIL)
    existing = session.exec(stmt).first()
    if existing is not None:
        return existing
    admin = User(
        name="Demo Admin",
        email=DEMO_ADMIN_EMAIL,
        password_hash=hash_password(DEMO_ADMIN_PASSWORD),
        role=UserRole.ADMIN,
        department_id=None,
        is_active=True,
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    return admin


def get_or_create_reporting_cycles(session: Session) -> list[ReportingCycle]:
    """Create two reporting cycles if missing: prior year OPEN, current year DRAFT."""
    cycles = []
    today = date.today()
    year1, year2 = today.year - 1, today.year
    descriptions = {
        DEMO_CYCLE_NAMES[0]: f"Annual sustainability reporting period for fiscal year {year1}. Covers institutional activities, research, teaching, and operations aligned to the UN Sustainable Development Goals.",
        DEMO_CYCLE_NAMES[1]: f"Annual sustainability reporting period for fiscal year {year2}. Data collection in progress.",
    }
    for name, year, status in [
        (DEMO_CYCLE_NAMES[0], year1, ReportingCycleStatus.OPEN),
        (DEMO_CYCLE_NAMES[1], year2, ReportingCycleStatus.DRAFT),
    ]:
        stmt = select(ReportingCycle).where(
            ReportingCycle.name == name,
            ReportingCycle.year == year,
        )
        existing = session.exec(stmt).first()
        if existing is None:
            cycle = ReportingCycle(
                name=name,
                year=year,
                start_date=date(year, 1, 1),
                end_date=date(year, 12, 31),
                status=status,
                description=descriptions.get(name, f"Reporting cycle for {year}."),
                in_scope_sdgs=list(range(1, 18)),
            )
            session.add(cycle)
            session.commit()
            session.refresh(cycle)
            cycles.append(cycle)
        else:
            cycles.append(existing)
    if len(cycles) < 2:
        stmt = select(ReportingCycle).where(ReportingCycle.name.in_(DEMO_CYCLE_NAMES)).order_by(ReportingCycle.year.desc())
        cycles = list(session.exec(stmt).all())
    return cycles


# Realistic contribution definitions: (title, type, description, primary_sdg, secondary_sdgs, status)
CONTRIBUTION_SPECS = [
    (
        "Climate and Biodiversity Research Programme",
        ContributionType.RESEARCH,
        "Cross-disciplinary research on climate adaptation and ecosystem conservation, with partnerships for SDG 13 and 15.",
        13,
        [14, 15],
        ContributionStatus.SUBMITTED,
    ),
    (
        "Campus Carbon Reduction and Energy Efficiency",
        ContributionType.OPERATIONS,
        "Institutional energy audits, renewable energy uptake, and building efficiency measures supporting SDG 7 and 12.",
        7,
        [12, 13],
        ContributionStatus.SUBMITTED,
    ),
    (
        "Sustainable Materials and Circular Economy Research",
        ContributionType.RESEARCH,
        "Research initiatives on sustainable materials, waste reduction, and circular economy practices aligned to SDG 9 and 12.",
        9,
        [12],
        ContributionStatus.DRAFT,
    ),
    (
        "Sustainability in the Curriculum",
        ContributionType.TEACHING,
        "Integration of sustainability and SDG-related content across undergraduate and postgraduate programmes (SDG 4).",
        4,
        [10, 12],
        ContributionStatus.APPROVED,
    ),
]


def get_or_create_contributions(
    session: Session,
    open_cycle: ReportingCycle,
    departments: list[Department],
    admin: User,
) -> list[Contribution]:
    """Create realistic contributions in the OPEN cycle if none exist for it."""
    stmt = select(Contribution).where(Contribution.reporting_cycle_id == open_cycle.id).limit(1)
    if session.exec(stmt).first() is not None:
        stmt = select(Contribution).where(Contribution.reporting_cycle_id == open_cycle.id)
        return list(session.exec(stmt).all())
    contributions = []
    cycle_year = open_cycle.year
    for i, (dept, spec) in enumerate(zip(departments[:4], CONTRIBUTION_SPECS)):
        title, ctype, description, primary_sdg, secondary_sdgs, status = spec
        c = Contribution(
            reporting_cycle_id=open_cycle.id,
            department_id=dept.id,
            title=title,
            type=ctype,
            description=description,
            primary_sdg_id=primary_sdg,
            secondary_sdg_ids=secondary_sdgs,
            start_date=date(cycle_year, 1, 1),
            end_date=date(cycle_year, 12, 31),
            status=status,
            created_by_user_id=admin.id,
        )
        session.add(c)
        contributions.append(c)
    session.commit()
    for c in contributions:
        session.refresh(c)
    return contributions


def add_demo_metrics(session: Session, contribution: Contribution) -> None:
    """Add realistic metrics to a contribution if it has none."""
    stmt = select(ContributionMetric).where(ContributionMetric.contribution_id == contribution.id).limit(1)
    if session.exec(stmt).first() is not None:
        return
    # Metrics vary by contribution type for a professional look
    metrics_by_type = {
        ContributionType.RESEARCH: [
            ("Peer-reviewed publications", 8.0, None, "publications"),
            ("Research projects", 3.0, None, "projects"),
        ],
        ContributionType.OPERATIONS: [
            ("Carbon savings", 125.0, None, "tCO2e"),
            ("Renewable energy share", 35.0, None, "%"),
        ],
        ContributionType.TEACHING: [
            ("Students reached", 420.0, None, "students"),
            ("Courses updated", 12.0, None, "courses"),
        ],
    }
    metrics = metrics_by_type.get(contribution.type, [("Outputs", 1.0, None, "units")])
    for name, value_number, value_text, unit in metrics:
        m = ContributionMetric(
            contribution_id=contribution.id,
            name=name,
            value_number=value_number,
            value_text=value_text,
            unit=unit,
        )
        session.add(m)
    session.commit()


def add_demo_comments(session: Session, contribution: Contribution, admin: User) -> None:
    """Add one professional review comment if the contribution has none."""
    stmt = select(Comment).where(Comment.contribution_id == contribution.id).limit(1)
    if session.exec(stmt).first() is not None:
        return
    session.add(Comment(
        contribution_id=contribution.id,
        author_user_id=admin.id,
        text="Evidence and metrics reviewed. Ready for inclusion in the annual report.",
    ))
    session.commit()


def add_demo_evidence_metadata(session: Session, contribution: Contribution, admin: User) -> None:
    """Add one realistic evidence placeholder if contribution has no evidence."""
    stmt = select(EvidenceFile).where(EvidenceFile.contribution_id == contribution.id).limit(1)
    if session.exec(stmt).first() is not None:
        return
    # Plausible file names by type (no real file; placeholder for demo)
    name_hint = contribution.title[:20].replace(" ", "_").lower()
    file_name = f"{name_hint}_summary.pdf"
    session.add(EvidenceFile(
        contribution_id=contribution.id,
        file_name=file_name,
        file_url=f"/uploads/evidence/{file_name}",
        file_type="application/pdf",
        uploaded_by_user_id=admin.id,
    ))
    session.commit()


REPORT_SECTION_CONTENT = {
    "Executive Summary": (
        "This report summarises our institution's progress towards the UN Sustainable Development Goals "
        "during the reporting period. Key themes include research impact, curriculum integration, "
        "and operational sustainability. We have seen strong engagement across departments and "
        "continued alignment of strategic priorities with SDG targets."
    ),
    "SDG 1 – No Poverty": (
        "Our contributions to SDG 1 include community outreach programmes, financial inclusion research, "
        "and partnerships with local organisations. Activities are documented in department submissions "
        "and will be expanded in the full report."
    ),
    "SDG 4: Quality Education": (
        "Sustainability and SDG-related content has been integrated across multiple programmes. "
        "Student numbers and course updates are tracked in the contributions and metrics. "
        "This section will be finalised with input from the Education Department."
    ),
    "Education Department": (
        "The Education Department has led curriculum renewal and professional development in "
        "sustainability education. Key metrics and evidence are attached to the relevant contributions."
    ),
}


def add_demo_report_sections(session: Session, open_cycle: ReportingCycle, departments: list[Department]) -> None:
    """Add professional report section drafts for the cycle if none exist."""
    stmt = select(ReportSectionDraft).where(
        ReportSectionDraft.reporting_cycle_id == open_cycle.id,
    ).limit(1)
    if session.exec(stmt).first() is not None:
        return
    edu_dept = next((d for d in departments if d.code == "EDU"), None)
    sections = [
        (ReportSectionScopeType.OVERALL, "overall", "Executive Summary", REPORT_SECTION_CONTENT["Executive Summary"]),
        (ReportSectionScopeType.SDG, "1", "SDG 1 – No Poverty", REPORT_SECTION_CONTENT["SDG 1 – No Poverty"]),
        (ReportSectionScopeType.SDG, "4", "SDG 4: Quality Education", REPORT_SECTION_CONTENT["SDG 4: Quality Education"]),
    ]
    if edu_dept is not None:
        sections.append((
            ReportSectionScopeType.DEPARTMENT,
            str(edu_dept.id),
            "Education Department",
            REPORT_SECTION_CONTENT["Education Department"],
        ))
    for scope_type, scope_value, title, content in sections:
        section = ReportSectionDraft(
            reporting_cycle_id=open_cycle.id,
            scope_type=scope_type,
            scope_value=scope_value,
            title=title,
            content_markdown=content,
            status=ReportSectionStatus.DRAFT,
            generated_by=DraftGeneratedBy.HUMAN,
        )
        session.add(section)
    session.commit()


def seed_demo_data(session: Session) -> dict[str, int]:
    """
    Idempotent demo seed. Returns counts of created entities (for logging).
    Requires SDGs to exist; run seed_sdgs first if needed.
    """
    ensure_sdgs(session)
    departments = get_or_create_departments(session)
    admin = get_or_create_demo_admin(session)
    cycles = get_or_create_reporting_cycles(session)
    open_cycle = next((c for c in cycles if c.status == ReportingCycleStatus.OPEN), cycles[0])
    contributions = get_or_create_contributions(session, open_cycle, departments, admin)
    for c in contributions:
        add_demo_metrics(session, c)
    for c in contributions[:2]:
        add_demo_comments(session, c, admin)
    for c in contributions[:2]:
        add_demo_evidence_metadata(session, c, admin)
    add_demo_report_sections(session, open_cycle, departments)
    return {
        "departments": len(departments),
        "reporting_cycles": len(cycles),
        "contributions": len(contributions),
    }


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.sqlmodel_database_url)
    with Session(engine) as session:
        try:
            counts = seed_demo_data(session)
            print("Demo seed completed.")
            print(f"  Departments: {counts['departments']}, Cycles: {counts['reporting_cycles']}, Contributions: {counts['contributions']}")
            print(f"  Demo admin: {DEMO_ADMIN_EMAIL} (password: {DEMO_ADMIN_PASSWORD!r})")
        except RuntimeError as e:
            print(f"Error: {e}")
            raise SystemExit(1) from e


if __name__ == "__main__":
    main()
