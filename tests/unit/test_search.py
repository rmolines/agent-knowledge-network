"""Unit tests for the GET /search endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.db import get_db
from api.main import app

RAW_RESULT = {
    "post_id": "abc-123",
    "handle": "@testuser",
    "title": "Test Post",
    "tl_dr": "A short summary.",
    "tags": ["ai", "tools"],
    "score": 0.9,
    "url": "https://agentknowledge.network/posts/abc-123",
}


@pytest.fixture()
def mock_arq_pool() -> MagicMock:
    pool = MagicMock()
    pool.close = AsyncMock()
    return pool


@pytest.fixture()
def client(mock_arq_pool: MagicMock) -> TestClient:
    mock_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_session

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


def test_search_returns_results(client: TestClient) -> None:
    with (
        patch("api.routers.search.embed", new_callable=AsyncMock, return_value=[0.1] * 256),
        patch(
            "api.routers.search.qdrant_service.hybrid_search",
            new_callable=AsyncMock,
            return_value=[RAW_RESULT],
        ),
    ):
        response = client.get("/search?q=test")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["query"] == "test"
    assert data["results"][0]["post_id"] == "abc-123"
    assert data["results"][0]["handle"] == "@testuser"
    assert data["results"][0]["tl_dr"] == "A short summary."


def test_search_result_has_wrapped_tl_dr(client: TestClient) -> None:
    with (
        patch("api.routers.search.embed", new_callable=AsyncMock, return_value=[0.1] * 256),
        patch(
            "api.routers.search.qdrant_service.hybrid_search",
            new_callable=AsyncMock,
            return_value=[RAW_RESULT],
        ),
    ):
        response = client.get("/search?q=test")

    result = response.json()["results"][0]
    assert "wrapped_tl_dr" in result
    assert '<retrieved_user_content' in result["wrapped_tl_dr"]
    assert 'untrusted="true"' in result["wrapped_tl_dr"]
    assert 'source_id="abc-123"' in result["wrapped_tl_dr"]
    assert 'author="@testuser"' in result["wrapped_tl_dr"]
    assert "A short summary." in result["wrapped_tl_dr"]


def test_search_empty_results_records_gap(client: TestClient) -> None:
    with (
        patch("api.routers.search.embed", new_callable=AsyncMock, return_value=[0.1] * 256),
        patch(
            "api.routers.search.qdrant_service.hybrid_search",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("api.routers.search.record_gap", new_callable=AsyncMock) as mock_gap,
    ):
        response = client.get("/search?q=unknown+topic")

    assert response.status_code == 200
    assert response.json()["total"] == 0
    mock_gap.assert_awaited_once()


def test_search_empty_results_returns_empty_list(client: TestClient) -> None:
    with (
        patch("api.routers.search.embed", new_callable=AsyncMock, return_value=[0.1] * 256),
        patch(
            "api.routers.search.qdrant_service.hybrid_search",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch("api.routers.search.record_gap", new_callable=AsyncMock),
    ):
        response = client.get("/search?q=nothing")

    data = response.json()
    assert data["results"] == []
    assert data["total"] == 0


def test_search_rejects_empty_query(client: TestClient) -> None:
    response = client.get("/search?q=")
    assert response.status_code == 422


def test_search_limit_param(client: TestClient) -> None:
    with (
        patch("api.routers.search.embed", new_callable=AsyncMock, return_value=[0.1] * 256),
        patch(
            "api.routers.search.qdrant_service.hybrid_search",
            new_callable=AsyncMock,
            return_value=[RAW_RESULT],
        ) as mock_search,
    ):
        client.get("/search?q=test&limit=10")

    mock_search.assert_awaited_once_with("test", [0.1] * 256, limit=10)
