"""
Seed the SDG reference table with the 17 UN Sustainable Development Goals.

Idempotent: inserts only missing rows (by id). Safe to run multiple times.
Run after migrations: alembic upgrade head && poetry run python -m app.db.seed_sdgs

Usage:
  From backend directory: poetry run python -m app.db.seed_sdgs
  Or: docker compose exec api poetry run python -m app.db.seed_sdgs
"""

from sqlmodel import Session, create_engine

from app.core.config import get_settings
from app.models.sdg import SDG

# Official UN SDG names and short descriptions (placeholder text)
SDG_DATA = [
    (1, "No Poverty", "End poverty in all its forms everywhere."),
    (2, "Zero Hunger", "End hunger, achieve food security and improved nutrition and promote sustainable agriculture."),
    (3, "Good Health and Well-being", "Ensure healthy lives and promote well-being for all at all ages."),
    (4, "Quality Education", "Ensure inclusive and equitable quality education and promote lifelong learning opportunities for all."),
    (5, "Gender Equality", "Achieve gender equality and empower all women and girls."),
    (6, "Clean Water and Sanitation", "Ensure availability and sustainable management of water and sanitation for all."),
    (7, "Affordable and Clean Energy", "Ensure access to affordable, reliable, sustainable and modern energy for all."),
    (8, "Decent Work and Economic Growth", "Promote sustained, inclusive and sustainable economic growth, full and productive employment and decent work for all."),
    (9, "Industry, Innovation and Infrastructure", "Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation."),
    (10, "Reduced Inequalities", "Reduce inequality within and among countries."),
    (11, "Sustainable Cities and Communities", "Make cities and human settlements inclusive, safe, resilient and sustainable."),
    (12, "Responsible Consumption and Production", "Ensure sustainable consumption and production patterns."),
    (13, "Climate Action", "Take urgent action to combat climate change and its impacts."),
    (14, "Life Below Water", "Conserve and sustainably use the oceans, seas and marine resources for sustainable development."),
    (15, "Life on Land", "Protect, restore and promote sustainable use of terrestrial ecosystems, sustainably manage forests, combat desertification, and halt and reverse land degradation and halt biodiversity loss."),
    (16, "Peace, Justice and Strong Institutions", "Promote peaceful and inclusive societies for sustainable development, provide access to justice for all and build effective, accountable and inclusive institutions at all levels."),
    (17, "Partnerships for the Goals", "Strengthen the means of implementation and revitalize the global partnership for sustainable development."),
]


def seed_sdgs(session: Session) -> int:
    """
    Insert the 17 SDGs if not already present. Returns number of rows inserted.
    """
    inserted = 0
    for sdg_id, name, description in SDG_DATA:
        existing = session.get(SDG, sdg_id)
        if existing is None:
            session.add(SDG(id=sdg_id, name=name, description=description, icon_url=None))
            inserted += 1
    session.commit()
    return inserted


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.sqlmodel_database_url)
    with Session(engine) as session:
        n = seed_sdgs(session)
        print(f"SDG seed: {n} row(s) inserted (17 total expected if DB was empty).")


if __name__ == "__main__":
    main()
