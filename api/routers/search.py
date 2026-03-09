from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.services.embeddings import embed
from api.services.qdrant import qdrant_service
from api.workers.gap_tracker import record_gap

router = APIRouter(tags=["search"])


class SearchResult(BaseModel):
    post_id: str
    handle: str
    title: str
    tl_dr: str
    tags: list[str]
    score: float
    url: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    query: str


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Public search endpoint — no auth required."""
    vector = await embed(q)
    results = await qdrant_service.hybrid_search(q, vector, limit=limit)

    if not results:
        await record_gap(q, db)

    return SearchResponse(
        results=results,
        total=len(results),
        query=q,
    )
