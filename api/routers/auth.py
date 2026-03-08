import secrets
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.config import settings
from api.db import get_db
from api.models import Handle, Session
from api.services.github import HEADERS as GITHUB_HEADERS
from api.services.jwt import SESSION_TTL_HOURS, create_session_token
from api.services.redis import consume_state, set_state

router = APIRouter(prefix="/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

SESSION_COOKIE = "session"


@router.get("/login")
async def login() -> RedirectResponse:
    """Redirect to GitHub OAuth. Stores one-time-use CSRF state in Redis."""
    state = secrets.token_urlsafe(32)
    await set_state(state, ttl=settings.oauth_state_ttl_seconds)
    url = httpx.URL(GITHUB_AUTHORIZE_URL).copy_merge_params({
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "read:user public_repo",
        "state": state,
    })
    return RedirectResponse(url=str(url))


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """GitHub OAuth callback. Validates state, exchanges code, issues HttpOnly session cookie."""
    # 1. Validate CSRF state (one-time-use — atomically deleted)
    if not await consume_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    # 2. Exchange code for GitHub access token + fetch user profile (single connection)
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
            timeout=10.0,
        )
        token_response.raise_for_status()
        token_data = token_response.json()

        github_token: str | None = token_data.get("access_token")
        if not github_token:
            raise HTTPException(status_code=400, detail="GitHub did not return an access token")

        # 3. Fetch GitHub user profile (reuses connection via keep-alive)
        user_response = await client.get(
            GITHUB_USER_URL,
            headers={**GITHUB_HEADERS, "Authorization": f"Bearer {github_token}"},
            timeout=10.0,
        )
        user_response.raise_for_status()
        user_data = user_response.json()

    github_id: int = user_data["id"]
    github_login: str = user_data["login"]

    # 4. Upsert Handle
    result = await db.exec(select(Handle).where(Handle.github_id == github_id))
    handle = result.first()
    if handle is None:
        handle = Handle(
            handle=github_login,
            github_login=github_login,
            github_id=github_id,
        )
        db.add(handle)
        await db.flush()  # populate handle.id before creating Session
    else:
        handle.github_login = github_login  # keep login in sync

    # 5. Create Session
    expires_at = datetime.now(tz=UTC) + timedelta(hours=SESSION_TTL_HOURS)
    session = Session(
        handle_id=handle.id,
        github_token=github_token,
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()

    # 6. Issue JWT as HttpOnly cookie
    jwt_token = create_session_token(handle_id=handle.id, session_id=session.id)
    response = Response(
        status_code=200,
        content='{"status": "ok"}',
        media_type="application/json",
    )
    response.set_cookie(
        key=SESSION_COOKIE,
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_TTL_HOURS * 3600,
    )
    return response


@router.post("/logout")
async def logout() -> Response:
    """Clear the session cookie."""
    response = Response(
        status_code=200,
        content='{"status": "ok"}',
        media_type="application/json",
    )
    response.delete_cookie(key=SESSION_COOKIE)
    return response
