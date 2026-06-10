import logging
import time
import uuid

from qdrant_client import QdrantClient, models

from app.config import settings

logger = logging.getLogger(__name__)


class SemanticCache:
    """Caches RAG answers keyed by query embedding similarity.

    A query that is semantically close enough to a previously answered one
    (cosine similarity above the configured threshold, same top_k) is served
    from the cache, skipping retrieval and LLM generation entirely.
    """

    def __init__(self) -> None:
        self.client: QdrantClient | None = None
        self.collection_name = settings.SEMANTIC_CACHE_COLLECTION_NAME
        self.vector_size = settings.VECTOR_SIZE
        self.similarity_threshold = settings.SEMANTIC_CACHE_SIMILARITY_THRESHOLD
        self.ttl_seconds = settings.SEMANTIC_CACHE_TTL_SECONDS

    @property
    def enabled(self) -> bool:
        return settings.SEMANTIC_CACHE_ENABLED

    def initialize(self) -> None:
        if not self.enabled:
            logger.info("semantic_cache_disabled")
            return

        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            timeout=settings.QDRANT_TIMEOUT_SECONDS,
        )

        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info(
                "semantic_cache_collection_created",
                extra={
                    "collection_name": self.collection_name,
                    "similarity_threshold": self.similarity_threshold,
                    "ttl_seconds": self.ttl_seconds,
                },
            )
        else:
            logger.info(
                "semantic_cache_collection_exists",
                extra={"collection_name": self.collection_name},
            )

    def lookup(self, query_embedding: list[float], top_k: int) -> dict | None:
        if not self.enabled or self.client is None:
            return None

        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=1,
                with_payload=True,
                score_threshold=self.similarity_threshold,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="top_k",
                            match=models.MatchValue(value=top_k),
                        )
                    ]
                ),
            )
        except Exception:
            logger.exception("semantic_cache_lookup_failed")
            return None

        if not results:
            return None

        point = results[0]
        payload = point.payload or {}

        created_at = float(payload.get("created_at", 0.0))
        if time.time() - created_at > self.ttl_seconds:
            try:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(points=[point.id]),
                )
            except Exception:
                logger.exception("semantic_cache_expiry_delete_failed")
            return None

        return {
            "answer": payload.get("answer", ""),
            "sources": payload.get("sources", []),
            "matched_query": payload.get("query", ""),
            "similarity": point.score,
            "generation_seconds": float(payload.get("generation_seconds", 0.0)),
        }

    def store(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int,
        answer: str,
        sources: list[dict],
        generation_seconds: float,
    ) -> None:
        if not self.enabled or self.client is None:
            return

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=query_embedding,
                        payload={
                            "query": query,
                            "top_k": top_k,
                            "answer": answer,
                            "sources": sources,
                            "generation_seconds": generation_seconds,
                            "created_at": time.time(),
                        },
                    )
                ],
                wait=False,
            )
        except Exception:
            logger.exception("semantic_cache_store_failed")

    def clear(self) -> None:
        """Drop all cached answers. Called when documents change, since
        previously generated answers may no longer reflect the corpus."""
        if not self.enabled or self.client is None:
            return

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(filter=models.Filter()),
            )
            logger.info("semantic_cache_cleared")
        except Exception:
            logger.exception("semantic_cache_clear_failed")


semantic_cache = SemanticCache()
