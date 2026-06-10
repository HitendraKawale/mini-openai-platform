import time

from app.config import settings
from app.services.semantic_cache import SemanticCache


class FakePoint:
    def __init__(self, point_id: str, score: float, payload: dict):
        self.id = point_id
        self.score = score
        self.payload = payload


class FakeQdrantClient:
    def __init__(self, search_results: list[FakePoint] | None = None):
        self.search_results = search_results or []
        self.upserted_points: list = []
        self.deleted_selectors: list = []

    def search(self, **kwargs):
        return self.search_results

    def upsert(self, collection_name, points, wait=False):
        self.upserted_points.extend(points)

    def delete(self, collection_name, points_selector):
        self.deleted_selectors.append(points_selector)


def make_cache(client: FakeQdrantClient | None) -> SemanticCache:
    cache = SemanticCache()
    cache.client = client
    return cache


def cached_payload(created_at: float) -> dict:
    return {
        "query": "what is rag?",
        "top_k": 3,
        "answer": "RAG combines retrieval with generation.",
        "sources": [{"document_id": "doc_1", "chunk_id": "doc_1_chunk_0"}],
        "generation_seconds": 4.2,
        "created_at": created_at,
    }


def test_lookup_returns_cached_answer_on_similar_query(monkeypatch):
    monkeypatch.setattr(settings, "SEMANTIC_CACHE_ENABLED", True)
    client = FakeQdrantClient(
        search_results=[FakePoint("p1", 0.97, cached_payload(time.time()))]
    )
    cache = make_cache(client)

    result = cache.lookup([0.1] * 4, top_k=3)

    assert result is not None
    assert result["answer"] == "RAG combines retrieval with generation."
    assert result["similarity"] == 0.97
    assert result["generation_seconds"] == 4.2


def test_lookup_returns_none_when_nothing_similar(monkeypatch):
    monkeypatch.setattr(settings, "SEMANTIC_CACHE_ENABLED", True)
    cache = make_cache(FakeQdrantClient(search_results=[]))

    assert cache.lookup([0.1] * 4, top_k=3) is None


def test_lookup_evicts_expired_entries(monkeypatch):
    monkeypatch.setattr(settings, "SEMANTIC_CACHE_ENABLED", True)
    expired_at = time.time() - settings.SEMANTIC_CACHE_TTL_SECONDS - 10
    client = FakeQdrantClient(
        search_results=[FakePoint("p1", 0.99, cached_payload(expired_at))]
    )
    cache = make_cache(client)

    assert cache.lookup([0.1] * 4, top_k=3) is None
    assert len(client.deleted_selectors) == 1


def test_lookup_returns_none_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "SEMANTIC_CACHE_ENABLED", False)
    client = FakeQdrantClient(
        search_results=[FakePoint("p1", 0.99, cached_payload(time.time()))]
    )
    cache = make_cache(client)

    assert cache.lookup([0.1] * 4, top_k=3) is None


def test_store_writes_point_with_payload(monkeypatch):
    monkeypatch.setattr(settings, "SEMANTIC_CACHE_ENABLED", True)
    client = FakeQdrantClient()
    cache = make_cache(client)

    cache.store(
        query="what is rag?",
        query_embedding=[0.1] * 4,
        top_k=3,
        answer="RAG combines retrieval with generation.",
        sources=[{"document_id": "doc_1"}],
        generation_seconds=4.2,
    )

    assert len(client.upserted_points) == 1
    payload = client.upserted_points[0].payload
    assert payload["query"] == "what is rag?"
    assert payload["top_k"] == 3
    assert payload["generation_seconds"] == 4.2
    assert payload["created_at"] <= time.time()


def test_store_is_noop_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "SEMANTIC_CACHE_ENABLED", False)
    client = FakeQdrantClient()
    cache = make_cache(client)

    cache.store(
        query="q",
        query_embedding=[0.1] * 4,
        top_k=3,
        answer="a",
        sources=[],
        generation_seconds=1.0,
    )

    assert client.upserted_points == []


def test_clear_deletes_all_points(monkeypatch):
    monkeypatch.setattr(settings, "SEMANTIC_CACHE_ENABLED", True)
    client = FakeQdrantClient()
    cache = make_cache(client)

    cache.clear()

    assert len(client.deleted_selectors) == 1
