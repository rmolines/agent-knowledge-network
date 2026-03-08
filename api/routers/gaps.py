from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(tags=["gaps"])


class GapItem(BaseModel):
    query_hint: str  # sanitized hint — never raw query text
    session_count: int
    week_bucket: str


class GapsResponse(BaseModel):
    gaps: list[GapItem]


@router.get("/gaps", response_model=GapsResponse)
async def list_gaps(
    limit: int = Query(20, ge=1, le=100),
) -> GapsResponse:
    """Public gap board — queries with no results, k-anonymized."""
    # TODO: implement DB query (GapSignal model)
    return GapsResponse(gaps=[])
