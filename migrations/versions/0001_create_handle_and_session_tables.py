"""create handle and session tables

Revision ID: 0001
Revises:
Create Date: 2026-03-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "handles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("handle", sqlmodel.AutoString(length=39), nullable=False),
        sa.Column("github_login", sqlmodel.AutoString(), nullable=False),
        sa.Column("github_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_id"),
        sa.UniqueConstraint("github_login"),
        sa.UniqueConstraint("handle"),
    )
    op.create_index("ix_handles_handle", "handles", ["handle"])
    op.create_index("ix_handles_github_login", "handles", ["github_login"])

    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("handle_id", sa.Uuid(), nullable=False),
        sa.Column("github_token", sqlmodel.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["handle_id"], ["handles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_handle_id", "sessions", ["handle_id"])


def downgrade() -> None:
    op.drop_index("ix_sessions_handle_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_handles_github_login", table_name="handles")
    op.drop_index("ix_handles_handle", table_name="handles")
    op.drop_table("handles")
