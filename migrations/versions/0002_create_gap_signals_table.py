"""create gap_signals table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gap_signals",
        sa.Column("query_hash", sqlmodel.AutoString(length=16), nullable=False),
        sa.Column("week_bucket", sqlmodel.AutoString(length=8), nullable=False),
        sa.Column("session_count", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("query_hash", "week_bucket"),
    )


def downgrade() -> None:
    op.drop_table("gap_signals")
