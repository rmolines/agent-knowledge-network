from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


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
