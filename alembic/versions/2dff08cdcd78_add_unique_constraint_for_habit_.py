"""Add unique constraint for habit completion periods

Revision ID: 2dff08cdcd78
Revises: 9b2b4da698b4
Create Date: 2025-09-27 22:45:11.977252

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2dff08cdcd78"
down_revision: Union[str, Sequence[str], None] = "9b2b4da698b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add compound index to prevent duplicate completions in same day for daily habits
    # This helps prevent race conditions at database level
    op.create_index(
        "ix_completions_habit_date",
        "completions",
        ["habit_id", sa.text("DATE(completed_at)")],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_completions_habit_date", table_name="completions")
