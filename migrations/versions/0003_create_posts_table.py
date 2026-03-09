"""create posts table with Postgres FTS

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("github_repo", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("handle", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("tl_dr", sa.String(), nullable=False),
        sa.Column("context", sa.String(), nullable=True),
        sa.Column("detail", sa.String(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("date", sa.String(), nullable=False),
        sa.Column("quarantined", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "quarantine_reasons",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_repo", "file_path", name="uq_posts_repo_file"),
    )
    op.create_index("idx_posts_handle", "posts", ["handle"])
    op.create_index("idx_posts_github_repo", "posts", ["github_repo"])
    op.create_index(
        "idx_posts_search_vector",
        "posts",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("idx_posts_search_vector", table_name="posts")
    op.drop_index("idx_posts_github_repo", table_name="posts")
    op.drop_index("idx_posts_handle", table_name="posts")
    op.drop_table("posts")
