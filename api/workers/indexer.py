"""
Indexer worker — runs as ARQ background task.

Pipeline: fetch GitHub → sanitize → parse frontmatter → embed → upsert Qdrant.

SECURITY: Sanitization is mandatory before indexing. Posts that fail sanitization
are quarantined (not indexed publicly). See api/security/sanitizer.py.
"""

import re
import uuid
from datetime import datetime, timezone

from api.security.sanitizer import is_safe_for_indexing
from api.services.embeddings import embed
from api.services.github import fetch_file_content
from api.services.qdrant import qdrant_service


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
        "date": str(meta.get("date", datetime.now(timezone.utc).date().isoformat())),
        "tl_dr": tl_dr_match.group(1).strip(),
        "context": context_match.group(1).strip() if context_match else None,
        "detail": detail_match.group(1).strip() if detail_match else None,
    }


async def index_post(github_repo: str, file_path: str, user_token: str | None = None) -> None:
    """
    Index a post from GitHub. Called as background task.

    Steps:
    1. Fetch markdown content from GitHub
    2. Sanitize (anti-injection)
    3. Parse frontmatter + sections
    4. Embed TL;DR + title (what agents search against)
    5. Upsert to Qdrant with metadata
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

    # Embed TL;DR + title (what agents search against)
    embed_text = f"{post['title']}\n{post['tl_dr']}"
    vector = await embed(embed_text)

    post_id = str(uuid.uuid4())
    payload = {
        "github_repo": github_repo,
        "file_path": file_path,
        "handle": post["handle"],
        "title": post["title"],
        "tl_dr": post["tl_dr"],
        "tags": post["tags"],
        "date": post["date"],
        "quarantined": quarantined,
        "quarantine_reasons": reasons,
        "indexed_at": datetime.now(timezone.utc).isoformat(),
    }

    await qdrant_service.client.upsert(
        collection_name="posts",
        points=[
            {
                "id": post_id,
                "vector": {"dense": vector},
                "payload": payload,
            }
        ],
    )

    print(f"[indexer] Indexed {post_id} ({post['title']}) quarantined={quarantined}")
