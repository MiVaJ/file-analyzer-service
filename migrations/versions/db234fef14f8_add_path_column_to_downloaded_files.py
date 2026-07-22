"""add path column to downloaded files

Revision ID: db234fef14f8
Revises: 04d0ffd13dd3
Create Date: 2026-07-22 16:07:41.653304

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "db234fef14f8"
down_revision: Union[str, Sequence[str], None] = "04d0ffd13dd3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "downloaded_files",
        sa.Column(
            "path",
            sa.String(length=500),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column(
        "downloaded_files",
        "path",
    )
