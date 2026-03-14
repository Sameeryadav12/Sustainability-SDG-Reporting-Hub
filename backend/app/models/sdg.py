"""
SDG (Sustainable Development Goal) reference model.

Static reference table for the 17 UN SDGs. Seeded once; id 1–17.
"""

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class SDG(SQLModel, table=True):
    """
    UN Sustainable Development Goal reference.
    id 1–17; do not add more rows unless the UN adds goals.
    """

    __tablename__ = "sdg"
    __table_args__ = {"schema": None}

    id: int = Field(primary_key=True, ge=1, le=17)
    name: str = Field(max_length=256, nullable=False)
    description: str = Field(sa_column=Column(Text(), nullable=False))
    icon_url: str | None = Field(default=None, max_length=512, nullable=True)
