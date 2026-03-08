from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class Handle(SQLModel, table=True):
    __tablename__ = "handles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    handle: str = Field(unique=True, index=True, max_length=39)  # mirrors GitHub username limit
    github_login: str = Field(unique=True, index=True)
    github_id: int = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    sessions: list["Session"] = Relationship(back_populates="handle")


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    handle_id: UUID = Field(foreign_key="handles.id", index=True)
    github_token: str  # OAuth token — used for GitHub API calls on behalf of the user
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

    handle: Handle | None = Relationship(back_populates="sessions")
