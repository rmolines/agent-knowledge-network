"""
GitHub service — fetch markdown files from user repos.

Uses Git Trees API (not Contents API) for efficient recursive listing.
Posts live in user repos; we index but do not copy content.
"""

import base64

import httpx

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


async def fetch_file_content(repo: str, file_path: str, token: str | None = None) -> str:
    """Fetch a single markdown file from a GitHub repo."""
    headers = {**HEADERS}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{GITHUB_API}/repos/{repo}/contents/{file_path}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        data = response.json()

    if data.get("encoding") != "base64":
        raise ValueError(f"Unexpected encoding: {data.get('encoding')}")

    return base64.b64decode(data["content"]).decode("utf-8")


async def list_network_posts(repo: str, token: str | None = None) -> list[str]:
    """List all .md files in .network-posts/ directory of a repo."""
    headers = {**HEADERS}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Get default branch SHA
    async with httpx.AsyncClient() as client:
        repo_response = await client.get(
            f"{GITHUB_API}/repos/{repo}", headers=headers, timeout=10.0
        )
        repo_response.raise_for_status()
        default_branch = repo_response.json()["default_branch"]

        # Use Git Trees API for efficient recursive listing
        tree_response = await client.get(
            f"{GITHUB_API}/repos/{repo}/git/trees/{default_branch}?recursive=1",
            headers=headers,
            timeout=10.0,
        )
        tree_response.raise_for_status()
        tree_data = tree_response.json()

    if tree_data.get("truncated"):
        # Repo is very large — only .network-posts/ files are relevant anyway
        pass

    return [
        item["path"]
        for item in tree_data.get("tree", [])
        if item["type"] == "blob"
        and item["path"].startswith(".network-posts/")
        and item["path"].endswith(".md")
    ]
