from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.security.wrappers import WrappedPost, wrap_tl_dr
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
    wrapped_tl_dr: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    query: str


def _build_result(raw: dict) -> SearchResult:  # type: ignore[type-arg]
    wrapped = wrap_tl_dr(
        WrappedPost(
            post_id=raw["post_id"],
            handle=raw["handle"],
            tl_dr=raw["tl_dr"],
        )
    )
    return SearchResult(**raw, wrapped_tl_dr=wrapped)


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Public search endpoint — no auth required."""
    vector = await embed(q)
    raw_results = await qdrant_service.hybrid_search(q, vector, limit=limit)

    if not raw_results:
        await record_gap(q, db)

    results = [_build_result(r) for r in raw_results]

    return SearchResponse(
        results=results,
        total=len(results),
        query=q,
    )
