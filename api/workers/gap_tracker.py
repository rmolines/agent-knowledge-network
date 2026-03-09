"""
Gap tracker worker — records searches with no results as gap signals.

Privacy: queries are NEVER stored as plain text. Only hashed + week_bucket.
k-anonymity: gaps are only exposed on the public board when k >= settings.gap_min_sessions.
"""

import hashlib
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import GapSignal


def _week_bucket(dt: datetime | None = None) -> str:
    """Return ISO week string like '2026-W10'."""
    d = (dt or datetime.now(timezone.utc)).date()
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def _hash_query(query: str) -> str:
    """One-way hash of query text. Cannot be reversed to original query."""
    return hashlib.sha256(query.lower().strip().encode()).hexdigest()[:16]


async def record_gap(query: str, db: AsyncSession) -> None:
    """
    Record a search with no results as a gap signal.

    Stores: query_hash + week_bucket + increment session count.
    Never stores: raw query text, IP address, user identity.
    """
    query_hash = _hash_query(query)
    bucket = _week_bucket()

    stmt = (
        pg_insert(GapSignal)
        .values(query_hash=query_hash, week_bucket=bucket, session_count=1)
        .on_conflict_do_update(
            index_elements=["query_hash", "week_bucket"],
            set_={"session_count": GapSignal.__table__.c.session_count + 1},
        )
    )
    await db.execute(stmt)
