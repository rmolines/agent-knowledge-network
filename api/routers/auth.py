import secrets

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from api.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"


@router.get("/login")
async def login() -> RedirectResponse:
    """Redirect to GitHub OAuth."""
    state = secrets.token_urlsafe(32)
    # TODO: store state in Redis with TTL=settings.oauth_state_ttl_seconds (one-time-use)
    params = (
        f"client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        f"&scope=read:user+public_repo"
        f"&state={state}"
    )
    return RedirectResponse(url=f"{GITHUB_AUTHORIZE_URL}?{params}")


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
) -> dict[str, str]:
    """GitHub OAuth callback. Validates state (CSRF), exchanges code for token."""
    # TODO: validate state from Redis (one-time-use, delete after validation)
    # TODO: exchange code for GitHub token via httpx
    # TODO: fetch GitHub user, create/update Handle in DB
    # TODO: return JWT session token
    raise HTTPException(status_code=501, detail="Not implemented yet")
