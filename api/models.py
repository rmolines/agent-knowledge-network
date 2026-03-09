from datetime import UTC, datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint


class GapSignal(SQLModel, table=True):
    __tablename__ = "gap_signals"

    query_hash: str = Field(primary_key=True, max_length=16)  # sha256[:16] — one-way, never raw query
    week_bucket: str = Field(primary_key=True, max_length=8)  # e.g. "2026-W10"
    session_count: int = Field(default=1)


class Handle(SQLModel, table=True):
    __tablename__ = "handles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    handle: str = Field(unique=True, index=True, max_length=39)  # mirrors GitHub username limit
    github_login: str = Field(unique=True, index=True)
    github_id: int = Field(unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    sessions: list["Session"] = Relationship(back_populates="handle")


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    handle_id: UUID = Field(foreign_key="handles.id", index=True)
    github_token: str  # OAuth token — used for GitHub API calls on behalf of the user
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    expires_at: datetime

    handle: Handle | None = Relationship(back_populates="sessions")


class Post(SQLModel, table=True):
    """Indexed post. search_vector is a Postgres tsvector built from title + tl_dr + tags."""

    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint("github_repo", "file_path", name="uq_posts_repo_file"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    github_repo: str = Field(index=True)
    file_path: str
    handle: str = Field(index=True)
    title: str
    tl_dr: str
    context: str | None = None
    detail: str | None = None
    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(sa.String()), nullable=False, server_default="{}"),
    )
    date: str
    quarantined: bool = Field(default=False)
    quarantine_reasons: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(sa.String()), nullable=False, server_default="{}"),
    )
    indexed_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    search_vector: str | None = Field(
        default=None,
        sa_column=Column(TSVECTOR, nullable=True),
    )
