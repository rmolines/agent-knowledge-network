"""Unit tests for api.deps.get_current_handle."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from jose import JWTError

from api.deps import get_current_handle
from api.models import Handle, Session


def _make_db(session_row=None, handle_row=None):
    """Build a mock AsyncSession whose exec() returns the given rows."""
    mock_result_session = MagicMock()
    mock_result_session.first.return_value = session_row

    mock_result_handle = MagicMock()
    mock_result_handle.first.return_value = handle_row

    db = AsyncMock()
    # first exec() call → sessions query; second → handles query
    db.exec.side_effect = [mock_result_session, mock_result_handle]
    return db


@pytest.mark.asyncio
async def test_missing_cookie_raises_401():
    db = AsyncMock()
    with pytest.raises(HTTPException) as exc_info:
        await get_current_handle(session_cookie=None, db=db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_invalid_jwt_raises_401():
    db = AsyncMock()
    with patch("api.deps.decode_session_token", side_effect=JWTError("bad token")):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_handle(session_cookie="bad.token.here", db=db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_jwt_missing_sub_raises_401():
    db = AsyncMock()
    with patch("api.deps.decode_session_token", return_value={"sid": str(uuid4())}):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_handle(session_cookie="token", db=db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_session_not_found_raises_401():
    handle_id = uuid4()
    session_id = uuid4()
    db = _make_db(session_row=None)  # no session in DB

    payload = {"sub": str(handle_id), "sid": str(session_id)}
    with patch("api.deps.decode_session_token", return_value=payload):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_handle(session_cookie="token", db=db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_expired_session_raises_401():
    handle_id = uuid4()
    session_id = uuid4()
    expired_session = Session(
        id=session_id,
        handle_id=handle_id,
        github_token="tok",
        expires_at=datetime.now(tz=UTC) - timedelta(hours=1),  # already expired
    )
    db = _make_db(session_row=expired_session)

    payload = {"sub": str(handle_id), "sid": str(session_id)}
    with patch("api.deps.decode_session_token", return_value=payload):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_handle(session_cookie="token", db=db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_handle_not_found_raises_401():
    handle_id = uuid4()
    session_id = uuid4()
    valid_session = Session(
        id=session_id,
        handle_id=handle_id,
        github_token="tok",
        expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
    )
    db = _make_db(session_row=valid_session, handle_row=None)  # no handle in DB

    payload = {"sub": str(handle_id), "sid": str(session_id)}
    with patch("api.deps.decode_session_token", return_value=payload):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_handle(session_cookie="token", db=db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_valid_session_returns_handle():
    handle_id = uuid4()
    session_id = uuid4()
    valid_session = Session(
        id=session_id,
        handle_id=handle_id,
        github_token="tok",
        expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
    )
    expected_handle = Handle(
        id=handle_id,
        handle="testuser",
        github_login="testuser",
        github_id=12345,
    )
    db = _make_db(session_row=valid_session, handle_row=expected_handle)

    payload = {"sub": str(handle_id), "sid": str(session_id)}
    with patch("api.deps.decode_session_token", return_value=payload):
        result = await get_current_handle(session_cookie="token", db=db)

    assert result is expected_handle
    assert result.handle == "testuser"
