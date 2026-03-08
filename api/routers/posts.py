from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_current_handle
from api.models import Handle
from api.workers.indexer import index_post

router = APIRouter(tags=["posts"])


class IngestRequest(BaseModel):
    github_repo: str   # "owner/repo"
    file_path: str     # path inside repo, e.g. ".network-posts/my-post.md"


class IngestResponse(BaseModel):
    status: str
    message: str


class PostDetail(BaseModel):
    post_id: str
    handle: str
    title: str
    tl_dr: str
    context: str | None
    detail: str | None
    tags: list[str]
    date: str
    url: str


@router.post("/posts", status_code=202, response_model=IngestResponse)
async def ingest_post(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    current_handle: Handle = Depends(get_current_handle),
) -> IngestResponse:
    """Ingest a post from a GitHub repo. Returns 202 immediately."""
    background_tasks.add_task(index_post, request.github_repo, request.file_path)
    return IngestResponse(status="queued", message="Post queued for indexing")


@router.get("/posts/{post_id}", response_model=PostDetail)
async def get_post(post_id: str) -> PostDetail:
    """Retrieve full post content by ID."""
    # TODO: implement DB + Qdrant fetch
    raise HTTPException(status_code=404, detail="Post not found")
