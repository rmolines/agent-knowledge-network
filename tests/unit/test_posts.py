"""Unit tests for the POST /posts endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture()
def mock_handle() -> MagicMock:
    handle = MagicMock()
    handle.id = "test-handle-id"
    handle.handle = "@testuser"
    return handle


@pytest.fixture()
def mock_arq_pool() -> MagicMock:
    pool = MagicMock()
    pool.enqueue_job = AsyncMock(return_value=None)
    pool.close = AsyncMock()
    return pool


@pytest.fixture()
def client(mock_handle: MagicMock, mock_arq_pool: MagicMock) -> TestClient:
    """TestClient with auth and ARQ pool mocked out; lifespan patched to avoid real services."""
    from api.deps import get_arq_pool, get_current_github_token, get_current_handle

    app.dependency_overrides[get_current_handle] = lambda: mock_handle
    app.dependency_overrides[get_current_github_token] = lambda: "gh-token-test"
    app.dependency_overrides[get_arq_pool] = lambda: mock_arq_pool

    with (
        patch("api.main.qdrant_service.ensure_collection", new_callable=AsyncMock),
        patch("api.main.qdrant_service.close", new_callable=AsyncMock),
        patch("api.main.get_redis", new_callable=AsyncMock),
        patch("api.main.close_redis", new_callable=AsyncMock),
        patch("api.main.create_pool", new_callable=AsyncMock, return_value=mock_arq_pool),
        TestClient(app, raise_server_exceptions=True) as c,
    ):
        yield c

    app.dependency_overrides.clear()


def test_ingest_post_returns_202(client: TestClient) -> None:
    response = client.post(
        "/posts",
        json={"github_repo": "owner/repo", "file_path": ".network-posts/my-post.md"},
    )
    assert response.status_code == 202


def test_ingest_post_returns_queued_status(client: TestClient) -> None:
    response = client.post(
        "/posts",
        json={"github_repo": "owner/repo", "file_path": ".network-posts/my-post.md"},
    )
    assert response.json()["status"] == "queued"


def test_ingest_post_enqueues_index_post_job(
    client: TestClient, mock_arq_pool: MagicMock
) -> None:
    client.post(
        "/posts",
        json={"github_repo": "owner/repo", "file_path": ".network-posts/my-post.md"},
    )

    mock_arq_pool.enqueue_job.assert_awaited_once_with(
        "index_post",
        "owner/repo",
        ".network-posts/my-post.md",
        "gh-token-test",
    )
