"""
Clean demo data: remove junk and test data so only a realistic demo set remains.

Use this before re-seeding (clean_demo_data then seed_demo_data) to get a
professional-looking dataset. Safe to run multiple times.

Keeps:
  - Users (including admin/demo) and SDGs; audit logs are not touched.
  - Departments with codes: SCI, OPS, RES, EDU.
  - Reporting cycles named exactly: Sustainability Report FY2024, Sustainability Report FY2025.

Removes:
  - Contributions (and their metrics, comments, evidence) in any other cycles.
  - Report sections in those cycles, then the cycles themselves.
  - Departments not in the whitelist, only if no contributions reference them.

Usage:
  docker compose exec api poetry run python -m app.db.clean_demo_data
  From backend: poetry run python -m app.db.clean_demo_data
"""

from sqlmodel import Session, create_engine, select

from app.core.config import get_settings
from app.models.comment import Comment
from app.models.contribution import Contribution
from app.models.contribution_metric import ContributionMetric
from app.models.department import Department
from app.models.evidence_file import EvidenceFile
from app.models.report_section_draft import ReportSectionDraft
from app.models.reporting_cycle import ReportingCycle

# Canonical demo set only (must match names/codes used in seed_demo_data)
DEPARTMENT_CODES = {"SCI", "OPS", "RES", "EDU"}
REPORTING_CYCLE_NAMES = {"Sustainability Report FY2024", "Sustainability Report FY2025"}
# Contribution titles to remove (junk/test entries)
TEST_CONTRIBUTION_TITLES = {"Test 1", "Test 2", "Test 3", "Test 4"}
# Report section titles to remove (SDG 1 and Education Department section)
REMOVE_REPORT_SECTION_TITLES = {"SDG 1 – No Poverty", "SDG 1 - No Poverty", "Education Department"}


def _delete_contribution_and_children(session: Session, contribution_id, deleted: dict) -> None:
    """Delete metrics, comments, evidence, then contribution for one contribution."""
    for m in session.exec(select(ContributionMetric).where(ContributionMetric.contribution_id == contribution_id)).all():
        session.delete(m)
        deleted["metrics"] += 1
    for c in session.exec(select(Comment).where(Comment.contribution_id == contribution_id)).all():
        session.delete(c)
        deleted["comments"] += 1
    for e in session.exec(select(EvidenceFile).where(EvidenceFile.contribution_id == contribution_id)).all():
        session.delete(e)
        deleted["evidence"] += 1


def clean_demo_data(session: Session) -> dict[str, int]:
    """Remove non-whitelist data and test contributions. Returns counts of deleted entities."""
    deleted = {"contributions": 0, "metrics": 0, "comments": 0, "evidence": 0, "report_sections": 0, "cycles": 0, "departments": 0}

    # Remove contributions titled "Test 1", "Test 2", "Test 3", "Test 4" (and their metrics, comments, evidence)
    test_contribs = list(session.exec(select(Contribution).where(Contribution.title.in_(TEST_CONTRIBUTION_TITLES))).all())
    for c in test_contribs:
        _delete_contribution_and_children(session, c.id, deleted)
        session.delete(c)
        deleted["contributions"] += 1
    if test_contribs:
        session.commit()

    # Remove specific report sections (SDG 1, Education Department)
    sections_to_remove = list(
        session.exec(select(ReportSectionDraft).where(ReportSectionDraft.title.in_(REMOVE_REPORT_SECTION_TITLES))).all()
    )
    for s in sections_to_remove:
        session.delete(s)
        deleted["report_sections"] += 1
    if sections_to_remove:
        session.commit()

    # Cycles to keep
    cycles_stmt = select(ReportingCycle).where(ReportingCycle.name.in_(REPORTING_CYCLE_NAMES))
    keep_cycle_ids = {c.id for c in session.exec(cycles_stmt).all()}
    all_cycles = list(session.exec(select(ReportingCycle)).all())
    remove_cycle_ids = {c.id for c in all_cycles if c.id not in keep_cycle_ids}

    # Contributions in removed cycles (and their metrics, comments, evidence)
    if remove_cycle_ids:
        contribs = list(session.exec(select(Contribution).where(Contribution.reporting_cycle_id.in_(remove_cycle_ids))).all())
        for c in contribs:
            _delete_contribution_and_children(session, c.id, deleted)
            session.delete(c)
            deleted["contributions"] += 1
        session.commit()

    # Report sections in removed cycles
    if remove_cycle_ids:
        sections = list(session.exec(select(ReportSectionDraft).where(ReportSectionDraft.reporting_cycle_id.in_(remove_cycle_ids))).all())
        for s in sections:
            session.delete(s)
            deleted["report_sections"] += 1
        session.commit()

    # Remove cycles not in whitelist
    for c in all_cycles:
        if c.id in remove_cycle_ids:
            session.delete(c)
            deleted["cycles"] += 1
    session.commit()

    # Departments not in whitelist (only if no contributions reference them)
    depts = list(session.exec(select(Department)).all())
    for d in depts:
        if d.code in DEPARTMENT_CODES:
            continue
        # Check no contributions use this department
        refs = session.exec(select(Contribution).where(Contribution.department_id == d.id).limit(1)).first()
        if refs is None:
            session.delete(d)
            deleted["departments"] += 1
    session.commit()

    return deleted


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.sqlmodel_database_url)
    with Session(engine) as session:
        deleted = clean_demo_data(session)
    print("Clean demo data completed.")
    print(f"  Deleted: {deleted}")


if __name__ == "__main__":
    main()
