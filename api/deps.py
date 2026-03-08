"""
FastAPI dependencies — reusable injectable components.
"""

from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.db import get_db
from api.models import Handle, Session
from api.services.jwt import decode_session_token


async def get_current_handle(
    session_cookie: str | None = Cookie(default=None, alias="session"),
    db: AsyncSession = Depends(get_db),
) -> Handle:
    """Decode the HttpOnly session cookie and return the authenticated Handle.

    Raises HTTP 401 if the cookie is missing, the JWT is invalid, or the
    session / handle no longer exists in the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )

    if session_cookie is None:
        raise credentials_exception

    try:
        payload = decode_session_token(session_cookie)
        handle_id: str | None = payload.get("sub")
        session_id: str | None = payload.get("sid")
    except JWTError:
        raise credentials_exception

    if handle_id is None or session_id is None:
        raise credentials_exception

    # Validate session row exists and is not expired
    session_result = await db.exec(
        select(Session).where(Session.id == session_id, Session.handle_id == handle_id)
    )
    db_session = session_result.first()
    if db_session is None:
        raise credentials_exception

    from datetime import UTC, datetime

    if datetime.now(tz=UTC) > db_session.expires_at:
        raise credentials_exception

    # Load Handle
    handle_result = await db.exec(select(Handle).where(Handle.id == handle_id))
    handle = handle_result.first()
    if handle is None:
        raise credentials_exception

    return handle


__all__ = ["get_current_handle"]
