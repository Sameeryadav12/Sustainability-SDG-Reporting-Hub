"""Initial empty revision — foundation scaffold.

Revision ID: 0001
Revises:
Create Date: (Step 1 — no business tables yet)

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No tables yet — placeholder for future migrations."""
    pass


def downgrade() -> None:
    """No tables yet."""
    pass
