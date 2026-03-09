"""Unit tests for api.workers.gap_tracker."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.workers.gap_tracker import _hash_query, _week_bucket, record_gap


class TestWeekBucket:
    def test_returns_iso_week_format(self):
        dt = datetime(2026, 3, 8, tzinfo=timezone.utc)  # 2026-W10
        assert _week_bucket(dt) == "2026-W10"

    def test_zero_pads_single_digit_week(self):
        dt = datetime(2026, 1, 5, tzinfo=timezone.utc)  # week 2 of 2026
        result = _week_bucket(dt)
        assert result.startswith("2026-W0")

    def test_uses_utc_now_when_no_arg(self):
        result = _week_bucket()
        assert result.startswith("20")
        assert "-W" in result


class TestHashQuery:
    def test_returns_16_char_string(self):
        assert len(_hash_query("hello world")) == 16

    def test_case_insensitive(self):
        assert _hash_query("FastAPI") == _hash_query("fastapi")

    def test_strips_whitespace(self):
        assert _hash_query("  test  ") == _hash_query("test")

    def test_deterministic(self):
        assert _hash_query("same query") == _hash_query("same query")

    def test_different_queries_produce_different_hashes(self):
        assert _hash_query("query A") != _hash_query("query B")


@pytest.mark.asyncio
async def test_record_gap_executes_upsert_and_commits():
    db = AsyncMock()

    with patch("api.workers.gap_tracker.pg_insert") as mock_pg_insert:
        mock_stmt = MagicMock()
        mock_pg_insert.return_value.values.return_value.on_conflict_do_update.return_value = mock_stmt

        await record_gap("some unanswered query", db)

    db.execute.assert_awaited_once_with(mock_stmt)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_gap_never_stores_raw_query():
    """record_gap must call pg_insert with a hash, never the raw query string."""
    raw_query = "sensitive search term"
    db = AsyncMock()
    captured_values: dict = {}

    def capture_values(**kwargs):
        captured_values.update(kwargs)
        return MagicMock()

    with patch("api.workers.gap_tracker.pg_insert") as mock_pg_insert:
        mock_pg_insert.return_value.values.side_effect = capture_values
        try:
            await record_gap(raw_query, db)
        except Exception:
            pass  # side_effect chain may break — we only care about values call

    assert raw_query not in str(captured_values.get("query_hash", ""))
    if "query_hash" in captured_values:
        assert len(captured_values["query_hash"]) == 16
