from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from api.config import settings
from api.db import get_db
from api.models import GapSignal

router = APIRouter(tags=["gaps"])


class GapItem(BaseModel):
    query_hash: str  # sha256[:16] — one-way, never raw query text
    session_count: int
    week_bucket: str


class GapsResponse(BaseModel):
    gaps: list[GapItem]


@router.get("/gaps", response_model=GapsResponse)
async def list_gaps(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> GapsResponse:
    """Public gap board — queries with no results, k-anonymized."""
    result = await db.exec(
        select(GapSignal)
        .where(GapSignal.session_count >= settings.gap_min_sessions)
        .order_by(GapSignal.session_count.desc())
        .limit(limit)
    )
    signals = result.all()
    return GapsResponse(
        gaps=[
            GapItem(
                query_hash=s.query_hash,
                session_count=s.session_count,
                week_bucket=s.week_bucket,
            )
            for s in signals
        ]
    )
