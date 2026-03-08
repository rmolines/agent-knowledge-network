"""
JWT utilities — create and decode session tokens.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt

from api.config import settings

ALGORITHM = "HS256"
SESSION_TTL_HOURS = 24 * 30  # 30 days


def create_session_token(handle_id: UUID, session_id: UUID) -> str:
    """Create a signed JWT embedding handle_id and session_id."""
    now = datetime.now(tz=UTC)
    payload = {
        "sub": str(handle_id),
        "sid": str(session_id),
        "iat": now,
        "exp": now + timedelta(hours=SESSION_TTL_HOURS),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_session_token(token: str) -> dict[str, str]:
    """Decode and validate a session JWT. Raises JWTError on failure."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


__all__ = ["create_session_token", "decode_session_token", "JWTError"]
