from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.models import Post
from api.security.wrappers import WrappedPost, wrap_tl_dr
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


async def _search_db(q: str, limit: int, db: AsyncSession) -> list[tuple[Post, float]]:
    """Execute Postgres FTS query. Returns (Post, rank) pairs ordered by relevance."""
    ts_query = func.websearch_to_tsquery("simple", q)
    rank = func.ts_rank(Post.search_vector, ts_query).label("rank")
    stmt = (
        select(Post, rank)
        .where(Post.quarantined == False)  # noqa: E712
        .where(Post.search_vector.op("@@")(ts_query))
        .order_by(rank.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.all())


def _build_result(post: Post, score: float) -> SearchResult:
    post_id = str(post.id)
    wrapped = wrap_tl_dr(WrappedPost(post_id=post_id, handle=post.handle, tl_dr=post.tl_dr))
    return SearchResult(
        post_id=post_id,
        handle=post.handle,
        title=post.title,
        tl_dr=post.tl_dr,
        tags=post.tags,
        score=score,
        url=f"https://agentknowledge.network/posts/{post.id}",
        wrapped_tl_dr=wrapped,
    )


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Public search endpoint — no auth required."""
    rows = await _search_db(q, limit, db)

    if not rows:
        await record_gap(q, db)

    results = [_build_result(post, float(score)) for post, score in rows]

    return SearchResponse(results=results, total=len(results), query=q)
