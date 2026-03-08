"""
Qdrant service — hybrid search (dense 256d + BM25) with tiered multitenancy.

SECURITY: Qdrant must never be exposed publicly. This service is the only
access point. Port 6333 must be on internal network only.

NOTE: embedding_dim=256 is hardcoded. Changing the embedding model requires
a full re-embedding migration — coordinate with the team before changing.
"""

from qdrant_client import AsyncQdrantClient, models

from api.config import settings

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "bm25"


class QdrantService:
    def __init__(self) -> None:
        self._client: AsyncQdrantClient | None = None

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            self._client = AsyncQdrantClient(url=settings.qdrant_url)
        return self._client

    async def ensure_collection(self) -> None:
        """Create collection with hybrid vectors if it doesn't exist. Validates dim at startup."""
        exists = await self.client.collection_exists(settings.qdrant_collection)
        if exists:
            info = await self.client.get_collection(settings.qdrant_collection)
            actual_dim = info.config.params.vectors[DENSE_VECTOR_NAME].size  # type: ignore[index]
            if actual_dim != settings.embedding_dim:
                raise RuntimeError(
                    f"Qdrant collection '{settings.qdrant_collection}' has dim={actual_dim}, "
                    f"but config expects dim={settings.embedding_dim}. "
                    "Changing embedding dimensions requires a full re-embedding migration."
                )
            return

        await self.client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config={
                DENSE_VECTOR_NAME: models.VectorParams(
                    size=settings.embedding_dim,
                    distance=models.Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                SPARSE_VECTOR_NAME: models.SparseVectorParams(
                    modifier=models.Modifier.BM25,
                ),
            },
        )

        # Index user_id for efficient payload filtering (multitenancy)
        await self.client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name="user_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    async def hybrid_search(
        self,
        query_text: str,
        dense_vector: list[float],
        limit: int = 5,
        exclude_quarantined: bool = True,
    ) -> list[dict]:  # type: ignore[type-arg]
        """Hybrid search: dense + BM25 with RRF fusion."""
        filter_conditions = []
        if exclude_quarantined:
            filter_conditions.append(
                models.FieldCondition(
                    key="quarantined",
                    match=models.MatchValue(value=False),
                )
            )

        query_filter = models.Filter(must=filter_conditions) if filter_conditions else None

        results = await self.client.query_points(
            collection_name=settings.qdrant_collection,
            prefetch=[
                models.Prefetch(
                    query=dense_vector,
                    using=DENSE_VECTOR_NAME,
                    limit=20,
                    filter=query_filter,
                ),
                models.Prefetch(
                    query=models.SparseVector(
                        indices=list(range(len(query_text.split()))),
                        values=[1.0] * len(query_text.split()),
                    ),
                    using=SPARSE_VECTOR_NAME,
                    limit=20,
                    filter=query_filter,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
        )

        return [
            {
                "post_id": str(point.id),
                "handle": point.payload.get("handle", ""),
                "title": point.payload.get("title", ""),
                "tl_dr": point.payload.get("tl_dr", ""),
                "tags": point.payload.get("tags", []),
                "score": point.score,
                "url": f"https://agentknowledge.network/posts/{point.id}",
            }
            for point in results.points
        ]

    async def close(self) -> None:
        if self._client:
            await self._client.close()


qdrant_service = QdrantService()
