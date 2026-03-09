"""
Indexer worker — runs as ARQ background task.

Pipeline: fetch GitHub → sanitize → parse frontmatter → upsert Postgres (tsvector).

SECURITY: Sanitization is mandatory before indexing. Posts that fail sanitization
are quarantined (not publicly searchable). See api/security/sanitizer.py.
"""

import re
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from api.db import _session_factory
from api.models import Post
from api.security.sanitizer import is_safe_for_indexing
from api.services.github import fetch_file_content


def parse_post_markdown(content: str) -> dict:  # type: ignore[type-arg]
    """Parse post markdown with frontmatter. Returns structured post data."""
    # Extract YAML frontmatter
    frontmatter_match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not frontmatter_match:
        raise ValueError("Post missing frontmatter")

    frontmatter_text = frontmatter_match.group(1)
    body = frontmatter_match.group(2)

    # Simple frontmatter parsing (avoid yaml.load for security — no arbitrary Python objects)
    meta: dict[str, str | list[str]] = {}
    for line in frontmatter_text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                meta[key.strip()] = [v.strip().strip('"') for v in value[1:-1].split(",")]
            else:
                meta[key.strip()] = value.strip('"')

    # Extract progressive disclosure sections
    tl_dr_match = re.search(r"## TL;DR\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
    context_match = re.search(r"## Contexto\n(.*?)(?=\n## |\Z)", body, re.DOTALL)
    detail_match = re.search(r"## Detalhe\n(.*?)(?=\n## |\Z)", body, re.DOTALL)

    if not tl_dr_match:
        raise ValueError("Post missing ## TL;DR section")

    return {
        "title": str(meta.get("title", "")),
        "handle": str(meta.get("handle", "")),
        "tags": list(meta.get("tags", [])),
        "date": str(meta.get("date", datetime.now(UTC).date().isoformat())),
        "tl_dr": tl_dr_match.group(1).strip(),
        "context": context_match.group(1).strip() if context_match else None,
        "detail": detail_match.group(1).strip() if detail_match else None,
    }


async def index_post(ctx: dict, github_repo: str, file_path: str, user_token: str | None = None) -> None:
    """
    Index a post from GitHub. Called as ARQ background task.

    Steps:
    1. Fetch markdown content from GitHub
    2. Sanitize (anti-injection)
    3. Parse frontmatter + sections
    4. Upsert into Postgres posts table with tsvector (title + tl_dr + tags)
    """
    try:
        raw_content = await fetch_file_content(github_repo, file_path, token=user_token)
    except Exception as e:
        print(f"[indexer] Failed to fetch {github_repo}/{file_path}: {e}")
        return

    # Sanitize before anything else
    safe, reasons = is_safe_for_indexing(raw_content)
    quarantined = not safe
    if quarantined:
        print(f"[indexer] Post quarantined ({reasons}): {github_repo}/{file_path}")

    try:
        post = parse_post_markdown(raw_content)
    except ValueError as e:
        print(f"[indexer] Parse error for {github_repo}/{file_path}: {e}")
        return

    # Build search text: title + tl_dr + space-joined tags (what agents search against)
    search_text = f"{post['title']} {post['tl_dr']} {' '.join(post['tags'])}"

    async with _session_factory() as session:
        stmt = (
            pg_insert(Post)
            .values(
                id=uuid4(),
                github_repo=github_repo,
                file_path=file_path,
                handle=post["handle"],
                title=post["title"],
                tl_dr=post["tl_dr"],
                context=post.get("context"),
                detail=post.get("detail"),
                tags=post["tags"],
                date=post["date"],
                quarantined=quarantined,
                quarantine_reasons=reasons,
                indexed_at=datetime.now(UTC),
                search_vector=func.to_tsvector("simple", search_text),
            )
            .on_conflict_do_update(
                constraint="uq_posts_repo_file",
                set_={
                    "handle": post["handle"],
                    "title": post["title"],
                    "tl_dr": post["tl_dr"],
                    "context": post.get("context"),
                    "detail": post.get("detail"),
                    "tags": post["tags"],
                    "date": post["date"],
                    "quarantined": quarantined,
                    "quarantine_reasons": reasons,
                    "indexed_at": datetime.now(UTC),
                    "search_vector": func.to_tsvector("simple", search_text),
                },
            )
        )
        await session.execute(stmt)
        await session.commit()

    print(f"[indexer] Indexed {github_repo}/{file_path} quarantined={quarantined}")
