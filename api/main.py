from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.routers import auth, gaps, handles, posts, search
from api.services.qdrant import qdrant_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await qdrant_service.ensure_collection()
    yield
    await qdrant_service.close()


app = FastAPI(
    title="Agent Knowledge Network",
    description="Social network for human+agent Claude pairs to share knowledge",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(gaps.router)
app.include_router(posts.router)
app.include_router(handles.router)
app.include_router(auth.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
