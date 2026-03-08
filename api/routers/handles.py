from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["handles"])


class HandleProfile(BaseModel):
    handle: str
    github_login: str
    post_count: int
    joined_at: str


@router.get("/handles/{handle}", response_model=HandleProfile)
async def get_handle(handle: str) -> HandleProfile:
    """Public profile for a handle."""
    # TODO: implement DB query
    raise HTTPException(status_code=404, detail="Handle not found")
