"""Fix unique constraint for habit completions

Revision ID: 2867196b2955
Revises: 2dff08cdcd78
Create Date: 2025-09-28 23:27:44.645863

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2867196b2955"
down_revision: Union[str, Sequence[str], None] = "2dff08cdcd78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the existing non-unique index
    op.drop_index("ix_completions_habit_date", table_name="completions")

    # Create a UNIQUE index to prevent duplicate completions per habit per day
    # This enforces uniqueness at the database level
    op.create_index(
        "uq_completions_habit_date",
        "completions",
        ["habit_id", sa.text("DATE(completed_at)")],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the unique index
    op.drop_index("uq_completions_habit_date", table_name="completions")

    # Recreate the original non-unique index
    op.create_index(
        "ix_completions_habit_date",
        "completions",
        ["habit_id", sa.text("DATE(completed_at)")],
    )
