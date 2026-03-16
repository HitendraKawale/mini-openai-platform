import logging
import uuid

from qdrant_client import QdrantClient, models

from app.config import settings

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    def __init__(self) -> None:
        self.client: QdrantClient | None = None
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_size = settings.VECTOR_SIZE
        self.url = settings.QDRANT_URL

    def connect(self) -> None:
        self.client = QdrantClient(
            url=self.url,
            timeout=settings.QDRANT_TIMEOUT_SECONDS,
        )

    def initialize(self) -> None:
        self.connect()
        self._ensure_client()

        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info(
                "qdrant_collection_created",
                extra={
                    "collection_name": self.collection_name,
                    "vector_size": self.vector_size,
                },
            )
        else:
            logger.info(
                "qdrant_collection_exists",
                extra={
                    "collection_name": self.collection_name,
                },
            )

    def _ensure_client(self) -> None:
        if self.client is None:
            raise RuntimeError("Qdrant client is not initialized")

    def is_ready(self) -> bool:
        try:
            self._ensure_client()
            assert self.client is not None
            self.client.get_collections()
            return True
        except Exception:
            return False

    def add_document_chunks(
        self,
        document_id: str,
        filename: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        self._ensure_client()
        assert self.client is not None

        points: list[models.PointStruct] = []

        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_id": f"{document_id}_chunk_{idx}",
                        "text": chunk,
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

    def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        self._ensure_client()
        assert self.client is not None

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True,
        )

        formatted: list[dict] = []
        for point in results:
            payload = point.payload or {}
            formatted.append(
                {
                    "document_id": payload.get("document_id"),
                    "filename": payload.get("filename"),
                    "chunk_id": payload.get("chunk_id"),
                    "text": payload.get("text"),
                    "score": point.score,
                }
            )

        return formatted

    def chunk_count(self) -> int:
        try:
            self._ensure_client()
            assert self.client is not None
            return int(self.client.count(collection_name=self.collection_name).count)
        except Exception:
            return 0

    def document_count(self) -> int:
        try:
            self._ensure_client()
            assert self.client is not None

            unique_document_ids: set[str] = set()
            offset = None

            while True:
                points, next_page_offset = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=256,
                    offset=offset,
                    with_payload=["document_id"],
                    with_vectors=False,
                )

                for point in points:
                    payload = point.payload or {}
                    document_id = payload.get("document_id")
                    if document_id:
                        unique_document_ids.add(document_id)

                if next_page_offset is None:
                    break

                offset = next_page_offset

            return len(unique_document_ids)
        except Exception:
            return 0


vector_store = QdrantVectorStore()


def new_document_id() -> str:
    return f"doc_{uuid.uuid4().hex[:10]}"