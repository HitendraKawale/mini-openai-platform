import logging

from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingRegistry:
    def __init__(self) -> None:
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.model = None

    def load(self) -> None:
        logger.info(
            "loading_embedding_model",
            extra={"model_name": self.model_name},
        )

        self.model = SentenceTransformer(self.model_name)

        logger.info(
            "embedding_model_loaded",
            extra={"model_name": self.model_name},
        )

    def is_ready(self) -> bool:
        return self.model is not None

    def embed(self, texts: list[str], normalize: bool) -> dict:
        if not self.is_ready():
            raise RuntimeError("Embedding model is not loaded")

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
        )

        embedding_list = embeddings.tolist()
        dimensions = len(embedding_list[0]) if embedding_list else 0

        data = [
            {
                "index": idx,
                "embedding": vector,
            }
            for idx, vector in enumerate(embedding_list)
        ]

        return {
            "model_name": self.model_name,
            "data": data,
            "usage": {
                "input_count": len(texts),
                "embedding_dimensions": dimensions,
            },
        }


embedding_registry = EmbeddingRegistry()