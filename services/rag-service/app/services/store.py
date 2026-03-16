import math
import uuid


class InMemoryVectorStore:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def add_document_chunks(
        self,
        document_id: str,
        filename: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            self.records.append(
                {
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_id": f"{document_id}_chunk_{idx}",
                    "text": chunk,
                    "embedding": embedding,
                }
            )

    def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        scored = []
        for record in self.records:
            score = cosine_similarity(query_embedding, record["embedding"])
            scored.append(
                {
                    **record,
                    "score": score,
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def document_count(self) -> int:
        return len({record["document_id"] for record in self.records})

    def chunk_count(self) -> int:
        return len(self.records)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


vector_store = InMemoryVectorStore()


def new_document_id() -> str:
    return f"doc_{uuid.uuid4().hex[:10]}"