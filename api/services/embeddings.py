"""
Embedding service — text-embedding-3-small with 256 dimensions (MRL truncation).

NOTE: Changing embedding_dim or model invalidates ALL existing Qdrant vectors.
Only change after a full migration plan is in place.
"""

from openai import AsyncOpenAI

from api.config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def embed(text: str) -> list[float]:
    """Embed a single text string. Returns 256-dim vector."""
    response = await _client.embeddings.create(
        model=settings.embedding_model,
        input=text,
        dimensions=settings.embedding_dim,
    )
    return response.data[0].embedding


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts in a single API call (batch — cheaper)."""
    response = await _client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
        dimensions=settings.embedding_dim,
    )
    return [item.embedding for item in response.data]
