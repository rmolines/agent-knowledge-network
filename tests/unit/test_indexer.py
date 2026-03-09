"""Unit tests for the indexer worker (parse_post_markdown)."""

import pytest

from api.workers.indexer import parse_post_markdown

_VALID_POST = """\
---
title: "Configuring Qdrant Hybrid Search"
handle: "@alice"
tags: [qdrant, search, fastapi]
date: "2025-01-15"
---

## TL;DR
Use hybrid search (dense + BM25) for best recall.

## Contexto
Combine semantic and keyword retrieval via RRF fusion.

## Detalhe
Configure sparse vectors with BM25 modifier in the collection.
"""

_POST_MINIMAL = """\
---
title: "Minimal Post"
handle: "@bob"
tags: []
date: "2025-06-01"
---

## TL;DR
Short post with no context or detail.
"""


def test_parse_valid_post_returns_title() -> None:
    result = parse_post_markdown(_VALID_POST)
    assert result["title"] == "Configuring Qdrant Hybrid Search"


def test_parse_valid_post_returns_handle() -> None:
    result = parse_post_markdown(_VALID_POST)
    assert result["handle"] == "@alice"


def test_parse_valid_post_returns_tags() -> None:
    result = parse_post_markdown(_VALID_POST)
    assert result["tags"] == ["qdrant", "search", "fastapi"]


def test_parse_valid_post_returns_tl_dr() -> None:
    result = parse_post_markdown(_VALID_POST)
    assert "hybrid search" in result["tl_dr"]


def test_parse_valid_post_returns_context() -> None:
    result = parse_post_markdown(_VALID_POST)
    assert result["context"] is not None
    assert "RRF fusion" in result["context"]


def test_parse_valid_post_returns_detail() -> None:
    result = parse_post_markdown(_VALID_POST)
    assert result["detail"] is not None
    assert "BM25 modifier" in result["detail"]


def test_parse_minimal_post_context_is_none() -> None:
    result = parse_post_markdown(_POST_MINIMAL)
    assert result["context"] is None


def test_parse_minimal_post_detail_is_none() -> None:
    result = parse_post_markdown(_POST_MINIMAL)
    assert result["detail"] is None


def test_parse_post_missing_frontmatter_raises() -> None:
    with pytest.raises(ValueError, match="missing frontmatter"):
        parse_post_markdown("# No frontmatter here\n\nJust content.")


def test_parse_post_missing_tl_dr_raises() -> None:
    post = """\
---
title: "No TL;DR"
handle: "@carol"
tags: []
date: "2025-01-01"
---

## Contexto
Only context, no TL;DR section.
"""
    with pytest.raises(ValueError, match="missing ## TL;DR"):
        parse_post_markdown(post)


def test_parse_post_date_defaults_when_missing() -> None:
    post = """\
---
title: "No Date"
handle: "@dave"
tags: []
---

## TL;DR
Post without a date field.
"""
    result = parse_post_markdown(post)
    # Should not raise; date is filled with today's date
    assert result["date"] != ""
